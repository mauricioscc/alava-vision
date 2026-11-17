"""BaseWidget - abstract base class for all widget types."""

from abc import ABC, abstractmethod
from typing import Any, Optional


class BaseWidget(ABC):
    """Abstract base class for all content widgets.
    
    Each widget type must implement this interface.
    The Player uses the renderer class returned by get_renderer_class()
    to display the widget on screen.
    """

    def __init__(
        self,
        widget_id: int,
        name: str,
        duration: int = 10,
        config: dict[str, Any] | None = None,
        priority: int = 1,
        active: bool = True,
        browser_profile_id: int | None = None,
    ) -> None:
        self.id = widget_id
        self.name = name
        self.duration = duration
        self.config = config or {}
        self.priority = priority
        self.active = active
        self.browser_profile_id = browser_profile_id

    @abstractmethod
    def validate(self) -> bool:
        """Validate widget configuration.
        
        Returns:
            True if configuration is valid, False otherwise.
        """
        ...

    @abstractmethod
    def get_renderer_class(self) -> str:
        """Return the renderer class name for this widget type.
        
        The renderer is used by the Player to display the widget.
        
        Returns:
            String name of the renderer class (e.g., 'site_renderer').
        """
        ...

    def get_duration(self) -> int:
        """Get the display duration in seconds."""
        return self.duration

    def to_dict(self) -> dict[str, Any]:
        """Convert widget to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "widget_type": self.widget_type,
            "duration": self.duration,
            "config": self.config,
            "priority": self.priority,
            "active": self.active,
            "browser_profile_id": self.browser_profile_id,
        }

    @classmethod
    def from_model(cls, model: Any) -> "BaseWidget":
        """Create a widget instance from an ORM model.
        
        Args:
            model: SQLAlchemy Widget model instance.
            
        Returns:
            Concrete BaseWidget instance.
        """
        import json
        config = {}
        if model.config:
            try:
                config = json.loads(model.config)
            except (json.JSONDecodeError, TypeError):
                config = {}

        return cls(
            widget_id=model.id,
            name=model.name,
            duration=model.duration,
            config=config,
            priority=model.priority,
            active=model.active,
            browser_profile_id=model.browser_profile_id,
        )

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id={self.id}, name='{self.name}')>"