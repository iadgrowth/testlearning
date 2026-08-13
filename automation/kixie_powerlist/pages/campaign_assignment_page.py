import re

from playwright.sync_api import Page


class CampaignAssignmentPage:
    """
    TODO(discovery): confirm whether campaign/team assignment is a dropdown
    on the same create screen or a separate step, via `playwright codegen`.
    """

    def __init__(self, page: Page):
        self.page = page

    def assign(self, campaign_name: str) -> None:
        self.page.get_by_label(re.compile('campaign|team', re.I)).select_option(label=campaign_name)
