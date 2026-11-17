"""Player application entry point - fullscreen kiosk player."""

import sys
import os
from pathlib import Path
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QScreen, QGuiApplication

from core.database import Database
from core.models import *  # noqa: F401, F403 - Register all models
from core.services.log_service import LogService
from core.services.config_service import ConfigService
from player.screen_manager import ScreenManager
from player.player_engine import PlayerEngine
from player.alert_manager import AlertManager


class PlayerWindow(QWidget):
    """The main player window - fullscreen, no decorations."""

    def __init__(self, monitor_index: int = 1) -> None:
        super().__init__()
        self._monitor_index = monitor_index
        self._log = LogService()
        self._screen_manager = ScreenManager()
        self._config = ConfigService()

        # Setup window
        self.setWindowTitle("AlavaVision Player")
        self.setStyleSheet("background-color: #000000;")
        self.setCursor(Qt.BlankCursor)  # Hide cursor

        # Remove window decorations
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )

        # Setup engine and alert manager
        self._engine = PlayerEngine(self)
        self._alert_manager = AlertManager(self)

        # Setup UI
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup the player UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Container for content
        self._content_container = QWidget()
        self._content_container.setStyleSheet("background-color: #000000;")
        layout.addWidget(self._content_container)

        # Set container for engine
        self._engine.set_container(self._content_container)

    def show_on_monitor(self) -> None:
        """Show the window on the target monitor."""
        screen = self._screen_manager.get_target_screen(self._monitor_index)
        if screen:
            self._screen_manager.move_to_screen(self, screen)
            self.showFullScreen()
            self._log.info(
                f"Player displayed on monitor {self._monitor_index}: {screen.name()}",
                source="player",
                category="screen",
            )
        else:
            # Fallback: show on primary screen
            self.showFullScreen()
            self._log.warning(
                f"Monitor {self._monitor_index} not found, using primary",
                source="player",
                category="screen",
            )

    def start_playback(self, playlist_id: int | None = None) -> None:
        """Start playing the specified playlist or the first active one."""
        if playlist_id:
            if self._engine.load_playlist(playlist_id):
                self._engine.play()
            return

        # Try to find the first active playlist
        try:
            db = Database()
            with db.get_session() as session:
                from core.models.playlist import Playlist
                playlist = session.query(Playlist).filter(
                    Playlist.active == True
                ).first()
                if playlist:
                    self._log.info(
                        f"Auto-loading playlist: '{playlist.name}'",
                        source="player",
                        category="playlist",
                    )
                    if self._engine.load_playlist(playlist.id):
                        self._engine.play()
                else:
                    self._log.warning(
                        "No active playlist found",
                        source="player",
                        category="playlist",
                    )
        except Exception as e:
            self._log.error(
                f"Error loading playlist: {e}",
                source="player",
                category="playlist",
            )

    def keyPressEvent(self, event) -> None:
        """Handle key presses for debugging/exit."""
        from PySide6.QtGui import QKeyEvent
        from PySide6.QtCore import Qt

        # ESC to exit (for development)
        if event.key() == Qt.Key_Escape:
            self._log.info("Player exiting (ESC pressed)", source="player", category="shutdown")
            QApplication.quit()

        # 'P' to pause/resume
        if event.key() == Qt.Key_P:
            if self._engine._is_paused:
                self._engine.resume()
            else:
                self._engine.pause()

        # 'R' to reload playlist
        if event.key() == Qt.Key_R:
            self._engine.stop()
            self.start_playback()

        super().keyPressEvent(event)

    def closeEvent(self, event) -> None:
        """Handle window close."""
        self._engine.stop()
        self._log.info("Player window closed", source="player", category="shutdown")
        super().closeEvent(event)


class PlayerApplication:
    """AlavaVision Player Application."""

    def __init__(self) -> None:
        self._app: QApplication | None = None
        self._window: PlayerWindow | None = None
        self._db = Database()
        self._log = LogService()
        self._config = ConfigService()

    def initialize(self) -> None:
        """Initialize the application."""
        self._db.create_all()
        self._log.info("Player application initialized", source="player", category="startup")

    def run(self) -> None:
        """Run the player application."""
        self._app = QApplication(sys.argv)
        self._app.setApplicationName("AlavaVision Player")
        self._app.setOrganizationName("AlavaVision")

        # Get monitor index from config
        monitor_index = self._config.get_int("PLAYER_MONITOR", 1)

        # Create and show player window
        self._window = PlayerWindow(monitor_index)
        self._window.show_on_monitor()

        # Start playback after a short delay (to ensure window is ready)
        QTimer.singleShot(1000, lambda: self._window.start_playback())

        self._log.info(
            f"Player started on monitor {monitor_index}",
            source="player",
            category="startup",
        )

        sys.exit(self._app.exec())


def main() -> None:
    """Entry point for the player application."""
    app = PlayerApplication()
    app.initialize()
    app.run()


if __name__ == "__main__":
    main()