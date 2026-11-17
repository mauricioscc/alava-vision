"""WidgetController - CRUD operations for widgets."""

import json
from typing import Any
from sqlalchemy.orm import Session
from core.database import Database
from core.models.widget import Widget, WidgetType
from core.models.schedule import ScheduleRule
from core.schemas.widget_schema import WidgetCreate, WidgetUpdate
from core.services.log_service import LogService


class WidgetController:
    """Controller for managing widgets."""

    def __init__(self) -> None:
        self._db = Database()
        self._log = LogService()

    def get_all(self) -> list[Widget]:
        """Get all widgets."""
        with self._db.get_session() as session:
            return session.query(Widget).order_by(Widget.name).all()

    def get_by_id(self, widget_id: int) -> Widget | None:
        """Get a widget by ID."""
        with self._db.get_session() as session:
            return session.query(Widget).filter(Widget.id == widget_id).first()

    def create(self, data: WidgetCreate) -> Widget:
        """Create a new widget."""
        with self._db.get_session() as session:
            widget = Widget(
                name=data.name,
                widget_type=WidgetType(data.widget_type),
                duration=data.duration,
                config=json.dumps(data.config, ensure_ascii=False),
                priority=data.priority,
                active=data.active,
                browser_profile_id=data.browser_profile_id,
            )
            session.add(widget)
            session.commit()
            session.refresh(widget)
            self._log.info(
                f"Widget created: '{widget.name}' ({widget.widget_type})",
                source="admin",
                category="widget",
            )
            return widget

    def update(self, widget_id: int, data: WidgetUpdate) -> Widget | None:
        """Update an existing widget."""
        with self._db.get_session() as session:
            widget = session.query(Widget).filter(Widget.id == widget_id).first()
            if not widget:
                return None

            if data.name is not None:
                widget.name = data.name
            if data.duration is not None:
                widget.duration = data.duration
            if data.config is not None:
                widget.config = json.dumps(data.config, ensure_ascii=False)
            if data.priority is not None:
                widget.priority = data.priority
            if data.active is not None:
                widget.active = data.active
            if data.browser_profile_id is not None:
                widget.browser_profile_id = data.browser_profile_id

            session.commit()
            session.refresh(widget)
            self._log.info(
                f"Widget updated: '{widget.name}'",
                source="admin",
                category="widget",
            )
            return widget

    def delete(self, widget_id: int) -> bool:
        """Delete a widget."""
        with self._db.get_session() as session:
            widget = session.query(Widget).filter(Widget.id == widget_id).first()
            if not widget:
                return False
            name = widget.name
            session.delete(widget)
            session.commit()
            self._log.info(
                f"Widget deleted: '{name}'",
                source="admin",
                category="widget",
            )
            return True

    def toggle_active(self, widget_id: int) -> bool:
        """Toggle widget active state."""
        with self._db.get_session() as session:
            widget = session.query(Widget).filter(Widget.id == widget_id).first()
            if not widget:
                return False
            widget.active = not widget.active
            session.commit()
            return widget.active