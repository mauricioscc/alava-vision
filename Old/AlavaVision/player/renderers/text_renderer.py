"""TextRenderer - displays text content using QLabel."""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtGui import QFont, QColor
from PySide6.QtCore import Qt
from core.widgets.base_widget import BaseWidget
from player.renderers.base_renderer import BaseRenderer


class TextRenderer(BaseRenderer):
    """Renderer for displaying text content with styling."""

    def __init__(self, widget: BaseWidget, parent: QWidget | None = None) -> None:
        super().__init__(widget, parent)
        self._label: QLabel | None = None

    def create_ui(self) -> QWidget:
        """Create the text display widget."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        self._label = QLabel()
        self._label.setAlignment(Qt.AlignCenter)
        self._label.setWordWrap(True)

        # Apply text styling from config
        text = self.widget.config.get("text", "")
        font_size = self.widget.config.get("font_size", 48)
        font_color = self.widget.config.get("font_color", "#FFFFFF")
        bg_color = self.widget.config.get("background_color", "#000000")
        alignment = self.widget.config.get("alignment", "center")
        font_family = self.widget.config.get("font_family", "Arial")
        bold = self.widget.config.get("bold", False)

        # Font
        font = QFont(font_family, font_size)
        font.setBold(bold)
        self._label.setFont(font)

        # Colors
        self._label.setStyleSheet(f"""
            QLabel {{
                color: {font_color};
                background-color: {bg_color};
                padding: 40px;
            }}
        """)

        # Alignment
        align_map = {
            "left": Qt.AlignLeft | Qt.AlignVCenter,
            "center": Qt.AlignCenter,
            "right": Qt.AlignRight | Qt.AlignVCenter,
        }
        self._label.setAlignment(align_map.get(alignment, Qt.AlignCenter))

        # Text
        self._label.setText(text)

        layout.addWidget(self._label)
        return container

    def start(self) -> None:
        """Text is already displayed in create_ui."""
        pass

    def stop(self) -> None:
        """Clean up."""
        if self._label:
            self._label.clear()
            self._label = None