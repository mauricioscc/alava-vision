"""Pydantic schemas for BrowserProfile data validation."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class BrowserProfileCreate(BaseModel):
    """Schema for creating a new browser profile."""
    name: str = Field(..., min_length=1, max_length=255)
    profile_path: str = Field(..., min_length=1)
    user_agent: Optional[str] = None
    javascript_enabled: bool = True
    cookies_enabled: bool = True
    zoom_factor: float = Field(default=1.0, ge=0.1, le=5.0)
    extra_args: Optional[str] = None
    active: bool = True


class BrowserProfileUpdate(BaseModel):
    """Schema for updating a browser profile."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    profile_path: Optional[str] = None
    user_agent: Optional[str] = None
    javascript_enabled: Optional[bool] = None
    cookies_enabled: Optional[bool] = None
    zoom_factor: Optional[float] = Field(None, ge=0.1, le=5.0)
    extra_args: Optional[str] = None
    active: Optional[bool] = None


class BrowserProfileResponse(BaseModel):
    """Schema for browser profile response."""
    id: int
    name: str
    profile_path: str
    user_agent: Optional[str]
    javascript_enabled: bool
    cookies_enabled: bool
    zoom_factor: float
    extra_args: Optional[str]
    active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True