"""LogService - centralized logging for the application."""

import logging
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from dotenv import load_dotenv

load_dotenv()


class LogService:
    """Centralized logging service that writes to both file and database.
    
    Provides structured logging with levels, categories, and source tracking.
    """

    _instance: "LogService | None" = None
    _logger: logging.Logger | None = None

    def __new__(cls) -> "LogService":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if self._logger is not None:
            return
        self._setup_logger()

    def _setup_logger(self) -> None:
        """Configure the Python logger with file and console handlers."""
        log_dir = os.getenv("LOGS_DIR", "logs")
        Path(log_dir).mkdir(parents=True, exist_ok=True)

        log_level = getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO)

        self._logger = logging.getLogger("alavavision")
        self._logger.setLevel(log_level)

        # File handler
        log_file = Path(log_dir) / f"alavavision_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(log_level)
        file_formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        self._logger.addHandler(file_handler)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(message)s"
        )
        console_handler.setFormatter(console_formatter)
        self._logger.addHandler(console_handler)

    def _log(
        self,
        level: str,
        message: str,
        source: str = "system",
        category: str = "general",
        details: dict[str, Any] | None = None,
        widget_id: int | None = None,
        player_id: int | None = None,
    ) -> None:
        """Internal logging method."""
        log_level = getattr(logging, level.upper(), logging.INFO)
        
        # Build structured message
        parts = [f"[{source}]", f"[{category}]", message]
        if details:
            parts.append(json.dumps(details, ensure_ascii=False))
        
        full_message = " | ".join(parts)
        self._logger.log(log_level, full_message)

        # TODO: Also save to database Log model when DB session is available

    def info(
        self,
        message: str,
        source: str = "system",
        category: str = "general",
        details: dict[str, Any] | None = None,
        widget_id: int | None = None,
        player_id: int | None = None,
    ) -> None:
        """Log an info message."""
        self._log("INFO", message, source, category, details, widget_id, player_id)

    def warning(
        self,
        message: str,
        source: str = "system",
        category: str = "general",
        details: dict[str, Any] | None = None,
        widget_id: int | None = None,
        player_id: int | None = None,
    ) -> None:
        """Log a warning message."""
        self._log("WARNING", message, source, category, details, widget_id, player_id)

    def error(
        self,
        message: str,
        source: str = "system",
        category: str = "general",
        details: dict[str, Any] | None = None,
        widget_id: int | None = None,
        player_id: int | None = None,
    ) -> None:
        """Log an error message."""
        self._log("ERROR", message, source, category, details, widget_id, player_id)

    def debug(
        self,
        message: str,
        source: str = "system",
        category: str = "general",
        details: dict[str, Any] | None = None,
        widget_id: int | None = None,
        player_id: int | None = None,
    ) -> None:
        """Log a debug message."""
        self._log("DEBUG", message, source, category, details, widget_id, player_id)