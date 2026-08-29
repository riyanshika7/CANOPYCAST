"""Runtime settings, all overridable by environment."""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")

DB_PATH = os.environ.get("CANOPYCAST_DB", str(BASE_DIR / "canopycast.db"))
CHROMA_DIR = os.environ.get("CANOPYCAST_CHROMA", str(BASE_DIR / "chroma_db"))
DOCUMENTS_DIR = str(BASE_DIR / "documents")

CHAT_MODEL = os.environ.get("CANOPYCAST_CHAT_MODEL", "gpt-5.6-luna")
EMBED_MODEL = os.environ.get("CANOPYCAST_EMBED_MODEL", "text-embedding-3-small")

DEFAULT_CITY = "Kolkata"


def has_openai_key() -> bool:
    return bool(os.environ.get("OPENAI_API_KEY"))
