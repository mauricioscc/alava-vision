"""TextWidget - for displaying text content."""

from typing import Any
from core.widgets.base_widget import BaseWidget


class TextWidget(BaseWidget):
    """Widget for displaying text content.
    
    Config parameters:
        text (str): The text content to display (required).
        font_size (int): Font size in pixels.
        font_color (str): Font color in hex (e.g., '#FFFFFF').
        background_color (str): Background color in hex.
        alignment (str): Text alignment: 'left', 'center', 'right'.
        font_family (str): Font family name.
        bold (bool): Bold text.
    """

    widget_type = "text"

    def __init__(
        self,
        widget_id: int,
        name: str,
        duration: int = 10,
        config: dict[str, Any] | None = None,
        priority: int = 1,
        active: bool = True,
        browser_profile_id: int | None = None,
    ) -> None:
        super().__init__(widget_id, name, duration, config, priority, active, browser_profile_id)

    def validate(self) -> bool:
        """Validate that text content is present."""
        return bool(self.config.get("text"))

    def get_renderer_class(self) -> str:
        return "text_renderer"