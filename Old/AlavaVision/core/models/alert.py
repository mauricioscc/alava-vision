"""Alert model - for overlay notifications on the player."""

import enum
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Boolean, Text, Enum, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database import Base


class AlertType(str, enum.Enum):
    """Types of alert display modes."""
    OVERLAY_CENTER = "overlay_center"
    BANNER_TOP = "banner_top"
    BANNER_BOTTOM = "banner_bottom"
    FULLSCREEN = "fullscreen"
    TOAST = "toast"
    TICKER = "ticker"


class AlertPosition(str, enum.Enum):
    """Position of the alert on screen."""
    TOP_LEFT = "top_left"
    TOP_RIGHT = "top_right"
    CENTER = "center"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_RIGHT = "bottom_right"


class AlertAnimation(str, enum.Enum):
    """Animation types for alerts."""
    FADE = "fade"
    SLIDE = "slide"
    ZOOM = "zoom"
    NONE = "none"


class Alert(Base):
    """Represents an alert that can be shown over content."""

    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    alert_type: Mapped[AlertType] = mapped_column(Enum(AlertType), default=AlertType.OVERLAY_CENTER)
    position: Mapped[AlertPosition] = mapped_column(Enum(AlertPosition), default=AlertPosition.CENTER)
    animation: Mapped[AlertAnimation] = mapped_column(Enum(AlertAnimation), default=AlertAnimation.FADE)
    background_color: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    text_color: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    icon: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    image_path: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    audio_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("audios.id"), nullable=True
    )
    duration: Mapped[int] = mapped_column(Integer, default=10)  # seconds
    priority: Mapped[int] = mapped_column(Integer, default=10)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now
    )

    # Relationships
    audio = relationship("Audio", back_populates="alerts")
    schedule_rules = relationship(
        "ScheduleRule", back_populates="alert", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Alert(id={self.id}, title='{self.title}', type='{self.alert_type}')>"