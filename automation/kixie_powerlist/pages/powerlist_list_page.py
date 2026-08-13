import re

from playwright.sync_api import Page


class PowerlistListPage:
    """
    TODO(discovery): confirm the nav path/selectors to Kixie's PowerList
    list screen and its "create new" entry point via `playwright codegen`.
    """

    def __init__(self, page: Page):
        self.page = page

    def goto(self) -> None:
        self.page.get_by_role('link', name=re.compile('power ?list', re.I)).click()

    def click_create_new(self) -> None:
        self.page.get_by_role(
            'button', name=re.compile('new power ?list|create power ?list', re.I)
        ).click()
