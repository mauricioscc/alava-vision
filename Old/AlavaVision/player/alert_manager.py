"""AlertManager - manages overlay alerts on the player with audio support."""

import os
from typing import Any
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFrame
from PySide6.QtCore import QTimer, QPropertyAnimation, QEasingCurve, Qt, QPoint, Property, QObject
from PySide6.QtGui import QFont, QColor
from PySide6.QtMultimedia import QSoundEffect
from PySide6.QtCore import QUrl

from core.models.alert import Alert, AlertType, AlertPosition, AlertAnimation
from core.services.log_service import LogService


class AlertOverlay(QFrame):
    """A single alert overlay widget with animations."""

    def __init__(self, alert_data: dict[str, Any], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._alert = alert_data
        self._opacity = 1.0
        self._setup_ui()
        self._setup_animation()

    def _setup_ui(self) -> None:
        """Setup the alert UI based on type."""
        alert_type = self._alert.get("alert_type", "overlay_center")
        bg_color = self._alert.get("background_color", "#333333")
        text_color = self._alert.get("text_color", "#FFFFFF")
        message = self._alert.get("message", "")
        title = self._alert.get("title", "")

        # Base styling
        self.setStyleSheet(f"""
            AlertOverlay {{
                background-color: {bg_color};
                border-radius: 12px;
                border: 2px solid rgba(255,255,255,0.1);
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(8)

        if title:
            title_label = QLabel(title)
            title_label.setStyleSheet(f"""
                font-size: 24px;
                font-weight: bold;
                color: {text_color};
            """)
            title_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(title_label)

        msg_label = QLabel(message)
        msg_label.setStyleSheet(f"""
            font-size: 18px;
            color: {text_color};
        """)
        msg_label.setAlignment(Qt.AlignCenter)
        msg_label.setWordWrap(True)
        layout.addWidget(msg_label)

        # Position based on type
        self._apply_position(alert_type)

    def _apply_position(self, alert_type: str) -> None:
        """Apply positioning based on alert type."""
        position_map = {
            "overlay_center": (Qt.AlignCenter, 400, 200),
            "banner_top": (Qt.AlignTop | Qt.AlignHCenter, 800, 80),
            "banner_bottom": (Qt.AlignBottom | Qt.AlignHCenter, 800, 80),
            "toast": (Qt.AlignBottom | Qt.AlignRight, 300, 100),
        }
        if alert_type in position_map:
            alignment, width, height = position_map[alert_type]
            self.setFixedSize(width, height)

    def _setup_animation(self) -> None:
        """Setup entrance animation."""
        anim_type = self._alert.get("animation", "fade")
        duration = self._alert.get("duration", 10) * 1000  # Convert to ms

        if anim_type == "fade":
            self._fade_animation = QPropertyAnimation(self, b"windowOpacity")
            self._fade_animation.setDuration(500)
            self._fade_animation.setStartValue(0.0)
            self._fade_animation.setEndValue(1.0)
            self._fade_animation.setEasingCurve(QEasingCurve.OutCubic)
            self._fade_animation.start()

    def get_duration(self) -> int:
        """Get alert display duration in ms."""
        return self._alert.get("duration", 10) * 1000


class AlertManager(QObject):
    """Manages alert overlays on the player screen.
    
    Handles:
    - Displaying alerts over current content
    - Queue management with priority
    - Animations (fade, slide, zoom)
    - Audio playback for alerts
    - Auto-dismiss after duration
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._parent = parent
        self._log = LogService()
        self._current_alert: AlertOverlay | None = None
        self._alert_queue: list[dict[str, Any]] = []
        self._dismiss_timer = QTimer(self)
        self._dismiss_timer.timeout.connect(self._dismiss_current)
        self._sound_effects: dict[int, QSoundEffect] = {}

    def show_alert(self, alert_data: dict[str, Any]) -> None:
        """Show an alert overlay.
        
        Args:
            alert_data: Dictionary with alert configuration.
        """
        priority = alert_data.get("priority", 10)

        # If there's a current alert, check priority
        if self._current_alert:
            current_priority = self._current_alert.property("priority") or 0
            if priority > current_priority:
                self._dismiss_current()
            else:
                # Queue this alert
                self._alert_queue.append(alert_data)
                self._alert_queue.sort(key=lambda a: a.get("priority", 0), reverse=True)
                return

        # Create and show the alert
        overlay = AlertOverlay(alert_data, self._parent)
        overlay.setProperty("priority", priority)

        if self._parent:
            overlay.setParent(self._parent)
            overlay.show()
            overlay.raise_()

        self._current_alert = overlay

        # Play audio if configured
        audio_path = alert_data.get("audio_path")
        if audio_path and os.path.exists(audio_path):
            self._play_alert_audio(audio_path)

        self._log.info(
            f"Alert displayed: '{alert_data.get('title', alert_data.get('message', ''))[:50]}'",
            source="player",
            category="alert",
        )

        # Set dismiss timer
        duration = alert_data.get("duration", 10) * 1000
        self._dismiss_timer.start(duration)

    def _play_alert_audio(self, audio_path: str) -> None:
        """Play audio for an alert."""
        try:
            sound = QSoundEffect()
            sound.setSource(QUrl.fromLocalFile(audio_path))
            sound.setVolume(0.8)
            sound.play()
            self._sound_effects[id(sound)] = sound
            # Clean up when done
            sound.playingChanged.connect(lambda: self._cleanup_sound(sound))
            self._log.info(
                f"Alert audio playing: {audio_path}",
                source="player", category="alert",
            )
        except Exception as e:
            self._log.error(
                f"Error playing alert audio: {e}",
                source="player", category="alert",
            )

    def _cleanup_sound(self, sound: QSoundEffect) -> None:
        """Remove sound effect from cache when done."""
        key = id(sound)
        if key in self._sound_effects:
            del self._sound_effects[key]

    def _dismiss_current(self) -> None:
        """Dismiss the current alert."""
        if self._current_alert:
            self._current_alert.hide()
            self._current_alert.deleteLater()
            self._current_alert = None
            self._dismiss_timer.stop()

        # Show next in queue
        if self._alert_queue:
            next_alert = self._alert_queue.pop(0)
            self.show_alert(next_alert)

    def dismiss_all(self) -> None:
        """Dismiss all alerts."""
        self._dismiss_current()
        self._alert_queue.clear()
        self._sound_effects.clear()