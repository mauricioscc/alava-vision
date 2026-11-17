"""ConfigService - manages application configuration."""

import os
import json
from typing import Any
from dotenv import load_dotenv
from core.database import Database
from core.models.setting import Setting

load_dotenv()


class ConfigService:
    """Manages application configuration from .env and database settings.
    
    Provides a unified interface for reading/writing configuration values.
    Database settings override .env defaults.
    """

    _instance: "ConfigService | None" = None
    _cache: dict[str, str] = {}

    def __new__(cls) -> "ConfigService":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if self._cache:
            return
        self._load_env_defaults()

    def _load_env_defaults(self) -> None:
        """Load default values from .env file."""
        self._cache = {
            "DATABASE_PATH": os.getenv("DATABASE_PATH", "data/database.db"),
            "FILES_DIR": os.getenv("FILES_DIR", "data/files"),
            "AUDIO_DIR": os.getenv("AUDIO_DIR", "data/audio"),
            "PROFILES_DIR": os.getenv("PROFILES_DIR", "data/profiles"),
            "LOGS_DIR": os.getenv("LOGS_DIR", "logs"),
            "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
            "PLAYER_MONITOR": os.getenv("PLAYER_MONITOR", "1"),
            "PLAYER_FULLSCREEN": os.getenv("PLAYER_FULLSCREEN", "true"),
            "API_HOST": os.getenv("API_HOST", "localhost"),
            "API_PORT": os.getenv("API_PORT", "8000"),
        }
        # Load all remaining env vars dynamically
        for key, value in os.environ.items():
            if key not in self._cache:
                self._cache[key] = value

    def get(self, key: str, default: str = "") -> str:
        """Get a configuration value."""
        return self._cache.get(key, default)

    def get_int(self, key: str, default: int = 0) -> int:
        """Get a configuration value as integer."""
        try:
            return int(self._cache.get(key, str(default)))
        except (ValueError, TypeError):
            return default

    def get_bool(self, key: str, default: bool = False) -> bool:
        """Get a configuration value as boolean."""
        value = self._cache.get(key, str(default)).lower()
        return value in ("true", "1", "yes")

    def set(self, key: str, value: str) -> None:
        """Set a configuration value in the database."""
        self._cache[key] = value
        try:
            db = Database()
            with db.get_session() as session:
                setting = session.query(Setting).filter(Setting.key == key).first()
                if setting:
                    setting.value = value
                else:
                    setting = Setting(key=key, value=value)
                    session.add(setting)
                session.commit()
        except Exception:
            pass  # Database may not be ready yet

    def get_all(self) -> dict[str, str]:
        """Get all configuration values."""
        return dict(self._cache)