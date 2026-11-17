"""ClockRenderer - displays current time in real-time."""

from datetime import datetime
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QFont
from player.renderers.base_renderer import BaseRenderer
from core.widgets.clock_widget import ClockWidget


class ClockRenderer(BaseRenderer):
    """Renderer for clock widget - shows current time with live updates."""

    def __init__(self, widget: ClockWidget, parent: QWidget | None = None) -> None:
        super().__init__(widget, parent)
        self._timer: QTimer | None = None
        self._label: QLabel | None = None

    def create_ui(self) -> QWidget:
        container = QWidget()
        container.setStyleSheet("background-color: #000000;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        self._label = QLabel()
        self._label.setAlignment(Qt.AlignCenter)
        font_size = self.widget.get_font_size()
        self._label.setStyleSheet(f"""
            color: #ffffff;
            font-size: {font_size}px;
            font-weight: bold;
            background-color: transparent;
        """)
        layout.addWidget(self._label)
        return container

    def start(self) -> None:
        self._update_time()
        self._timer = QTimer()
        self._timer.timeout.connect(self._update_time)
        self._timer.start(1000)  # Update every second

    def _update_time(self) -> None:
        if not self._label:
            return
        fmt = self.widget.get_format()
        now = datetime.now()
        try:
            self._label.setText(now.strftime(fmt))
        except ValueError:
            self._label.setText(now.strftime("%H:%M:%S"))

    def stop(self) -> None:
        if self._timer:
            self._timer.stop()
            self._timer = None