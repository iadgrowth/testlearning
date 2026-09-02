import re

from playwright.sync_api import Page

from ..models import DialMode


class DialSettingsPage:
    """
    Partially confirmed against discovery recording
    (automation/.artifacts/discovery_codegen.py): selecting "3 at a time"
    was recorded as clicking a div whose text content is the concatenated
    "Dial at a Time3Dial at a Time" (a slider/segmented-control rendering
    both option labels), then a "Dial at a Time" heading.

    TODO(discovery): the "1 at a time" interaction hasn't been recorded --
    confirm whether it's the same control with a different value, or a
    different element entirely, before trusting this for DialMode.ONE_AT_A_TIME.
    """

    def __init__(self, page: Page):
        self.page = page

    def set_dial_mode(self, mode: DialMode) -> None:
        if mode is DialMode.THREE_AT_A_TIME:
            self.page.locator('div').filter(
                has_text=re.compile(r'^Dial at a Time3Dial at a Time$')
            ).first.click()
            self.page.get_by_role('heading', name='Dial at a Time').click()
        else:
            raise NotImplementedError(
                "DialMode.ONE_AT_A_TIME hasn't been confirmed against the real "
                "UI yet -- only the '3 at a time' path was recorded."
            )
