"""ClockWidget - displays current time in real-time."""

from typing import Any
from core.widgets.base_widget import BaseWidget


class ClockWidget(BaseWidget):
    """Widget that displays the current time."""

    def __init__(
        self,
        widget_id: int = 0,
        name: str = "Clock",
        duration: int = 10,
        config: dict[str, Any] | None = None,
        priority: int = 1,
    ) -> None:
        super().__init__(widget_id, name, "clock", duration, config or {}, priority)

    def validate(self) -> bool:
        return True

    def get_format(self) -> str:
        return self.config.get("format", "HH:mm:ss")

    def get_font_size(self) -> int:
        return self.config.get("font_size", 72)