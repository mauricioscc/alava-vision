"""Pydantic schemas for Widget data validation."""

from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field


class WidgetCreate(BaseModel):
    """Schema for creating a new widget."""
    name: str = Field(..., min_length=1, max_length=255)
    widget_type: str = Field(..., pattern=r"^(site|image|video|pdf|html|text|clock|countdown|weather)$")
    duration: int = Field(default=10, ge=1, le=86400)
    config: dict[str, Any] = Field(default_factory=dict)
    priority: int = Field(default=1, ge=1, le=1000)
    active: bool = True
    browser_profile_id: Optional[int] = None


class WidgetUpdate(BaseModel):
    """Schema for updating an existing widget."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    duration: Optional[int] = Field(None, ge=1, le=86400)
    config: Optional[dict[str, Any]] = None
    priority: Optional[int] = Field(None, ge=1, le=1000)
    active: Optional[bool] = None
    browser_profile_id: Optional[int] = None


class WidgetResponse(BaseModel):
    """Schema for widget response data."""
    id: int
    name: str
    widget_type: str
    duration: int
    config: dict[str, Any]
    priority: int
    active: bool
    browser_profile_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True