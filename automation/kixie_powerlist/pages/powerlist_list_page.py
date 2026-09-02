from playwright.sync_api import Page


class PowerlistListPage:
    """Confirmed against discovery recording (automation/.artifacts/discovery_codegen.py)."""

    def __init__(self, page: Page):
        self.page = page

    def goto(self) -> None:
        # TODO(discovery): this sidebar icon click preceded "PowerLists" in
        # the recording -- confirm whether it's always required (e.g. only
        # when the nav is collapsed) or can be dropped.
        self.page.get_by_role('link', name='Stockholm-icons / Design /').click()
        self.page.get_by_role('link', name='PowerLists').click()

    def click_create_new(self) -> None:
        self.page.get_by_role('button', name='New Team PowerList').click()
