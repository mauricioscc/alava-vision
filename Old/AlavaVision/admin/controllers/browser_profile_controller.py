"""BrowserProfileController - CRUD operations for browser profiles."""

from core.database import Database
from core.models.browser_profile import BrowserProfile
from core.schemas.browser_profile_schema import BrowserProfileCreate, BrowserProfileUpdate
from core.services.log_service import LogService


class BrowserProfileController:
    """Controller for managing browser profiles."""

    def __init__(self) -> None:
        self._db = Database()
        self._log = LogService()

    def get_all(self) -> list[BrowserProfile]:
        """Get all browser profiles."""
        with self._db.get_session() as session:
            return session.query(BrowserProfile).order_by(BrowserProfile.name).all()

    def get_by_id(self, profile_id: int) -> BrowserProfile | None:
        """Get a profile by ID."""
        with self._db.get_session() as session:
            return session.query(BrowserProfile).filter(BrowserProfile.id == profile_id).first()

    def create(self, data: BrowserProfileCreate) -> BrowserProfile:
        """Create a new browser profile."""
        with self._db.get_session() as session:
            profile = BrowserProfile(
                name=data.name,
                profile_path=data.profile_path,
                user_agent=data.user_agent,
                javascript_enabled=data.javascript_enabled,
                cookies_enabled=data.cookies_enabled,
                zoom_factor=data.zoom_factor,
                extra_args=data.extra_args,
                active=data.active,
            )
            session.add(profile)
            session.commit()
            session.refresh(profile)
            self._log.info(
                f"Browser profile created: '{profile.name}'",
                source="admin",
                category="profile",
            )
            return profile

    def update(self, profile_id: int, data: BrowserProfileUpdate) -> BrowserProfile | None:
        """Update an existing browser profile."""
        with self._db.get_session() as session:
            profile = session.query(BrowserProfile).filter(BrowserProfile.id == profile_id).first()
            if not profile:
                return None
            if data.name is not None:
                profile.name = data.name
            if data.profile_path is not None:
                profile.profile_path = data.profile_path
            if data.user_agent is not None:
                profile.user_agent = data.user_agent
            if data.javascript_enabled is not None:
                profile.javascript_enabled = data.javascript_enabled
            if data.cookies_enabled is not None:
                profile.cookies_enabled = data.cookies_enabled
            if data.zoom_factor is not None:
                profile.zoom_factor = data.zoom_factor
            if data.extra_args is not None:
                profile.extra_args = data.extra_args
            if data.active is not None:
                profile.active = data.active
            session.commit()
            session.refresh(profile)
            self._log.info(
                f"Browser profile updated: '{profile.name}'",
                source="admin",
                category="profile",
            )
            return profile

    def delete(self, profile_id: int) -> bool:
        """Delete a browser profile."""
        with self._db.get_session() as session:
            profile = session.query(BrowserProfile).filter(BrowserProfile.id == profile_id).first()
            if not profile:
                return False
            name = profile.name
            session.delete(profile)
            session.commit()
            self._log.info(
                f"Browser profile deleted: '{name}'",
                source="admin",
                category="profile",
            )
            return True