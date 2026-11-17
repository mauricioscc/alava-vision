"""PlayerEngine - core playback loop for the player."""

import json
import time
from typing import Any
from PySide6.QtWidgets import QWidget, QStackedWidget, QVBoxLayout
from PySide6.QtCore import QTimer, QObject, Signal, Qt
from core.database import Database
from core.models.playlist import Playlist, PlaylistItem
from core.models.widget import Widget as WidgetModel
from core.models.schedule import ScheduleRule
from core.widgets.base_widget import BaseWidget
from core.widgets.site_widget import SiteWidget
from core.widgets.image_widget import ImageWidget
from core.widgets.text_widget import TextWidget
from core.widgets.clock_widget import ClockWidget
from core.widgets.pdf_widget import PDFWidget
from core.widgets.weather_widget import WeatherWidget
from core.services.schedule_engine import ScheduleEngine
from core.services.log_service import LogService
from player.renderers.base_renderer import BaseRenderer
from player.renderers.site_renderer import SiteRenderer
from player.renderers.image_renderer import ImageRenderer
from player.renderers.text_renderer import TextRenderer
from player.renderers.pdf_renderer import PDFRenderer
from player.renderers.clock_renderer import ClockRenderer
from player.renderers.weather_renderer import WeatherRenderer


class PlayerEngine(QObject):
    """Core playback engine that manages the playlist loop.
    
    Handles:
    - Loading playlists from database
    - Iterating through items
    - Managing display duration
    - Error recovery
    - Schedule rule evaluation
    """

    content_changed = Signal(str, str)  # widget_name, widget_type
    status_changed = Signal(str)  # status message

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._db = Database()
        self._log = LogService()
        self._schedule_engine = ScheduleEngine()

        # Playback state
        self._playlist_id: int | None = None
        self._items: list[dict[str, Any]] = []
        self._current_index: int = 0
        self._current_renderer: BaseRenderer | None = None
        self._is_playing: bool = False
        self._is_paused: bool = False
        self._error_count: int = 0
        self._max_errors: int = 3

        # UI
        self._container: QWidget | None = None
        self._stack: QStackedWidget | None = None

        # Timers
        self._duration_timer = QTimer(self)
        self._duration_timer.timeout.connect(self._on_duration_timeout)
        self._poll_timer = QTimer(self)
        self._poll_timer.timeout.connect(self._check_for_updates)
        self._poll_timer.start(5000)  # Check for updates every 5s

        # Renderer factory mapping
        self._renderer_factory: dict[str, type[BaseRenderer]] = {
            "site": SiteRenderer,
            "image": ImageRenderer,
            "text": TextRenderer,
            "pdf": PDFRenderer,
            "clock": ClockRenderer,
            "weather": WeatherRenderer,
        }

    def set_container(self, container: QWidget) -> None:
        """Set the container widget for rendering."""
        self._container = container
        self._stack = QStackedWidget(container)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._stack)

    def load_playlist(self, playlist_id: int) -> bool:
        """Load a playlist from the database."""
        try:
            with self._db.get_session() as session:
                playlist = session.query(Playlist).filter(
                    Playlist.id == playlist_id,
                    Playlist.active == True,
                ).first()

                if not playlist:
                    self._log.error(
                        f"Playlist {playlist_id} not found or inactive",
                        source="player",
                        category="playlist",
                    )
                    return False

                items = (
                    session.query(PlaylistItem, WidgetModel)
                    .join(WidgetModel, PlaylistItem.widget_id == WidgetModel.id)
                    .filter(
                        PlaylistItem.playlist_id == playlist_id,
                        PlaylistItem.active == True,
                        WidgetModel.active == True,
                    )
                    .order_by(PlaylistItem.order)
                    .all()
                )

                self._items = []
                for item, widget_model in items:
                    # Parse config
                    config = {}
                    if widget_model.config:
                        try:
                            config = json.loads(widget_model.config)
                        except json.JSONDecodeError:
                            config = {}

                    # Get effective duration
                    duration = item.duration or widget_model.duration

                    # Load schedule rules
                    rules = session.query(ScheduleRule).filter(
                        ScheduleRule.widget_id == widget_model.id,
                        ScheduleRule.active == True,
                    ).all()

                    self._items.append({
                        "item_id": item.id,
                        "widget_id": widget_model.id,
                        "name": widget_model.name,
                        "widget_type": widget_model.widget_type.value,
                        "duration": duration,
                        "config": config,
                        "priority": item.priority,
                        "browser_profile_id": widget_model.browser_profile_id,
                        "rules": rules,
                    })

                self._playlist_id = playlist_id
                self._log.info(
                    f"Loaded playlist '{playlist.name}' with {len(self._items)} items",
                    source="player",
                    category="playlist",
                )
                return True

        except Exception as e:
            self._log.error(
                f"Error loading playlist: {e}",
                source="player",
                category="playlist",
            )
            return False

    def play(self) -> None:
        """Start playback from the beginning."""
        if not self._items:
            self._log.warning("No items to play", source="player", category="playback")
            self.status_changed.emit("Nenhum item na playlist")
            return

        self._is_playing = True
        self._current_index = 0
        self._error_count = 0
        self._log.info(
            "Playback started",
            source="player",
            category="playback",
        )
        self.status_changed.emit("Reproduzindo")
        self._play_current()

    def stop(self) -> None:
        """Stop playback."""
        self._is_playing = False
        self._duration_timer.stop()
        if self._current_renderer:
            self._current_renderer.stop()
            self._current_renderer = None
        self._log.info("Playback stopped", source="player", category="playback")
        self.status_changed.emit("Parado")

    def pause(self) -> None:
        """Pause playback."""
        self._is_paused = True
        self._duration_timer.stop()
        self.status_changed.emit("Pausado")

    def resume(self) -> None:
        """Resume playback."""
        if self._is_paused:
            self._is_paused = False
            self._duration_timer.start()
            self.status_changed.emit("Reproduzindo")

    def _play_current(self) -> None:
        """Play the current item in the playlist."""
        if not self._is_playing or self._is_paused:
            return

        if self._current_index >= len(self._items):
            if self._items:
                self._current_index = 0  # Loop
            else:
                self.stop()
                return

        item = self._items[self._current_index]

        # Check schedule rules
        if not self._schedule_engine.evaluate_rules(item["rules"]):
            self._log.info(
                f"Widget '{item['name']}' skipped (schedule rules not met)",
                source="player",
                category="schedule",
            )
            self._next()
            return

        # Create widget instance
        widget = self._create_widget_from_item(item)
        if not widget:
            self._error_count += 1
            if self._error_count >= self._max_errors:
                self._log.error(
                    "Max errors reached, stopping playback",
                    source="player",
                    category="playback",
                )
                self.stop()
                return
            self._next()
            return

        # Create renderer
        renderer_class = self._renderer_factory.get(item["widget_type"])
        if not renderer_class:
            self._log.error(
                f"No renderer for widget type: {item['widget_type']}",
                source="player",
                category="renderer",
            )
            self._next()
            return

        # Stop current renderer
        if self._current_renderer:
            self._current_renderer.stop()

        # Create and start new renderer
        try:
            self._current_renderer = renderer_class(widget, self._container)
            ui = self._current_renderer.get_widget_ui()
            if self._stack:
                # Remove previous widgets
                while self._stack.count() > 0:
                    w = self._stack.widget(0)
                    self._stack.removeWidget(w)
                    w.deleteLater()
                self._stack.addWidget(ui)
                self._stack.setCurrentWidget(ui)

            self._current_renderer.start()
            self._error_count = 0

            # Emit signals
            self.content_changed.emit(item["name"], item["widget_type"])
            self._log.info(
                f"Playing: '{item['name']}' ({item['widget_type']}) for {item['duration']}s",
                source="player",
                category="playback",
                widget_id=item["widget_id"],
            )

            # Start duration timer
            self._duration_timer.start(item["duration"] * 1000)

        except Exception as e:
            self._log.error(
                f"Error playing widget '{item['name']}': {e}",
                source="player",
                category="playback",
                widget_id=item["widget_id"],
            )
            if self._current_renderer:
                self._current_renderer.handle_error(e)
            self._error_count += 1
            self._next()

    def _next(self) -> None:
        """Advance to the next item."""
        self._duration_timer.stop()
        self._current_index += 1
        self._play_current()

    def _on_duration_timeout(self) -> None:
        """Called when the current widget's duration expires."""
        self._next()

    def _create_widget_from_item(self, item: dict[str, Any]) -> BaseWidget | None:
        """Create a BaseWidget instance from playlist item data."""
        widget_type = item["widget_type"]
        try:
            if widget_type == "site":
                return SiteWidget(
                    widget_id=item["widget_id"],
                    name=item["name"],
                    duration=item["duration"],
                    config=item["config"],
                    priority=item["priority"],
                    browser_profile_id=item["browser_profile_id"],
                )
            elif widget_type == "image":
                return ImageWidget(
                    widget_id=item["widget_id"],
                    name=item["name"],
                    duration=item["duration"],
                    config=item["config"],
                    priority=item["priority"],
                )
            elif widget_type == "text":
                return TextWidget(
                    widget_id=item["widget_id"],
                    name=item["name"],
                    duration=item["duration"],
                    config=item["config"],
                    priority=item["priority"],
                )
            elif widget_type == "pdf":
                return PDFWidget(
                    widget_id=item["widget_id"],
                    name=item["name"],
                    duration=item["duration"],
                    config=item["config"],
                    priority=item["priority"],
                )
            elif widget_type == "clock":
                return ClockWidget(
                    widget_id=item["widget_id"],
                    name=item["name"],
                    duration=item["duration"],
                    config=item["config"],
                    priority=item["priority"],
                )
            elif widget_type == "weather":
                return WeatherWidget(
                    widget_id=item["widget_id"],
                    name=item["name"],
                    duration=item["duration"],
                    config=item["config"],
                    priority=item["priority"],
                )
            else:
                self._log.error(
                    f"Unknown widget type: {widget_type}",
                    source="player",
                    category="widget",
                )
                return None
        except Exception as e:
            self._log.error(
                f"Error creating widget '{item['name']}': {e}",
                source="player",
                category="widget",
            )
            return None

    def _check_for_updates(self) -> None:
        """Poll for playlist changes and reload if needed."""
        if not self._playlist_id:
            return
        try:
            with self._db.get_session() as session:
                playlist = session.query(Playlist).filter(
                    Playlist.id == self._playlist_id,
                ).first()
                if not playlist:
                    return
                current_count = len(self._items)
                items = (
                    session.query(PlaylistItem, WidgetModel)
                    .join(WidgetModel, PlaylistItem.widget_id == WidgetModel.id)
                    .filter(
                        PlaylistItem.playlist_id == self._playlist_id,
                        PlaylistItem.active == True,
                        WidgetModel.active == True,
                    )
                    .count()
                )
                if items != current_count:
                    self._log.info(
                        f"Playlist changed: {current_count} -> {items} items, reloading...",
                        source="player", category="playlist",
                    )
                    self._current_index = 0
                    if self._current_renderer:
                        self._current_renderer.stop()
                        self._current_renderer = None
                    self.load_playlist(self._playlist_id)
                    if self._is_playing:
                        self._play_current()
        except Exception as e:
            self._log.error(
                f"Error checking for updates: {e}",
                source="player", category="playlist",
            )

    def get_current_info(self) -> dict[str, Any]:
        """Get information about the currently playing content."""
        if not self._items or self._current_index >= len(self._items):
            return {"status": "stopped"}
        item = self._items[self._current_index]
        return {
            "status": "playing" if self._is_playing else "paused",
            "current_index": self._current_index,
            "total_items": len(self._items),
            "current_name": item["name"],
            "current_type": item["widget_type"],
            "duration": item["duration"],
        }