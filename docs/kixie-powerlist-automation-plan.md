# Kixie PowerList Setup Automation (Playwright, Python)

## Context

Setting up a new client campaign currently requires manually clicking through Kixie's
web UI to create a PowerList, import contacts, configure dial settings, and assign it
to a campaign — for every new customer. This repo already models that same setup on
the reporting side (`Customer` → `CustomerPowerlist` in [core/models.py](core/models.py))
and `TODO.md` already lists "Bulk powerlist import from CSV" as backlog work. The goal
here is a standalone Playwright library that drives Kixie's own UI to do this setup
automatically from a CSV of contacts, so onboarding a new powerlist becomes a single
command instead of a manual click-through.

Confirmed scope (from user):
- Automate: create PowerList → import contacts → configure dial settings (1-at-a-time
  vs 3-at-a-time) → assign to campaign/team.
- Contact data source: a local CSV file per run.
- Auth: plain username/password, no 2FA.
- Location/stack: new folder in this repo, Python (playwright-python), consistent with
  the existing Django codebase.

Key constraint: I have no visibility into Kixie's actual DOM/UI. Kixie's screens are
unknown until we open the real site, so this plan includes an explicit **discovery
step** using `playwright codegen` against the live account before real selectors can
be written. The plan below front-loads infrastructure that doesn't depend on Kixie's
DOM, then isolates the DOM-dependent work into its own phase.

## Structure

New top-level directory, sibling to `core/`, `config/`, `scripts/`:

```
automation/
  kixie_powerlist/
    __init__.py
    config.py              # loads KIXIE_EMAIL, KIXIE_PASSWORD, KIXIE_BASE_URL from .env
    models.py               # PowerlistSpec, DialMode enum (ONE/THREE), PowerlistResult
    auth.py                 # login(), reuses storage_state for session reuse
    contacts.py              # CSV loading + validation into contact records
    pages/
      login_page.py
      powerlist_list_page.py
      powerlist_create_page.py
      contact_import_page.py
      dial_settings_page.py
      campaign_assignment_page.py
    setup_powerlist.py       # orchestrator: chains page objects into one flow
    cli.py                   # `python -m automation.kixie_powerlist.cli ...`
  .auth/                     # gitignored: saved storage_state.json
  .artifacts/                # gitignored: failure screenshots + HTML dumps
  requirements.txt           # playwright, pytest-playwright, pandas (or csv-only, TBD)
  README.md                  # setup, env vars, how to run codegen for future selector work
```

Rationale for a dedicated `automation/requirements.txt` instead of adding to the root
`requirements.txt`: the root file is what Render installs for the deployed Django app
([README.md](README.md)) — it shouldn't need Playwright + browser binaries on the web
server.

## Design details

- **Config/env**: reuse the existing `python-dotenv` dependency and `.env` pattern
  already used by `config/settings.py`. Add `KIXIE_EMAIL`, `KIXIE_PASSWORD`,
  `KIXIE_BASE_URL` to `.env` (never committed — `.env` is already gitignored).
- **Session reuse**: `auth.py` logs in once and saves Playwright's `storage_state` to
  `automation/.auth/kixie_state.json` (gitignored), so repeated runs skip a full login.
- **Contacts**: `contacts.py` validates the input CSV against an expected schema
  (first_name, last_name, phone_number, email, company_name, job_title — mirroring the
  fields already tracked in `CallReport`) and fails fast with a clear error before any
  browser interaction, rather than failing mid-import inside Kixie's UI.
- **Dial mode**: modeled as `DialMode.ONE` / `DialMode.THREE` in `PowerlistSpec`, mapped
  to whatever the actual Kixie control turns out to be once discovered.
- **Locators**: prefer Playwright's role/label-based locators (`get_by_role`,
  `get_by_label`) over brittle CSS/XPath where Kixie's markup allows, since third-party
  UI changes over time will break selectors regardless — role-based locators are more
  resilient to non-structural markup changes.
- **Failure handling**: on any exception in a page-object step, capture a screenshot and
  page HTML into `automation/.artifacts/<timestamp>/` before re-raising, so a broken
  selector is debuggable without re-running.
- **CLI flags**: `--contacts <csv>`, `--name`, `--dial-mode {1,3}`, `--campaign`,
  `--dry-run` (walks the whole flow but stops short of the final "create" submit),
  `--headed` (visible browser for debugging), `--slowmo <ms>`.
- **Django integration (stretch, not in first pass)**: once a run succeeds and Kixie
  returns a powerlist ID, optionally write a matching `CustomerPowerlist` row via
  Django's ORM (same pattern as `scripts/create_test_user.py`), closing the loop between
  Kixie and this app's own tracking — flagged as a follow-up, not required for v1.

## Phased implementation

1. **Scaffolding** — create the `automation/` tree above, `.gitignore` entries for
   `automation/.auth/` and `automation/.artifacts/`, `automation/requirements.txt`
   (playwright, pytest-playwright), `playwright install chromium` instructions in
   `automation/README.md`.
2. **Auth** — implement `config.py`, `auth.py`, `pages/login_page.py`. Verify by
   actually logging into the real Kixie account and confirming the session lands on
   the dashboard.
3. **Discovery** — run `playwright codegen <kixie-url>` logged in manually, walk
   through creating one PowerList end-to-end by hand once. This produces a recorded
   script with real selectors that steps 4 onward translate into page objects. This
   step requires the user's live Kixie session — flagged as a joint/interactive step,
   not something plannable in advance.
4. **Page objects** — translate the discovery recording into
   `powerlist_create_page.py`, `contact_import_page.py`, `dial_settings_page.py`,
   `campaign_assignment_page.py`, each exposing a small explicit method per action
   (e.g. `create(name)`, `upload_csv(path)`, `set_dial_mode(mode)`, `assign_campaign(name)`).
5. **Orchestrator + CLI** — `setup_powerlist.py` chains the page objects per
   `PowerlistSpec`; `cli.py` wires up argparse and the flags above.
6. **End-to-end verification** — run with `--dry-run` first against a disposable test
   powerlist, then a real run, confirming the created PowerList in Kixie's UI matches
   the CSV contacts, dial mode, and campaign assignment.

## Verification

- Steps 1–2 are testable immediately: run the CLI's auth check against the real Kixie
  account and confirm a successful authenticated session (storage_state file written,
  dashboard reachable).
- Steps 3–6 require the user's live Kixie account to discover real selectors — cannot
  be verified from this repo alone. Plan is to build the skeleton + auth now, then do a
  short interactive session against the real site to capture selectors and fill in the
  page objects.
- Final acceptance: `python -m automation.kixie_powerlist.cli --contacts sample.csv
  --name "Test List" --dial-mode 3 --campaign "Test Campaign"` produces a real PowerList
  in Kixie matching the input, with `--dry-run` giving a safe way to test without side
  effects.
