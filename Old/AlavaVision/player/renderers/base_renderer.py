"""BaseRenderer - abstract base class for all widget renderers."""

from abc import ABC, abstractmethod
from typing import Any
from PySide6.QtWidgets import QWidget
from core.widgets.base_widget import BaseWidget


class BaseRenderer(ABC):
    """Abstract base class for rendering widgets on screen.
    
    Each widget type has a corresponding renderer that knows
    how to display that type of content.
    """

    def __init__(self, widget: BaseWidget, parent: QWidget | None = None) -> None:
        self.widget = widget
        self.parent = parent
        self._widget_ui: QWidget | None = None

    @abstractmethod
    def create_ui(self) -> QWidget:
        """Create the UI widget for this renderer.
        
        Returns:
            A QWidget that displays the content.
        """
        ...

    @abstractmethod
    def start(self) -> None:
        """Start rendering (e.g., load URL, play video)."""
        ...

    @abstractmethod
    def stop(self) -> None:
        """Stop rendering and clean up resources."""
        ...

    def get_widget_ui(self) -> QWidget:
        """Get the UI widget, creating it if needed."""
        if self._widget_ui is None:
            self._widget_ui = self.create_ui()
        return self._widget_ui

    def handle_error(self, error: Exception) -> None:
        """Handle rendering errors gracefully."""
        from core.services.log_service import LogService
        log = LogService()
        log.error(
            f"Renderer error for widget '{self.widget.name}': {error}",
            source="player",
            category="renderer",
            widget_id=self.widget.id,
        )