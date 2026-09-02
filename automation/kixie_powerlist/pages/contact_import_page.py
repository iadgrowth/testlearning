import re
from pathlib import Path

from playwright.sync_api import Page

from ..contacts import HeaderMap

# Canonical standard field -> the actual text of the Kixie dropdown option
# to select. Only 'job_title' -> 'Title' is confirmed against a real
# mapping (see automation/.artifacts/discovery_codegen.py); the rest are
# unconfirmed guesses -- correct them once observed, or drop entries here
# if Kixie turns out to auto-map them without any explicit click.
STANDARD_FIELD_KIXIE_OPTION_LABELS: dict[str, str] = {
    'first_name': 'First Name',
    'last_name': 'Last Name',
    'phone_number': 'Phone',
    'email': 'Email',
    'company_name': 'Company',
    'job_title': 'Title',  # confirmed
}


class ContactImportPage:
    """
    Partially confirmed against discovery recording
    (automation/.artifacts/discovery_codegen.py):
      - "Contacts" tab, "Select File" button + hidden file input, and the
        per-column mapping table are real.
      - Custom-field columns map to generic "Custom1"/"Custom2"/"Custom3"
        dropdown options, not semantic names -- see contacts.py.
      - Two of the four recorded column mappings fell back to raw,
        auto-generated CSS class selectors (styled-components hashes) rather
        than role-based ones, which are unstable across deploys -- this
        implementation instead locates each row by its text content, which
        is what worked for the other two columns and doesn't depend on
        those classes.
      - The double "Preview" click at the end is unconfirmed: TODO(discovery)
        confirm whether the second click is the actual final submit, or
        there's a further confirmation step after it.
    """

    def __init__(self, page: Page):
        self.page = page

    def upload(self, csv_path: Path, header_map: HeaderMap) -> None:
        self.page.get_by_role('tab', name='Contacts').click()
        self.page.get_by_role('button', name='Select File').click()
        self.page.get_by_label('Select File').set_input_files(str(csv_path))
        self._map_columns(header_map)

    def _map_columns(self, header_map: HeaderMap) -> None:
        for raw_header, (kind, canonical) in header_map.items():
            target_label = (
                canonical if kind == 'custom'
                else STANDARD_FIELD_KIXIE_OPTION_LABELS.get(canonical, canonical)
            )
            self._map_one_column(raw_header, target_label)

    def _map_one_column(self, raw_header: str, target_label: str) -> None:
        row = self.page.locator('tr').filter(
            has_text=re.compile(rf'^{re.escape(raw_header)}\b')
        )
        row.get_by_role('combobox').click()
        self.page.get_by_role('option', name=target_label).click()

    def submit(self) -> None:
        """
        TODO(discovery): confirm this is actually the final create/import
        action -- recording showed "Preview" clicked twice in a row, which
        may mean the first opens a confirmation and the second confirms, or
        there may be further steps after this.
        """
        self.page.get_by_role('button', name='Preview').click()
        self.page.get_by_role('button', name='Preview').click()
