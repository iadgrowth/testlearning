import re

from playwright.sync_api import Page


class PowerlistCreatePage:
    """
    TODO(discovery): confirm the actual "create PowerList" form fields and
    submit flow via `playwright codegen`.
    """

    def __init__(self, page: Page):
        self.page = page

    def create(self, name: str) -> None:
        self.page.get_by_label(re.compile(r'^name$', re.I)).fill(name)
        self.page.get_by_role('button', name=re.compile('create|save|continue', re.I)).click()

    def get_created_powerlist_id(self) -> str:
        """
        TODO(discovery): once a PowerList is created, Kixie's URL or a page
        element should expose the new PowerList ID -- capture it here. Left
        unimplemented until that's confirmed against the real site (see
        docs/kixie-powerlist-automation-plan.md, Discovery phase).
        """
        raise NotImplementedError(
            "PowerlistCreatePage.get_created_powerlist_id is not yet wired up; "
            "needs a real Kixie session to discover where the ID appears."
        )
