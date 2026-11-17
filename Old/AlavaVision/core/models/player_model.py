"""Player model - represents a player device."""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Boolean, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from core.database import Base


class Player(Base):
    """Represents a player device that displays content."""

    __tablename__ = "players"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    hostname: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    monitor_index: Mapped[int] = mapped_column(Integer, default=1)
    fullscreen: Mapped[bool] = mapped_column(Boolean, default=True)
    active_playlist_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="offline")  # online, offline, playing, error
    last_seen: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    config: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now
    )

    def __repr__(self) -> str:
        return f"<Player(id={self.id}, name='{self.name}', status='{self.status}')>"