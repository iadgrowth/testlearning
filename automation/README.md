# Kixie PowerList Setup Automation

Playwright library that drives Kixie's own web UI to create a PowerList,
import contacts from a CSV, configure dial settings, and assign it to a
campaign — so onboarding a new powerlist is one command instead of a manual
click-through. Background and design rationale: `docs/kixie-powerlist-automation-plan.md`.

Kept separate from the root `requirements.txt` on purpose: that file is what
Render installs for the deployed Django app, and it shouldn't need
Playwright + browser binaries on the web server.

## Status

Auth, CSV loading/validation, login, PowerList navigation/creation, dial
mode (3-at-a-time only), and contact import + column mapping are implemented
against a real discovery recording (`.artifacts/discovery_codegen.py`,
gitignored). There is no separate campaign/team-assignment step in Kixie's
UI — confirmed during discovery — so `--campaign` is metadata only, used in
the printed result summary (and eventually a matching `CustomerPowerlist`
row on the Django-app side), not a browser action.

Still open, each flagged with `TODO(discovery)`:
- `dial_settings_page.py`: only "3 at a time" has been recorded; "1 at a
  time" raises `NotImplementedError` until it's confirmed.
- `powerlist_create_page.py.get_created_powerlist_id`: confirmed the ID
  appears somewhere on the resulting page after submit, but the exact
  element hasn't been pinned down yet — raises `NotImplementedError`.
- `powerlist_list_page.py`: the sidebar icon click before "PowerLists" may
  not always be necessary (e.g. only when nav is collapsed).
- Custom-field slot mapping (`Custom1`/`Custom2`/`Custom3`) is a best-effort
  default, **not guaranteed** — see "Custom field mapping" below.

## Setup

```bash
cd automation
python3 -m venv .venv        # separate venv from the Django app's
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

Add to the repo's `.env` (not committed):

```
KIXIE_EMAIL=you@example.com
KIXIE_PASSWORD=...
KIXIE_BASE_URL=https://app.kixie.com   # adjust if different
```

## Discovery

First pass done — see "Status" above for what's confirmed vs. still open.
To fill in a remaining `TODO(discovery)` spot, repeat the same process:

1. Log into Kixie manually and run:
   ```bash
   cd automation && source .venv/bin/activate
   playwright codegen -o .artifacts/discovery_codegen.py https://app.kixie.com
   ```
   The `-o` flag auto-saves the recorded script as you click, so nothing is
   lost if the Inspector window just gets closed.
2. Walk through the specific gap (e.g. select "1 at a time", or just look at
   what appears on the page right after the final submit for the PowerList
   ID).
3. Read the saved script and update the relevant `pages/*.py` file.

`.artifacts/discovery_codegen.py` is gitignored — it can capture real
credentials if fields get filled in during recording. Strip any plaintext
password from it after reading, since `.env` already holds it securely and
there's no reason to leave a second copy on disk.

## Custom field mapping

Confirmed via discovery: Kixie's column-mapping UI targets generic slots
(`Custom1`, `Custom2`, `Custom3`, ...), not semantic names. CSVs typically
carry 3 extra columns that need to land in specific slots — commonly
`Location` → `Custom1`, `Website` → `Custom2`, `LinkedIn URL` → `Custom3` —
but **this isn't guaranteed**: the account owner confirmed those slots don't
always hold that same data, and header wording varies between CSVs too.
`kixie_powerlist/contacts.py` handles this with an alias table
(`CUSTOM_FIELD_ALIASES`) rather than a fixed column list:

- Known headers (and common variants) auto-map to their usual slot.
- Anything it doesn't recognize fails loudly before any browser interaction,
  rather than silently dropping or mis-mapping a column.
- **The CLI always prints the resolved header → slot mapping before
  submitting** (see `_print_field_mapping` in `cli.py`) — check it against
  `--dry-run` before ever running for real, since a wrong slot guess here
  would misroute data into the wrong dashboard field silently.
- One-off mismatches can be resolved without editing code via
  `--field-map 'CSV Header=custom:CustomN'` (repeatable), e.g.:
  ```bash
  --field-map 'Region=custom:Custom1'
  ```
- Recurring new header spellings should be added to `STANDARD_FIELD_ALIASES` /
  `CUSTOM_FIELD_ALIASES` in `contacts.py` instead of relying on `--field-map`
  every time.

## Usage

```bash
python -m kixie_powerlist.cli \
  --contacts sample_data/sample_contacts.csv \
  --name "Test List" \
  --dial-mode 3 \
  --campaign "Test Campaign" \
  --dry-run --headed
```

Flags:
- `--contacts` — path to the contacts CSV (required)
- `--name` — PowerList name (required)
- `--dial-mode {1,3}` — lines per agent (required)
- `--campaign` — campaign/team to assign (required)
- `--field-map` — explicit column override, repeatable (see above)
- `--dry-run` — run the full flow but stop short of the final create/submit
- `--headed` — show the browser window (default is headless)
- `--slow-mo <ms>` — slow down actions, for debugging selectors

A saved login session lives at `.auth/kixie_state.json` (gitignored) and is
reused across runs. Delete it to force a fresh login. On any failure, a
screenshot + page HTML are saved to `.artifacts/<timestamp>/` (gitignored).

## Sample data

`sample_data/sample_contacts.csv` has the standard fields plus `Location`,
`Website`, and `LinkedIn URL` — useful for testing `contacts.py`'s loading
and mapping logic without touching Kixie at all:

```bash
python -c "
from kixie_powerlist.contacts import load_contacts
from pathlib import Path
print(load_contacts(Path('sample_data/sample_contacts.csv')).contacts)
"
```
