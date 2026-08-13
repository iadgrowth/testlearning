import os
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
AUTOMATION_ROOT = REPO_ROOT / 'automation'
AUTH_DIR = AUTOMATION_ROOT / '.auth'
ARTIFACTS_DIR = AUTOMATION_ROOT / '.artifacts'
STORAGE_STATE_PATH = AUTH_DIR / 'kixie_state.json'

load_dotenv(REPO_ROOT / '.env')

KIXIE_EMAIL = os.getenv('KIXIE_EMAIL')
KIXIE_PASSWORD = os.getenv('KIXIE_PASSWORD')
KIXIE_BASE_URL = os.getenv('KIXIE_BASE_URL', 'https://app.kixie.com')


def require_credentials() -> None:
    missing = [
        name for name, value in (
            ('KIXIE_EMAIL', KIXIE_EMAIL),
            ('KIXIE_PASSWORD', KIXIE_PASSWORD),
        )
        if not value
    ]
    if missing:
        raise RuntimeError(
            f"Missing required .env value(s): {', '.join(missing)}. "
            f"Add them to {REPO_ROOT / '.env'}."
        )
