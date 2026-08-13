import re

from playwright.sync_api import Page

from .. import config


class LoginPage:
    """
    TODO(discovery): verify these locators against the real Kixie login
    screen with `playwright codegen <KIXIE_BASE_URL>` and adjust. Written
    against common patterns (labeled email/password inputs, a "Log in"
    submit button) as a starting point -- not yet confirmed against Kixie's
    actual DOM.
    """

    def __init__(self, page: Page):
        self.page = page

    def login(self, email: str, password: str) -> None:
        self.page.goto(config.KIXIE_BASE_URL, wait_until='domcontentloaded')
        self.page.get_by_label(re.compile('email', re.I)).fill(email)
        self.page.get_by_label(re.compile('password', re.I)).fill(password)
        self.page.get_by_role('button', name=re.compile('log ?in', re.I)).click()
        self.page.wait_for_load_state('networkidle')
