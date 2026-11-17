"""Widget model - represents a content widget."""

import enum
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Boolean, Text, Enum, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database import Base


class WidgetType(str, enum.Enum):
    """Types of widgets available in the system."""
    SITE = "site"
    IMAGE = "image"
    VIDEO = "video"
    PDF = "pdf"
    HTML = "html"
    TEXT = "text"
    CLOCK = "clock"
    COUNTDOWN = "countdown"
    WEATHER = "weather"


class Widget(Base):
    """Represents a content widget that can be added to playlists."""

    __tablename__ = "widgets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    widget_type: Mapped[WidgetType] = mapped_column(Enum(WidgetType), nullable=False)
    duration: Mapped[int] = mapped_column(Integer, default=10)  # seconds
    config: Mapped[str] = mapped_column(Text, default="{}")  # JSON config
    priority: Mapped[int] = mapped_column(Integer, default=1)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    browser_profile_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("browser_profiles.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now
    )

    # Relationships
    browser_profile = relationship("BrowserProfile", back_populates="widgets")
    schedule_rules = relationship(
        "ScheduleRule", back_populates="widget", cascade="all, delete-orphan"
    )
    playlist_items = relationship(
        "PlaylistItem", back_populates="widget", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Widget(id={self.id}, name='{self.name}', type='{self.widget_type}')>"