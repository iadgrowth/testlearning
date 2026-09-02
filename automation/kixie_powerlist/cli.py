import argparse
import logging
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

from .contacts import ContactsCSVError, load_contacts, parse_field_map_args
from .models import DialMode, PowerlistSpec
from .setup_powerlist import create_powerlist


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create and configure a Kixie PowerList from a contacts CSV."
    )
    parser.add_argument('--contacts', required=True, type=Path, help='Path to contacts CSV')
    parser.add_argument('--name', required=True, help='PowerList name')
    parser.add_argument(
        '--dial-mode', required=True, choices=['1', '3'],
        help='Lines per agent: 1 or 3 at a time',
    )
    parser.add_argument('--campaign', required=True, help='Campaign/team to assign the PowerList to')
    parser.add_argument(
        '--field-map', action='append', default=[],
        metavar="'CSV Header=standard:field|custom:Name'",
        help="Explicit mapping override for a CSV column that doesn't match a "
             "known alias, e.g. --field-map 'Region=custom:Location'. Repeatable.",
    )
    parser.add_argument(
        '--dry-run', action='store_true',
        help='Run the full flow but stop short of the final create/submit',
    )
    parser.add_argument('--headed', action='store_true', help='Show the browser window')
    parser.add_argument('--slow-mo', type=int, default=0, help='Slow down actions by N ms, for debugging')
    return parser


def _print_field_mapping(header_map: dict[str, tuple[str, str]]) -> None:
    print("Column mapping (verify custom-field slots before a non-dry-run submit):")
    for raw_header, (kind, canonical) in header_map.items():
        print(f"  {raw_header!r} -> {kind}:{canonical}")


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')
    args = build_parser().parse_args(argv)

    try:
        field_map_override = parse_field_map_args(args.field_map)
        loaded = load_contacts(args.contacts, field_map_override=field_map_override)
    except ContactsCSVError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    _print_field_mapping(loaded.header_map)

    spec = PowerlistSpec(
        name=args.name,
        contacts=loaded.contacts,
        dial_mode=DialMode(args.dial_mode),
        campaign=args.campaign,
        dry_run=args.dry_run,
    )

    with sync_playwright() as playwright:
        result = create_powerlist(
            playwright, spec, loaded, args.contacts,
            headed=args.headed, slow_mo=args.slow_mo,
        )

    print(
        f"Created PowerList {result.name!r}: {result.contact_count} contacts, "
        f"dial_mode={result.dial_mode.value}, campaign={result.campaign!r}, "
        f"powerlist_id={result.powerlist_id}, dry_run={result.dry_run}"
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
