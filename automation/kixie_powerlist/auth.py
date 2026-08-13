import contextlib
import logging

from playwright.sync_api import Browser, BrowserContext, Playwright

from . import config
from .pages.login_page import LoginPage

logger = logging.getLogger(__name__)


@contextlib.contextmanager
def authenticated_context(
    playwright: Playwright,
    *,
    headed: bool = False,
    slow_mo: int = 0,
    force_relogin: bool = False,
):
    """Yields a Playwright BrowserContext logged into Kixie.

    Reuses a saved storage_state (automation/.auth/kixie_state.json) across
    runs when it's still valid, so repeated runs skip a full login.
    """
    config.require_credentials()
    config.AUTH_DIR.mkdir(parents=True, exist_ok=True)

    browser = playwright.chromium.launch(headless=not headed, slow_mo=slow_mo)
    try:
        context = _load_or_create_context(browser, force_relogin=force_relogin)
        try:
            yield context
        finally:
            context.close()
    finally:
        browser.close()


def _load_or_create_context(browser: Browser, *, force_relogin: bool) -> BrowserContext:
    if not force_relogin and config.STORAGE_STATE_PATH.exists():
        context = browser.new_context(storage_state=str(config.STORAGE_STATE_PATH))
        if _session_is_valid(context):
            logger.info("Reusing saved Kixie session from %s", config.STORAGE_STATE_PATH)
            return context
        logger.info("Saved Kixie session is no longer valid, logging in again")
        context.close()

    context = browser.new_context()
    page = context.new_page()
    LoginPage(page).login(config.KIXIE_EMAIL, config.KIXIE_PASSWORD)
    page.close()
    context.storage_state(path=str(config.STORAGE_STATE_PATH))
    logger.info("Saved Kixie session to %s", config.STORAGE_STATE_PATH)
    return context


def _session_is_valid(context: BrowserContext) -> bool:
    """
    Best-effort check that a saved session is still authenticated.
    TODO(discovery): tighten once we know Kixie's post-login URL/selector
    (currently just checks we weren't bounced back to a login screen).
    """
    page = context.new_page()
    try:
        page.goto(config.KIXIE_BASE_URL, wait_until='domcontentloaded')
        return 'login' not in page.url.lower()
    finally:
        page.close()
