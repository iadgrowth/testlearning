import re

from playwright.sync_api import Page

from ..models import DialMode


class DialSettingsPage:
    """
    TODO(discovery): confirm the control type (radio/dropdown/toggle) Kixie
    uses for lines-per-agent (1-at-a-time vs 3-at-a-time) and its exact
    labels via `playwright codegen`.
    """

    _LABELS = {
        DialMode.ONE_AT_A_TIME: re.compile(r'\b1\b.*at a time', re.I),
        DialMode.THREE_AT_A_TIME: re.compile(r'\b3\b.*at a time', re.I),
    }

    def __init__(self, page: Page):
        self.page = page

    def set_dial_mode(self, mode: DialMode) -> None:
        self.page.get_by_role('radio', name=self._LABELS[mode]).check()
