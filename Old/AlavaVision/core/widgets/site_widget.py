"""SiteWidget - for displaying web pages."""

from typing import Any
from core.widgets.base_widget import BaseWidget


class SiteWidget(BaseWidget):
    """Widget for displaying web pages using QWebEngineView.
    
    Config parameters:
        url (str): The URL to display (required).
        auto_refresh (int): Auto-refresh interval in seconds (0 = disabled).
        zoom_factor (float): Zoom level (1.0 = 100%).
        scroll_horizontal (int): Horizontal scroll position.
        scroll_vertical (int): Vertical scroll position.
        hide_scrollbars (bool): Hide scrollbars.
    """

    widget_type = "site"

    def __init__(
        self,
        widget_id: int,
        name: str,
        duration: int = 30,
        config: dict[str, Any] | None = None,
        priority: int = 1,
        active: bool = True,
        browser_profile_id: int | None = None,
    ) -> None:
        super().__init__(widget_id, name, duration, config, priority, active, browser_profile_id)

    def validate(self) -> bool:
        """Validate that URL is present and valid."""
        url = self.config.get("url", "")
        if not url:
            return False
        return url.startswith(("http://", "https://", "file://"))

    def get_renderer_class(self) -> str:
        return "site_renderer"