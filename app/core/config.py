import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./data/mortgage.db")
    model_path: str = os.getenv("MODEL_PATH", "./data/model_bundle.joblib")
    reports_dir: str = os.getenv("REPORTS_DIR", "./reports/generated")
    api_host: str = os.getenv("API_HOST", "127.0.0.1")
    api_port: int = int(os.getenv("API_PORT", "8000"))


settings = Settings()
