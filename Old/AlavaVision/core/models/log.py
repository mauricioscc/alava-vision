"""Log model - for system event logging."""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from core.database import Base


class Log(Base):
    """Represents a system event log entry."""

    __tablename__ = "logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, index=True)
    level: Mapped[str] = mapped_column(String(20), default="INFO")  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    source: Mapped[str] = mapped_column(String(100), default="system")  # admin, player, server
    category: Mapped[str] = mapped_column(String(100), default="general")
    message: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON with extra data
    widget_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    player_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    def __repr__(self) -> str:
        return f"<Log(id={self.id}, level='{self.level}', message='{self.message[:50]}')>"