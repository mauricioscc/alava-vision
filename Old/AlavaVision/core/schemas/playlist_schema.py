"""Pydantic schemas for Playlist data validation."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class PlaylistItemCreate(BaseModel):
    """Schema for creating a playlist item."""
    widget_id: int = Field(..., ge=1)
    order: int = Field(..., ge=0)
    duration: Optional[int] = Field(None, ge=1, le=86400)
    active: bool = True
    priority: int = Field(default=1, ge=1, le=1000)


class PlaylistItemUpdate(BaseModel):
    """Schema for updating a playlist item."""
    widget_id: Optional[int] = None
    order: Optional[int] = None
    duration: Optional[int] = None
    active: Optional[bool] = None
    priority: Optional[int] = None


class PlaylistItemResponse(BaseModel):
    """Schema for playlist item response."""
    id: int
    playlist_id: int
    widget_id: int
    order: int
    duration: Optional[int] = None
    active: bool
    priority: int
    widget_name: Optional[str] = None
    widget_type: Optional[str] = None

    class Config:
        from_attributes = True


class PlaylistCreate(BaseModel):
    """Schema for creating a playlist."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    active: bool = True
    loop: bool = True


class PlaylistUpdate(BaseModel):
    """Schema for updating a playlist."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    active: Optional[bool] = None
    loop: Optional[bool] = None


class PlaylistResponse(BaseModel):
    """Schema for playlist response."""
    id: int
    name: str
    description: Optional[str] = None
    active: bool
    loop: bool
    created_at: datetime
    updated_at: datetime
    items: list[PlaylistItemResponse] = []

    class Config:
        from_attributes = True