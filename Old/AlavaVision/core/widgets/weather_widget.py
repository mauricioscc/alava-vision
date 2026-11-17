"""WeatherWidget - displays weather information."""

from typing import Any
from core.widgets.base_widget import BaseWidget


class WeatherWidget(BaseWidget):
    """Widget that displays weather forecast."""

    def __init__(
        self,
        widget_id: int = 0,
        name: str = "Weather",
        duration: int = 30,
        config: dict[str, Any] | None = None,
        priority: int = 1,
    ) -> None:
        super().__init__(widget_id, name, "weather", duration, config or {}, priority)

    def validate(self) -> bool:
        return True

    def get_city(self) -> str:
        return self.config.get("city", "São Paulo")

    def get_unit(self) -> str:
        return self.config.get("unit", "celsius")

    def get_update_interval(self) -> int:
        return self.config.get("update_interval", 30)