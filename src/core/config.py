from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    app_name: str = "splitter"
    app_version: str = "0.1.0"

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            app_name=os.getenv("SPLITTER_APP_NAME", cls.app_name),
            app_version=os.getenv("SPLITTER_APP_VERSION", cls.app_version),
        )

    def provider_env(self, prefix: str) -> dict[str, str]:
        normalized = prefix.upper()
        return {
            "provider_name": os.getenv(f"SPLITTER_{normalized}_PROVIDER", "").strip(),
            "model_name": os.getenv(f"SPLITTER_{normalized}_MODEL", "").strip(),
            "base_url": os.getenv(f"SPLITTER_{normalized}_BASE_URL", "").strip(),
            "api_key": os.getenv(f"SPLITTER_{normalized}_API_KEY", "").strip(),
        }
