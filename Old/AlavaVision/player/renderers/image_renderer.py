"""ImageRenderer - displays images using QLabel with proper scaling."""

from pathlib import Path
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
from core.widgets.base_widget import BaseWidget
from core.services.log_service import LogService
from player.renderers.base_renderer import BaseRenderer


class ImageRenderer(BaseRenderer):
    """Renderer for displaying images (PNG, JPG, WebP, GIF)."""

    def __init__(self, widget: BaseWidget, parent: QWidget | None = None) -> None:
        super().__init__(widget, parent)
        self._label: QLabel | None = None
        self._container: QWidget | None = None
        self._log = LogService()

    def create_ui(self) -> QWidget:
        """Create the image display widget."""
        self._container = QWidget()
        layout = QVBoxLayout(self._container)
        layout.setContentsMargins(0, 0, 0, 0)

        self._label = QLabel()
        self._label.setAlignment(Qt.AlignCenter)
        self._label.setStyleSheet("background-color: #000000;")
        self._label.setScaledContents(True)

        # Don't set a fixed size - let it inherit from parent
        layout.addWidget(self._label)
        return self._container

    def start(self) -> None:
        """Load and display the image with proper scaling."""
        file_path = self.widget.config.get("file_path", "")
        if not file_path:
            self._log.error(
                f"No file path configured for image widget '{self.widget.name}'",
                source="player", category="image", widget_id=self.widget.id,
            )
            return

        path = Path(file_path)
        if not path.exists():
            self._log.error(
                f"Image file not found: {file_path}",
                source="player", category="image", widget_id=self.widget.id,
            )
            return

        pixmap = QPixmap(str(path))
        if pixmap.isNull():
            self._log.error(
                f"Failed to load image: {file_path}",
                source="player", category="image", widget_id=self.widget.id,
            )
            return

        if self._label:
            # Scale pixmap to fit the label while maintaining aspect ratio
            fit_mode = self.widget.config.get("fit_mode", "contain")
            if fit_mode == "fill":
                # Scale to fill exactly (may stretch)
                self._label.setScaledContents(True)
            elif fit_mode == "cover":
                # Crop to cover - use scaled with KeepAspectRatioByExpanding
                self._label.setScaledContents(False)
                if self._label.parent():
                    max_size = self._label.parent().size()
                    scaled = pixmap.scaled(max_size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                    self._label.setPixmap(scaled)
                    # Center the cropped image
                    self._label.setFixedSize(max_size)
            else:  # contain (default)
                # Scale to fit within bounds maintaining aspect ratio
                self._label.setScaledContents(False)
                if self._label.parent():
                    max_size = self._label.parent().size()
                    scaled = pixmap.scaled(max_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    self._label.setPixmap(scaled)

            self._log.info(
                f"Displaying image: {file_path} (mode: {fit_mode})",
                source="player", category="image", widget_id=self.widget.id,
            )

    def stop(self) -> None:
        """Clear the image."""
        if self._label:
            self._label.clear()
            self._label.setPixmap(QPixmap())  # Clear any pixmap
            self._label.setFixedSize(0, 0)  # Reset size
            self._label = None
        if self._container:
            self._container.setFixedSize(0, 0)
            self._container = None