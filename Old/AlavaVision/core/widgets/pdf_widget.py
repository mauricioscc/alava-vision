"""PDFWidget - displays PDF documents."""

from typing import Any
from core.widgets.base_widget import BaseWidget


class PDFWidget(BaseWidget):
    """Widget that displays a PDF document."""

    def __init__(
        self,
        widget_id: int = 0,
        name: str = "PDF",
        duration: int = 30,
        config: dict[str, Any] | None = None,
        priority: int = 1,
    ) -> None:
        super().__init__(widget_id, name, "pdf", duration, config or {}, priority)

    def validate(self) -> bool:
        return bool(self.config.get("file_path"))

    def get_file_path(self) -> str:
        return self.config.get("file_path", "")

    def get_page_duration(self) -> int:
        return self.config.get("page_duration", 10)