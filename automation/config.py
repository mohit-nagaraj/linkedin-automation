from dataclasses import dataclass
import os
from typing import Optional, List


@dataclass
class Settings:
    # LinkedIn
    linkedin_email: str
    linkedin_password: str
    search_keywords: List[str]
    locations: List[str]
    seniority_keywords: List[str]
    max_profiles: int = 25

    # Google Gemini
    google_api_key: str = ""

    # Google Sheets (Service Account JSON path or JSON string)
    gcp_service_account_json_path: Optional[str] = None
    gcp_service_account_json: Optional[str] = None
    gsheet_name: Optional[str] = None
    gsheet_worksheet: str = "Leads"
    storage_state_path: Optional[str] = ".playwright/storage_state.json"

    # OAuth user credentials fallback (if service account not provided)
    oauth_client_secrets_path: Optional[str] = None
    oauth_token_path: str = "token.json"

    # Runtime
    headless: bool = True
    slow_mo_ms: int = 0
    navigation_timeout_ms: int = 30000


def get_env_list(name: str) -> List[str]:
    raw = os.getenv(name, "").strip()
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


def load_settings() -> Settings:
    return Settings(
        linkedin_email=os.getenv("LINKEDIN_EMAIL", ""),
        linkedin_password=os.getenv("LINKEDIN_PASSWORD", ""),
        search_keywords=get_env_list("SEARCH_KEYWORDS"),
        locations=get_env_list("LOCATIONS"),
        seniority_keywords=get_env_list("SENIORITY_KEYWORDS") or [
            "founder",
            "co-founder",
            "cto",
            "vp engineering",
            "head of engineering",
            "lead software engineer",
        ],
        max_profiles=int(os.getenv("MAX_PROFILES", "25")),
        google_api_key=os.getenv("GOOGLE_API_KEY", ""),
        gcp_service_account_json_path=os.getenv("GCP_SERVICE_ACCOUNT_JSON_PATH"),
        gcp_service_account_json=os.getenv("GCP_SERVICE_ACCOUNT_JSON"),
        gsheet_name=os.getenv("GSHEET_NAME"),
        gsheet_worksheet=os.getenv("GSHEET_WORKSHEET", "Leads"),
        storage_state_path=os.getenv("STORAGE_STATE_PATH", ".playwright/storage_state.json"),
        oauth_client_secrets_path=os.getenv("OAUTH_CLIENT_SECRETS_PATH"),
        oauth_token_path=os.getenv("OAUTH_TOKEN_PATH", "token.json"),
        headless=os.getenv("HEADLESS", "true").lower() in {"1", "true", "yes"},
        slow_mo_ms=int(os.getenv("SLOW_MO_MS", "0")),
        navigation_timeout_ms=int(os.getenv("NAVIGATION_TIMEOUT_MS", "30000")),
    )


