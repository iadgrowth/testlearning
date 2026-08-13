import csv
import re
from dataclasses import dataclass, field
from pathlib import Path

# Kixie's standard contact fields. Extend the alias lists as new CSV header
# spellings show up rather than requiring an exact match.
STANDARD_FIELD_ALIASES: dict[str, list[str]] = {
    'first_name': ['first name', 'firstname', 'first'],
    'last_name': ['last name', 'lastname', 'last'],
    'phone_number': ['phone', 'phone number', 'mobile', 'cell', 'direct phone'],
    'email': ['email', 'email address'],
    'company_name': ['company', 'company name', 'organization'],
    'job_title': ['title', 'job title'],
}

# Kixie has 6 account-level custom fields. In practice, 3 of them are the
# ones CSVs regularly need mapped -- but the header spelling on any given
# CSV varies (e.g. "LinkedIn" vs "LinkedIn URL"), so this is an alias table,
# not a fixed column list.
#
# TODO(discovery): confirm the exact custom-field names/IDs as they appear
# in Kixie's own Custom Fields settings and contact-import mapping UI, and
# fill in the remaining 3 slots if/when they're used.
CUSTOM_FIELD_ALIASES: dict[str, list[str]] = {
    'Location': ['location', 'city', 'region'],
    'Website': ['website', 'company website', 'url', 'domain'],
    'LinkedIn URL': ['linkedin url', 'linkedin', 'li url', 'linkedin profile'],
}

REQUIRED_STANDARD_FIELDS = {'phone_number'}

# raw CSV header -> ('standard' | 'custom', canonical field/custom-field name)
HeaderMap = dict[str, tuple[str, str]]


@dataclass
class Contact:
    phone_number: str
    first_name: str = ''
    last_name: str = ''
    email: str = ''
    company_name: str = ''
    job_title: str = ''
    custom_fields: dict[str, str] = field(default_factory=dict)


@dataclass
class LoadedContacts:
    contacts: list[Contact]
    header_map: HeaderMap


class ContactsCSVError(ValueError):
    """Raised when a contacts CSV can't be loaded or mapped cleanly."""


def _normalize(header: str) -> str:
    return re.sub(r'\s+', ' ', header.strip().lower())


def _build_header_map(
    headers: list[str],
    field_map_override: dict[str, str] | None = None,
) -> HeaderMap:
    """Map each raw CSV header to (kind, canonical_name).

    field_map_override lets a caller pin a specific header to a specific
    target for CSVs that use unrecognized wording, without editing code:
        {"Region": "custom:Location", "Direct Line": "standard:phone_number"}
    """
    override = field_map_override or {}
    header_map: HeaderMap = {}
    unmapped: list[str] = []

    for raw_header in headers:
        if raw_header in override:
            kind, _, name = override[raw_header].partition(':')
            header_map[raw_header] = (kind, name)
            continue

        normalized = _normalize(raw_header)
        matched = False

        for canonical, aliases in STANDARD_FIELD_ALIASES.items():
            if normalized in aliases or normalized == canonical.replace('_', ' '):
                header_map[raw_header] = ('standard', canonical)
                matched = True
                break
        if matched:
            continue

        for canonical, aliases in CUSTOM_FIELD_ALIASES.items():
            if normalized in aliases or normalized == canonical.lower():
                header_map[raw_header] = ('custom', canonical)
                matched = True
                break
        if matched:
            continue

        unmapped.append(raw_header)

    if unmapped:
        raise ContactsCSVError(
            "Unrecognized CSV column(s): " + ', '.join(repr(h) for h in unmapped) +
            ". Add an alias in contacts.py, or pass an explicit override via "
            "--field-map, e.g. --field-map 'Region=custom:Location'."
        )

    return header_map


def load_contacts(
    csv_path: Path,
    field_map_override: dict[str, str] | None = None,
) -> LoadedContacts:
    with open(csv_path, newline='', encoding='utf-8-sig') as fh:
        reader = csv.DictReader(fh)
        if not reader.fieldnames:
            raise ContactsCSVError(f"{csv_path} has no header row.")

        header_map = _build_header_map(list(reader.fieldnames), field_map_override)

        contacts: list[Contact] = []
        for row_num, row in enumerate(reader, start=2):  # header is row 1
            standard_values: dict[str, str] = {}
            custom_values: dict[str, str] = {}

            for raw_header, value in row.items():
                kind, canonical = header_map[raw_header]
                value = (value or '').strip()
                if kind == 'standard':
                    standard_values[canonical] = value
                else:
                    custom_values[canonical] = value

            missing_required = [
                f for f in REQUIRED_STANDARD_FIELDS
                if not standard_values.get(f)
            ]
            if missing_required:
                raise ContactsCSVError(
                    f"{csv_path}:{row_num} missing required field(s): "
                    f"{', '.join(missing_required)}"
                )

            contacts.append(Contact(
                phone_number=standard_values.get('phone_number', ''),
                first_name=standard_values.get('first_name', ''),
                last_name=standard_values.get('last_name', ''),
                email=standard_values.get('email', ''),
                company_name=standard_values.get('company_name', ''),
                job_title=standard_values.get('job_title', ''),
                custom_fields=custom_values,
            ))

    if not contacts:
        raise ContactsCSVError(f"{csv_path} has no data rows.")

    return LoadedContacts(contacts=contacts, header_map=header_map)


def parse_field_map_args(pairs: list[str]) -> dict[str, str]:
    """Parse repeated --field-map 'CSV Header=standard:field' / '=custom:Name' args."""
    result: dict[str, str] = {}
    for pair in pairs:
        header, sep, target = pair.partition('=')
        if not sep or ':' not in target:
            raise ContactsCSVError(
                f"Invalid --field-map value {pair!r}; expected "
                f"'CSV Header=standard:field_name' or 'CSV Header=custom:Field Name'."
            )
        result[header] = target
    return result
