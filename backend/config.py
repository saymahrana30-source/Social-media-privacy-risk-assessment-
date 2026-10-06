"""Central configuration. Values come from environment variables (see .env.example).

Privacy by default: short retention, no accounts, no personal-data fields.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def _load_dotenv():
    """Tiny .env loader so beginners do not need an extra package."""
    env_file = BASE_DIR / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())


_load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-not-secret")
    DATABASE_PATH = os.environ.get("DATABASE_PATH", str(BASE_DIR / "instance" / "privacy_assessments.db"))
    RETENTION_DAYS = int(os.environ.get("RETENTION_DAYS", "30"))  # Retention limitation
    RATE_LIMIT_PER_MINUTE = int(os.environ.get("RATE_LIMIT_PER_MINUTE", "120"))
    RATE_LIMIT_POST_PER_MINUTE = int(os.environ.get("RATE_LIMIT_POST_PER_MINUTE", "20"))
    MAX_CONTENT_LENGTH = 32 * 1024  # 32 KB is plenty for questionnaire answers
    DATASET_PATH = str(BASE_DIR / "data" / "social_media_privacy_assessments.csv")
    FRONTEND_DIR = str(BASE_DIR / "frontend")
