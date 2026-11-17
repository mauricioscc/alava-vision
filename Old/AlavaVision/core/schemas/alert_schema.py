"""Pydantic schemas for Alert data validation."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class AlertCreate(BaseModel):
    """Schema for creating a new alert."""
    title: Optional[str] = Field(None, max_length=255)
    message: str = Field(..., min_length=1)
    alert_type: str = Field(default="overlay_center", pattern=r"^(overlay_center|banner_top|banner_bottom|fullscreen|toast|ticker)$")
    position: str = Field(default="center", pattern=r"^(top_left|top_right|center|bottom_left|bottom_right)$")
    animation: str = Field(default="fade", pattern=r"^(fade|slide|zoom|none)$")
    background_color: Optional[str] = None
    text_color: Optional[str] = None
    icon: Optional[str] = None
    image_path: Optional[str] = None
    audio_id: Optional[int] = None
    duration: int = Field(default=10, ge=1, le=86400)
    priority: int = Field(default=10, ge=1, le=1000)
    active: bool = True


class AlertUpdate(BaseModel):
    """Schema for updating an existing alert."""
    title: Optional[str] = Field(None, max_length=255)
    message: Optional[str] = None
    alert_type: Optional[str] = None
    position: Optional[str] = None
    animation: Optional[str] = None
    background_color: Optional[str] = None
    text_color: Optional[str] = None
    icon: Optional[str] = None
    image_path: Optional[str] = None
    audio_id: Optional[int] = None
    duration: Optional[int] = Field(None, ge=1, le=86400)
    priority: Optional[int] = Field(None, ge=1, le=1000)
    active: Optional[bool] = None


class AlertResponse(BaseModel):
    """Schema for alert response data."""
    id: int
    title: Optional[str]
    message: str
    alert_type: str
    position: str
    animation: str
    background_color: Optional[str]
    text_color: Optional[str]
    icon: Optional[str]
    image_path: Optional[str]
    audio_id: Optional[int]
    duration: int
    priority: int
    active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True