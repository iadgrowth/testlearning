from playwright.sync_api import Page

from .. import config


class LoginPage:
    """Confirmed against a real login via discovery recording
    (automation/.artifacts/discovery_codegen.py)."""

    def __init__(self, page: Page):
        self.page = page

    def login(self, email: str, password: str) -> None:
        self.page.goto(f"{config.KIXIE_BASE_URL}/login", wait_until='domcontentloaded')
        self.page.get_by_role('textbox', name='Email').click()
        self.page.get_by_role('textbox', name='Email').fill(email)
        self.page.get_by_role('textbox', name='Password').fill(password)
        self.page.get_by_role('button', name='Sign In').click()
        self.page.wait_for_load_state('networkidle')
