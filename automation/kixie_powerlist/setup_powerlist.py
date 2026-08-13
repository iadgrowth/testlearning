import logging
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import Page, Playwright

from . import auth, config
from .contacts import LoadedContacts
from .models import PowerlistResult, PowerlistSpec
from .pages.campaign_assignment_page import CampaignAssignmentPage
from .pages.contact_import_page import ContactImportPage
from .pages.dial_settings_page import DialSettingsPage
from .pages.powerlist_create_page import PowerlistCreatePage
from .pages.powerlist_list_page import PowerlistListPage

logger = logging.getLogger(__name__)


def create_powerlist(
    playwright: Playwright,
    spec: PowerlistSpec,
    loaded: LoadedContacts,
    csv_path: Path,
    *,
    headed: bool = False,
    slow_mo: int = 0,
) -> PowerlistResult:
    with auth.authenticated_context(playwright, headed=headed, slow_mo=slow_mo) as context:
        page = context.new_page()
        try:
            PowerlistListPage(page).goto()
            PowerlistListPage(page).click_create_new()

            PowerlistCreatePage(page).create(spec.name)
            DialSettingsPage(page).set_dial_mode(spec.dial_mode)
            ContactImportPage(page).upload(csv_path, loaded.header_map)
            CampaignAssignmentPage(page).assign(spec.campaign)

            if spec.dry_run:
                logger.info("Dry run: stopping before final submit for %r", spec.name)
                powerlist_id = None
            else:
                powerlist_id = PowerlistCreatePage(page).get_created_powerlist_id()
        except Exception:
            _capture_failure_artifacts(page)
            raise

    return PowerlistResult(
        name=spec.name,
        contact_count=len(loaded.contacts),
        dial_mode=spec.dial_mode,
        campaign=spec.campaign,
        dry_run=spec.dry_run,
        powerlist_id=powerlist_id,
    )


def _capture_failure_artifacts(page: Page) -> None:
    config.ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    run_dir = config.ARTIFACTS_DIR / stamp
    run_dir.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(run_dir / 'failure.png'), full_page=True)
    (run_dir / 'page.html').write_text(page.content(), encoding='utf-8')
    logger.error("Saved failure artifacts to %s", run_dir)
