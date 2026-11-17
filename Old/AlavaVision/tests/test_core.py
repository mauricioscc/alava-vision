"""Core tests for AlavaVision."""

import sys
import os
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Use offscreen mode for testing
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from core.database import Database
from core.models import *
from core.models.widget import WidgetType
from core.models.schedule import RuleType, DayOfWeek
from core.services.schedule_engine import ScheduleEngine
from core.services.log_service import LogService
from core.widgets.site_widget import SiteWidget
from core.widgets.image_widget import ImageWidget
from core.widgets.text_widget import TextWidget
from admin.controllers.widget_controller import WidgetController
from admin.controllers.playlist_controller import PlaylistController
from core.schemas.widget_schema import WidgetCreate, WidgetUpdate
from core.schemas.playlist_schema import PlaylistCreate, PlaylistItemCreate


def test_database():
    """Test database initialization."""
    db = Database()
    db.create_all()
    print("[OK] Database created successfully")


def test_widget_creation():
    """Test widget creation via controller."""
    wc = WidgetController()
    
    # Create widgets
    w1 = wc.create(WidgetCreate(
        name="Dashboard Vendas",
        widget_type="site",
        duration=30,
        config={"url": "https://vendas.empresa.com/dashboard"},
        priority=1,
    ))
    assert w1.id > 0
    assert w1.name == "Dashboard Vendas"
    print(f"[OK] Created site widget: {w1.name} (ID: {w1.id})")

    w2 = wc.create(WidgetCreate(
        name="Logo Institucional",
        widget_type="image",
        duration=15,
        config={"file_path": "data/files/logo.png", "fit_mode": "contain"},
    ))
    assert w2.id > 0
    print(f"[OK] Created image widget: {w2.name} (ID: {w2.id})")

    w3 = wc.create(WidgetCreate(
        name="Mensagem Boas Vindas",
        widget_type="text",
        duration=10,
        config={
            "text": "Bem-vindo à nossa empresa!",
            "font_size": 48,
            "font_color": "#FFFFFF",
            "background_color": "#1a1a2e",
        },
    ))
    assert w3.id > 0
    print(f"[OK] Created text widget: {w3.name} (ID: {w3.id})")

    # Test update
    wc.update(w1.id, WidgetUpdate(duration=60))
    updated = wc.get_by_id(w1.id)
    assert updated.duration == 60
    print(f"[OK] Updated widget duration to {updated.duration}s")

    # Test get all
    all_widgets = wc.get_all()
    assert len(all_widgets) >= 3
    print(f"[OK] Total widgets: {len(all_widgets)}")

    return w1, w2, w3


def test_playlist():
    """Test playlist creation and management."""
    wc = WidgetController()
    pc = PlaylistController()

    # Get widgets
    widgets = wc.get_all()
    assert len(widgets) >= 3

    # Create playlist
    pl = pc.create(PlaylistCreate(
        name="Playlist Principal",
        description="Playlist principal da TV corporativa",
        loop=True,
    ))
    assert pl.id > 0
    print(f"[OK] Created playlist: {pl.name} (ID: {pl.id})")

    # Add items
    for i, w in enumerate(widgets):
        item = pc.add_item(pl.id, PlaylistItemCreate(
            widget_id=w.id,
            order=i,
            duration=w.duration,
        ))
        assert item.id > 0
        print(f"  [+] Added: {w.name} (order: {i}, duration: {w.duration}s)")

    # Verify items
    items = pc.get_playlist_with_widgets(pl.id)
    assert len(items) == len(widgets)
    print(f"[OK] Playlist has {len(items)} items")

    # Test reorder
    item_ids = [it["item_id"] for it in reversed(items)]
    pc.reorder_items(pl.id, item_ids)
    print(f"[OK] Reordered playlist items")

    return pl


def test_schedule_engine():
    """Test schedule engine rules."""
    from datetime import datetime, time

    # Test time range rule
    rule = type('Rule', (), {
        'active': True,
        'rule_type': RuleType.TIME_RANGE,
        'start_time': '08:00',
        'end_time': '18:00',
        'days_of_week': None,
        'start_date': None,
        'end_date': None,
    })()

    # Should pass during business hours
    business_hours = datetime(2026, 8, 12, 14, 0)  # 2 PM
    assert ScheduleEngine.evaluate_rules([rule], business_hours) == True
    print("[OK] Time range rule: business hours passes")

    # Should fail outside business hours
    after_hours = datetime(2026, 8, 12, 20, 0)  # 8 PM
    assert ScheduleEngine.evaluate_rules([rule], after_hours) == False
    print("[OK] Time range rule: after hours fails")

    # Test day of week rule
    day_rule = type('Rule', (), {
        'active': True,
        'rule_type': RuleType.DAY_OF_WEEK,
        'start_time': None,
        'end_time': None,
        'days_of_week': 'monday,tuesday,wednesday,thursday,friday',
        'start_date': None,
        'end_date': None,
    })()

    wednesday = datetime(2026, 8, 12, 10, 0)  # Wednesday
    assert ScheduleEngine.evaluate_rules([day_rule], wednesday) == True
    print("[OK] Day of week rule: Wednesday passes")

    # Test priority interruption
    assert ScheduleEngine.should_interrupt(1, 10) == True
    assert ScheduleEngine.should_interrupt(10, 5) == False
    print("[OK] Priority interruption logic works")


def test_widget_validation():
    """Test widget validation."""
    # Valid site widget
    w = SiteWidget(1, "Test", 30, {"url": "https://example.com"})
    assert w.validate() == True
    assert w.get_renderer_class() == "site_renderer"
    print(f"[OK] SiteWidget valid: {w.validate()}")

    # Invalid site widget (no URL)
    w2 = SiteWidget(2, "Invalid", 30, {})
    assert w2.validate() == False
    print(f"[OK] SiteWidget invalid (no URL): {w2.validate()}")

    # Valid image widget
    i = ImageWidget(3, "Image", 10, {"file_path": "test.png"})
    assert i.validate() == True
    print(f"[OK] ImageWidget valid: {i.validate()}")

    # Valid text widget
    t = TextWidget(4, "Text", 10, {"text": "Hello"})
    assert t.validate() == True
    print(f"[OK] TextWidget valid: {t.validate()}")


def test_log_service():
    """Test logging service."""
    log = LogService()
    log.info("Test info message", source="test", category="testing")
    log.warning("Test warning message", source="test", category="testing")
    log.error("Test error message", source="test", category="testing")
    print("[OK] Log service works")


if __name__ == "__main__":
    print("=" * 50)
    print("AlavaVision - Core Tests")
    print("=" * 50)
    print()

    test_database()
    test_widget_validation()
    test_widget_creation()
    test_playlist()
    test_schedule_engine()
    test_log_service()

    print()
    print("=" * 50)
    print("[OK] All tests passed!")
    print("=" * 50)