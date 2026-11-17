"""Admin application entry point."""

import sys
import os
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from core.database import Database
from core.models import *  # noqa: F401, F403 - Register all models
from core.services.log_service import LogService
from admin.views.main_window import MainWindow


class AdminApplication:
    """AlavaVision Admin Application."""

    def __init__(self) -> None:
        self._app: QApplication | None = None
        self._window: MainWindow | None = None
        self._db = Database()
        self._log = LogService()

    def initialize(self) -> None:
        """Initialize the application."""
        # Create database tables
        self._db.create_all()
        self._log.info("Admin application initialized", source="admin", category="startup")

    def run(self) -> None:
        """Run the admin application."""
        self._app = QApplication(sys.argv)
        self._app.setApplicationName("AlavaVision")
        self._app.setOrganizationName("AlavaVision")

        # Set dark theme palette
        self._app.setStyle("Fusion")
        self._app.setStyleSheet("""
            QToolTip {
                background-color: #16213e;
                color: #ffffff;
                border: 1px solid #2a2a3e;
                padding: 4px;
            }
        """)

        self._window = MainWindow()
        self._window.show()

        self._log.info("Admin application started", source="admin", category="startup")

        sys.exit(self._app.exec())


def main() -> None:
    """Entry point for the admin application."""
    app = AdminApplication()
    app.initialize()
    app.run()


if __name__ == "__main__":
    main()