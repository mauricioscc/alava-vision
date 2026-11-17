"""BrowserProfile model - for persistent browser sessions."""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Boolean, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database import Base


class BrowserProfile(Base):
    """Represents a browser profile with persistent cookies/session."""

    __tablename__ = "browser_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    profile_path: Mapped[str] = mapped_column(String(500), nullable=False)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    javascript_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    cookies_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    zoom_factor: Mapped[float] = mapped_column(default=1.0)
    extra_args: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now
    )

    # Relationships
    widgets = relationship("Widget", back_populates="browser_profile")

    def __repr__(self) -> str:
        return f"<BrowserProfile(id={self.id}, name='{self.name}')>"