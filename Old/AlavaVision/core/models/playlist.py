"""Playlist and PlaylistItem models."""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database import Base


class Playlist(Base):
    """Represents a playlist containing ordered items."""

    __tablename__ = "playlists"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    loop: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now
    )

    # Relationships
    items: Mapped[list["PlaylistItem"]] = relationship(
        "PlaylistItem", back_populates="playlist",
        cascade="all, delete-orphan",
        order_by="PlaylistItem.order"
    )

    def __repr__(self) -> str:
        return f"<Playlist(id={self.id}, name='{self.name}')>"


class PlaylistItem(Base):
    """Represents a single item in a playlist."""

    __tablename__ = "playlist_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    playlist_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("playlists.id", ondelete="CASCADE"), nullable=False
    )
    widget_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("widgets.id", ondelete="CASCADE"), nullable=False
    )
    order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    duration: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # override widget duration
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    priority: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    # Relationships
    playlist: Mapped["Playlist"] = relationship("Playlist", back_populates="items")
    widget: Mapped["Widget"] = relationship("Widget", back_populates="playlist_items")

    def __repr__(self) -> str:
        return f"<PlaylistItem(id={self.id}, order={self.order}, widget_id={self.widget_id})>"