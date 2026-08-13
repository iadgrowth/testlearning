# Kixie PowerList Setup Automation

Playwright library that drives Kixie's own web UI to create a PowerList,
import contacts from a CSV, configure dial settings, and assign it to a
campaign — so onboarding a new powerlist is one command instead of a manual
click-through. Background and design rationale: `docs/kixie-powerlist-automation-plan.md`.

Kept separate from the root `requirements.txt` on purpose: that file is what
Render installs for the deployed Django app, and it shouldn't need
Playwright + browser binaries on the web server.

## Status

Auth and CSV loading/validation are implemented and tested. The page objects
that actually drive Kixie's PowerList creation/import/dial-settings/campaign
screens (`kixie_powerlist/pages/`) are **stubs written against guessed
selectors** — Kixie's real DOM hasn't been inspected yet. Every stub has a
`TODO(discovery)` docstring flagging what needs confirming. See "Discovery"
below before expecting an end-to-end run to work.

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

## Discovery (required before first real run)

The page objects were written against common UI patterns, not Kixie's actual
markup. Before they'll work:

1. Log into Kixie manually and run:
   ```bash
   playwright codegen https://app.kixie.com
   ```
2. Walk through creating one PowerList by hand: name it, import a small CSV,
   set the dial mode (1-at-a-time vs 3-at-a-time), assign a campaign.
3. Use the recorded script's selectors to fill in the `TODO(discovery)` spots
   in `kixie_powerlist/pages/*.py` — particularly:
   - `powerlist_create_page.py`: real "create" form + `get_created_powerlist_id`
     (currently raises `NotImplementedError`)
   - `contact_import_page.py`: the real column-mapping UI for custom fields
   - `dial_settings_page.py`: the actual 1-vs-3 control and labels
   - `campaign_assignment_page.py`: whether assignment is same-screen or separate

## Custom field mapping

Kixie has 6 account-level custom fields. CSVs typically carry 3 extra columns
that need to land in specific ones — commonly `Location`, `Website`, and
`LinkedIn URL` — but the exact header wording varies between CSVs.
`kixie_powerlist/contacts.py` handles this with an alias table
(`CUSTOM_FIELD_ALIASES`) rather than a fixed column list:

- Known headers (and common variants) auto-map.
- Anything it doesn't recognize fails loudly before any browser interaction,
  rather than silently dropping or mis-mapping a column.
- One-off mismatches can be resolved without editing code via
  `--field-map 'CSV Header=custom:Field Name'` (repeatable), e.g.:
  ```bash
  --field-map 'Region=custom:Location'
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
