from playwright.sync_api import Page

from .. import config


class PowerlistCreatePage:
    """Confirmed against discovery recording (automation/.artifacts/discovery_codegen.py).
    "Create" isn't a separate submit here -- naming, dial mode, and contact
    import all happen on one continuous PowerList screen; the actual submit
    is the "Preview" button in the Contacts tab (see contact_import_page.py).

    After submit, the new PowerList's ID isn't shown on a confirmation
    screen -- it shows up back in the /manage/powerlists list table, as the
    first column in the row matching the PowerList's name.
    """

    def __init__(self, page: Page):
        self.page = page

    def set_name(self, name: str) -> None:
        self.page.get_by_role('textbox', name='PowerList Name').click()
        self.page.get_by_role('textbox', name='PowerList Name').fill(name)

    def get_created_powerlist_id(self, name: str) -> str:
        # NOTE: matches by name only -- if multiple PowerLists share the same
        # name, .first() isn't guaranteed to be the one just created. Use a
        # unique --name per run (e.g. include a date/timestamp) to avoid this.
        self.page.goto(f"{config.KIXIE_BASE_URL}/manage/powerlists", wait_until='domcontentloaded')
        row = self.page.locator('tr').filter(
            has=self.page.get_by_role('link', name=name, exact=True)
        ).first
        return row.locator('td').first.inner_text().strip()
