import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _default_database_url() -> str:
    configured = os.getenv("DATABASE_URL")
    if configured:
        return configured
    if os.getenv("SPACE_ID"):
        return "sqlite:////tmp/mortgage.db"
    return "sqlite:///./data/mortgage.db"


def _default_reports_dir() -> str:
    configured = os.getenv("REPORTS_DIR")
    if configured:
        return configured
    if os.getenv("SPACE_ID"):
        return "/tmp/reports/generated"
    return "./reports/generated"


def _default_model_path() -> str:
    configured = os.getenv("MODEL_PATH")
    if configured:
        return configured
    if os.getenv("SPACE_ID"):
        return "/tmp/model_bundle.joblib"
    return "./data/model_bundle.joblib"


@dataclass(frozen=True)
class Settings:
    database_url: str = _default_database_url()
    model_path: str = _default_model_path()
    reports_dir: str = _default_reports_dir()
    api_host: str = os.getenv("API_HOST", "127.0.0.1")
    api_port: int = int(os.getenv("API_PORT", "8000"))


settings = Settings()
