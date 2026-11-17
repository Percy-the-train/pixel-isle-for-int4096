import os
import sys
from pathlib import Path

APP_NAME = "NewsCrawler Buddy"
VERSION = "1.0.0"

FROZEN = getattr(sys, "frozen", False)
ROOT = Path(sys.executable).parent if FROZEN else Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get("NCB_DATA_DIR", ROOT / "data"))
EXPORT_DIR = DATA_DIR / "exports"
DB_PATH = DATA_DIR / "newscrawler.db"
KEY_FILE = DATA_DIR / "secret.key"
STATIC_DIR = Path(__file__).resolve().parent / "static"

# Honest, identifiable User-Agent by default.
USER_AGENT = "NewsCrawlerBuddy/1.0 (research dataset collector; polite crawler)"


def ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)