"""AlertController - CRUD operations for alerts."""

from typing import Any
from core.database import Database
from core.models.alert import Alert, AlertType, AlertPosition, AlertAnimation
from core.schemas.alert_schema import AlertCreate, AlertUpdate
from core.services.log_service import LogService


class AlertController:
    """Controller for managing alerts."""

    def __init__(self) -> None:
        self._db = Database()
        self._log = LogService()

    def get_all(self) -> list[Alert]:
        """Get all alerts."""
        with self._db.get_session() as session:
            return session.query(Alert).order_by(Alert.priority.desc(), Alert.title).all()

    def get_by_id(self, alert_id: int) -> Alert | None:
        """Get an alert by ID."""
        with self._db.get_session() as session:
            return session.query(Alert).filter(Alert.id == alert_id).first()

    def create(self, data: AlertCreate) -> Alert:
        """Create a new alert."""
        with self._db.get_session() as session:
            alert = Alert(
                title=data.title,
                message=data.message,
                alert_type=AlertType(data.alert_type),
                position=AlertPosition(data.position),
                animation=AlertAnimation(data.animation),
                background_color=data.background_color,
                text_color=data.text_color,
                icon=data.icon,
                image_path=data.image_path,
                audio_id=data.audio_id,
                duration=data.duration,
                priority=data.priority,
                active=data.active,
            )
            session.add(alert)
            session.commit()
            session.refresh(alert)
            self._log.info(
                f"Alert created: '{alert.title or alert.message[:30]}'",
                source="admin",
                category="alert",
            )
            return alert

    def update(self, alert_id: int, data: AlertUpdate) -> Alert | None:
        """Update an existing alert."""
        with self._db.get_session() as session:
            alert = session.query(Alert).filter(Alert.id == alert_id).first()
            if not alert:
                return None
            if data.title is not None:
                alert.title = data.title
            if data.message is not None:
                alert.message = data.message
            if data.alert_type is not None:
                alert.alert_type = AlertType(data.alert_type)
            if data.position is not None:
                alert.position = AlertPosition(data.position)
            if data.animation is not None:
                alert.animation = AlertAnimation(data.animation)
            if data.background_color is not None:
                alert.background_color = data.background_color
            if data.text_color is not None:
                alert.text_color = data.text_color
            if data.icon is not None:
                alert.icon = data.icon
            if data.image_path is not None:
                alert.image_path = data.image_path
            if data.audio_id is not None:
                alert.audio_id = data.audio_id
            if data.duration is not None:
                alert.duration = data.duration
            if data.priority is not None:
                alert.priority = data.priority
            if data.active is not None:
                alert.active = data.active
            session.commit()
            session.refresh(alert)
            self._log.info(
                f"Alert updated: '{alert.title or alert.message[:30]}'",
                source="admin",
                category="alert",
            )
            return alert

    def delete(self, alert_id: int) -> bool:
        """Delete an alert."""
        with self._db.get_session() as session:
            alert = session.query(Alert).filter(Alert.id == alert_id).first()
            if not alert:
                return False
            name = alert.title or alert.message[:30]
            session.delete(alert)
            session.commit()
            self._log.info(
                f"Alert deleted: '{name}'",
                source="admin",
                category="alert",
            )
            return True

    def toggle_active(self, alert_id: int) -> bool:
        """Toggle alert active state."""
        with self._db.get_session() as session:
            alert = session.query(Alert).filter(Alert.id == alert_id).first()
            if not alert:
                return False
            alert.active = not alert.active
            session.commit()
            return alert.active