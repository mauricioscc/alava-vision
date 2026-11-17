"""ScreenManager - manages multiple monitors for the player."""

from typing import Any
from PySide6.QtGui import QScreen, QGuiApplication
from PySide6.QtWidgets import QWidget
from core.services.log_service import LogService


class ScreenManager:
    """Manages screen/monitor selection for the player.
    
    Handles detection of multiple monitors and allows selecting
    which one to display the player on.
    """

    def __init__(self) -> None:
        self._log = LogService()

    def get_screens(self) -> list[dict[str, Any]]:
        """Get information about all available screens."""
        screens = QGuiApplication.screens()
        result = []
        for i, screen in enumerate(screens):
            geometry = screen.geometry()
            result.append({
                "index": i,
                "name": screen.name(),
                "width": geometry.width(),
                "height": geometry.height(),
                "is_primary": screen == QGuiApplication.primaryScreen(),
                "geometry": geometry,
            })
        return result

    def get_target_screen(self, monitor_index: int = 1) -> QScreen | None:
        """Get the target screen for the player.
        
        Args:
            monitor_index: Index of the monitor to use (0 = primary, 1 = secondary, etc.)
            
        Returns:
            QScreen to display on, or None if not available.
        """
        screens = QGuiApplication.screens()
        if not screens:
            self._log.error("No screens detected", source="player", category="screen")
            return None

        if monitor_index < len(screens):
            return screens[monitor_index]

        # Fallback to last available screen
        self._log.warning(
            f"Monitor {monitor_index} not found, using last available",
            source="player",
            category="screen",
        )
        return screens[-1]

    def get_primary_screen(self) -> QScreen | None:
        """Get the primary screen."""
        return QGuiApplication.primaryScreen()

    def move_to_screen(self, widget: QWidget, screen: QScreen) -> None:
        """Move a widget to the specified screen and maximize it."""
        if not screen:
            return
        geometry = screen.geometry()
        widget.setGeometry(geometry)
        widget.move(geometry.topLeft())
        self._log.info(
            f"Moved player to screen: {screen.name()} ({geometry.width()}x{geometry.height()})",
            source="player",
            category="screen",
        )