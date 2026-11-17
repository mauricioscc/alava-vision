"""ImageWidget - for displaying images."""

from typing import Any
from core.widgets.base_widget import BaseWidget


class ImageWidget(BaseWidget):
    """Widget for displaying images (PNG, JPG, WebP, GIF).
    
    Config parameters:
        file_path (str): Path to the image file (required).
        fit_mode (str): How to fit the image: 'contain', 'cover', 'fill', 'none'.
        transition (str): Transition effect: 'fade', 'none'.
    """

    widget_type = "image"

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
        """Validate that file_path is present."""
        return bool(self.config.get("file_path"))

    def get_renderer_class(self) -> str:
        return "image_renderer"