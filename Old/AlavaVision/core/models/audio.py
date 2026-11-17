"""Audio model - for alert sounds."""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Float, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database import Base


class Audio(Base):
    """Represents an audio file for alerts."""

    __tablename__ = "audios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    duration: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # seconds
    file_size: Mapped[int] = mapped_column(Integer, default=0)
    format: Mapped[str] = mapped_column(String(10), default="mp3")
    active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    # Relationships
    alerts = relationship("Alert", back_populates="audio")

    def __repr__(self) -> str:
        return f"<Audio(id={self.id}, name='{self.name}')>"