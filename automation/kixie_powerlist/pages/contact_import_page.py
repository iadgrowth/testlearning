import re
from pathlib import Path

from playwright.sync_api import Page

from ..contacts import HeaderMap


class ContactImportPage:
    """
    TODO(discovery): Kixie's contact import is expected to be a two-step
    flow: upload a CSV, then map each detected column to a Kixie field
    (standard or one of the 6 account-level custom fields). The upload step
    below is a reasonable default (a plain file input); the per-column
    mapping step is a placeholder until the real mapping UI (dropdown per
    column vs. a single mapping table, exact labels) is confirmed via
    `playwright codegen`.
    """

    def __init__(self, page: Page):
        self.page = page

    def upload(self, csv_path: Path, header_map: HeaderMap) -> None:
        self.page.set_input_files('input[type="file"]', str(csv_path))
        self._map_columns(header_map)

    def _map_columns(self, header_map: HeaderMap) -> None:
        for raw_header, (kind, canonical) in header_map.items():
            target_label = canonical if kind == 'custom' else canonical.replace('_', ' ')
            self._map_one_column(raw_header, target_label)

    def _map_one_column(self, raw_header: str, target_label: str) -> None:
        """
        TODO(discovery): replace with the real per-column mapping control.
        Placeholder assumes a labeled dropdown next to each detected column
        header, keyed by the raw CSV header text.
        """
        dropdown = self.page.get_by_role(
            'combobox', name=re.compile(re.escape(raw_header), re.I)
        )
        dropdown.select_option(label=target_label)
