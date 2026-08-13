from dataclasses import dataclass
from enum import Enum

from .contacts import Contact


class DialMode(str, Enum):
    ONE_AT_A_TIME = '1'
    THREE_AT_A_TIME = '3'


@dataclass
class PowerlistSpec:
    name: str
    contacts: list[Contact]
    dial_mode: DialMode
    campaign: str
    dry_run: bool = False


@dataclass
class PowerlistResult:
    name: str
    contact_count: int
    dial_mode: DialMode
    campaign: str
    dry_run: bool
    powerlist_id: str | None = None
