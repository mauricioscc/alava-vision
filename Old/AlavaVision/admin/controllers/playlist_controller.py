"""PlaylistController - CRUD operations for playlists."""

from typing import Any
from core.database import Database
from core.models.playlist import Playlist, PlaylistItem
from core.models.widget import Widget
from core.schemas.playlist_schema import PlaylistCreate, PlaylistUpdate, PlaylistItemCreate
from core.services.log_service import LogService


class PlaylistController:
    """Controller for managing playlists."""

    def __init__(self) -> None:
        self._db = Database()
        self._log = LogService()

    def get_all(self) -> list[Playlist]:
        """Get all playlists."""
        with self._db.get_session() as session:
            return session.query(Playlist).order_by(Playlist.name).all()

    def get_all_with_counts(self) -> list[dict[str, Any]]:
        """Get all playlists with item counts (avoids lazy loading issues)."""
        with self._db.get_session() as session:
            playlists = session.query(Playlist).order_by(Playlist.name).all()
            result = []
            for pl in playlists:
                result.append({
                    "id": pl.id,
                    "name": pl.name,
                    "item_count": len(pl.items),
                })
            return result

    def get_by_id(self, playlist_id: int) -> Playlist | None:
        """Get a playlist by ID with items."""
        with self._db.get_session() as session:
            return session.query(Playlist).filter(Playlist.id == playlist_id).first()

    def create(self, data: PlaylistCreate) -> Playlist:
        """Create a new playlist."""
        with self._db.get_session() as session:
            playlist = Playlist(
                name=data.name,
                description=data.description,
                active=data.active,
                loop=data.loop,
            )
            session.add(playlist)
            session.commit()
            session.refresh(playlist)
            self._log.info(
                f"Playlist created: '{playlist.name}'",
                source="admin",
                category="playlist",
            )
            return playlist

    def update(self, playlist_id: int, data: PlaylistUpdate) -> Playlist | None:
        """Update a playlist."""
        with self._db.get_session() as session:
            playlist = session.query(Playlist).filter(Playlist.id == playlist_id).first()
            if not playlist:
                return None
            if data.name is not None:
                playlist.name = data.name
            if data.description is not None:
                playlist.description = data.description
            if data.active is not None:
                playlist.active = data.active
            if data.loop is not None:
                playlist.loop = data.loop
            session.commit()
            session.refresh(playlist)
            return playlist

    def delete(self, playlist_id: int) -> bool:
        """Delete a playlist."""
        with self._db.get_session() as session:
            playlist = session.query(Playlist).filter(Playlist.id == playlist_id).first()
            if not playlist:
                return False
            name = playlist.name
            session.delete(playlist)
            session.commit()
            self._log.info(
                f"Playlist deleted: '{name}'",
                source="admin",
                category="playlist",
            )
            return True

    def add_item(self, playlist_id: int, data: PlaylistItemCreate) -> PlaylistItem | None:
        """Add an item to a playlist."""
        with self._db.get_session() as session:
            playlist = session.query(Playlist).filter(Playlist.id == playlist_id).first()
            if not playlist:
                return None
            widget = session.query(Widget).filter(Widget.id == data.widget_id).first()
            if not widget:
                return None
            item = PlaylistItem(
                playlist_id=playlist_id,
                widget_id=data.widget_id,
                order=data.order,
                duration=data.duration,
                active=data.active,
                priority=data.priority,
            )
            session.add(item)
            session.commit()
            session.refresh(item)
            return item

    def remove_item(self, item_id: int) -> bool:
        """Remove an item from a playlist."""
        with self._db.get_session() as session:
            item = session.query(PlaylistItem).filter(PlaylistItem.id == item_id).first()
            if not item:
                return False
            session.delete(item)
            session.commit()
            return True

    def reorder_items(self, playlist_id: int, item_ids: list[int]) -> bool:
        """Reorder playlist items."""
        with self._db.get_session() as session:
            for order, item_id in enumerate(item_ids):
                item = session.query(PlaylistItem).filter(
                    PlaylistItem.id == item_id,
                    PlaylistItem.playlist_id == playlist_id,
                ).first()
                if item:
                    item.order = order
            session.commit()
            return True

    def get_playlist_with_widgets(self, playlist_id: int) -> list[dict[str, Any]]:
        """Get playlist items with widget details."""
        with self._db.get_session() as session:
            items = (
                session.query(PlaylistItem, Widget)
                .join(Widget, PlaylistItem.widget_id == Widget.id)
                .filter(PlaylistItem.playlist_id == playlist_id)
                .order_by(PlaylistItem.order)
                .all()
            )
            result = []
            for item, widget in items:
                result.append({
                    "item_id": item.id,
                    "order": item.order,
                    "duration": item.duration or widget.duration,
                    "active": item.active,
                    "priority": item.priority,
                    "widget_id": widget.id,
                    "widget_name": widget.name,
                    "widget_type": widget.widget_type.value,
                })
            return result