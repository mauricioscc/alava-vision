"""ScheduleRule model - for display scheduling rules."""

import enum
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Boolean, Time, Date, Enum, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database import Base


class RuleType(str, enum.Enum):
    """Types of scheduling rules."""
    TIME_RANGE = "time_range"       # between specific hours
    DAY_OF_WEEK = "day_of_week"     # specific days (mon-fri)
    DATE_RANGE = "date_range"       # between specific dates
    SPECIFIC_DATE = "specific_date" # a specific date
    SPECIFIC_DAY = "specific_day"   # e.g., only friday


class DayOfWeek(str, enum.Enum):
    """Days of the week."""
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


class ScheduleRule(Base):
    """Represents a scheduling rule for widgets or alerts."""

    __tablename__ = "schedule_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    widget_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("widgets.id", ondelete="CASCADE"), nullable=True
    )
    alert_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("alerts.id", ondelete="CASCADE"), nullable=True
    )
    rule_type: Mapped[RuleType] = mapped_column(Enum(RuleType), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Time range
    start_time: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)  # HH:MM
    end_time: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)    # HH:MM

    # Days of week (comma-separated)
    days_of_week: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Date range
    start_date: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)  # YYYY-MM-DD
    end_date: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)    # YYYY-MM-DD

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    # Relationships
    widget = relationship("Widget", back_populates="schedule_rules")
    alert = relationship("Alert", back_populates="schedule_rules")

    def __repr__(self) -> str:
        return f"<ScheduleRule(id={self.id}, type='{self.rule_type}')>"