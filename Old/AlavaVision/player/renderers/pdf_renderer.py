"""PDFRenderer - renders PDF documents using PyMuPDF."""

import pymupdf as fitz  # PyMuPDF (backward compat)
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QPixmap, QImage
from player.renderers.base_renderer import BaseRenderer
from core.widgets.pdf_widget import PDFWidget
from core.services.log_service import LogService


class PDFRenderer(BaseRenderer):
    """Renderer for PDF documents."""

    def __init__(self, widget: PDFWidget, parent: QWidget | None = None) -> None:
        super().__init__(widget, parent)
        self._log = LogService()
        self._doc: fitz.Document | None = None
        self._current_page: int = 0
        self._total_pages: int = 0
        self._page_timer: QTimer | None = None
        self._image_label: QLabel | None = None

    def create_ui(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        self._image_label = QLabel()
        self._image_label.setAlignment(Qt.AlignCenter)
        self._image_label.setStyleSheet("background-color: #000000;")
        layout.addWidget(self._image_label)
        return container

    def start(self) -> None:
        file_path = self.widget.get_file_path()
        if not file_path:
            self._log.error("PDF file path is empty", source="player", category="renderer")
            return

        try:
            self._doc = fitz.open(file_path)
            self._total_pages = len(self._doc)
            self._current_page = 0
            self._render_page()

            # Auto-advance pages
            page_duration = self.widget.get_page_duration() * 1000
            if self._total_pages > 1 and page_duration > 0:
                self._page_timer = QTimer()
                self._page_timer.timeout.connect(self._next_page)
                self._page_timer.start(page_duration)

            self._log.info(
                f"PDF loaded: {file_path} ({self._total_pages} pages)",
                source="player", category="renderer",
            )
        except Exception as e:
            self._log.error(
                f"Error loading PDF: {e}",
                source="player", category="renderer",
            )

    def _render_page(self) -> None:
        if not self._doc or not self._image_label:
            return
        try:
            page = self._doc[self._current_page]
            # Render at 2x for quality
            mat = fitz.Matrix(2.0, 2.0)
            pix = page.get_pixmap(matrix=mat)
            img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(img)

            # Scale to fit label while maintaining aspect ratio
            if self._image_label.parent():
                max_size = self._image_label.parent().size()
                scaled = pixmap.scaled(max_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self._image_label.setPixmap(scaled)
        except Exception as e:
            self._log.error(f"Error rendering PDF page: {e}", source="player", category="renderer")

    def _next_page(self) -> None:
        if not self._doc:
            return
        self._current_page += 1
        if self._current_page >= self._total_pages:
            self._current_page = 0
        self._render_page()

    def stop(self) -> None:
        if self._page_timer:
            self._page_timer.stop()
            self._page_timer = None
        if self._doc:
            self._doc.close()
            self._doc = None