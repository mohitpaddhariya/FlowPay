from pydantic_settings import BaseSettings
from pydantic import field_validator
from functools import lru_cache
import re


class Settings(BaseSettings):
    """Application settings loaded from .env file."""

    google_sheets_credentials_file: str = "credentials.json"
    google_sheet_id: str

    @field_validator("google_sheet_id", mode="before")
    @classmethod
    def extract_sheet_id_from_url(cls, v: str) -> str:
        """Accept both a raw Sheet ID and a full Google Sheets URL.
        
        e.g. https://docs.google.com/spreadsheets/d/1Ahb2eB.../edit?gid=0#gid=0
        extracts '1Ahb2eB...' automatically.
        """
        if not v:
            return v
        match = re.search(r"/spreadsheets/d/([a-zA-Z0-9_-]+)", v)
        if match:
            return match.group(1)
        return v  # Already a raw ID

    # Razorpay
    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""
    razorpay_webhook_secret: str = ""

    # Email / SMTP
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    from_email: str = ""
    business_name: str = "FlowPay"
    
    # AI Context
    gemini_api_key: str | None = None

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
