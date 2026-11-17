"""MainWindow - Main application window for the Admin interface."""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QStackedWidget, QLabel, QFrame,
    QListWidget, QListWidgetItem, QApplication, QMessageBox,
    QSplitter, QStatusBar,
)
from PySide6.QtCore import Qt, QSize, Signal, Slot
from PySide6.QtGui import QFont, QIcon, QAction

from admin.views.dashboard_view import DashboardView
from admin.views.widget_view import WidgetView
from admin.views.playlist_view import PlaylistView
from admin.views.alert_view import AlertView
from admin.views.schedule_view import ScheduleView
from admin.views.browser_profile_view import BrowserProfileView
from admin.views.settings_view import SettingsView
from admin.views.log_view import LogView


class SidebarButton(QPushButton):
    """A styled sidebar navigation button."""

    def __init__(self, text: str, icon_text: str = "") -> None:
        super().__init__(text)
        self.setFixedHeight(44)
        self.setCursor(Qt.PointingHandCursor)
        self.setCheckable(True)
        style = """
            QPushButton {
                text-align: left;
                padding: 8px 16px;
                border: none;
                border-radius: 6px;
                font-size: 13px;
                color: #e0e0e0;
                background-color: transparent;
            }
            QPushButton:hover {
                background-color: #2a2a3e;
                color: #ffffff;
            }
            QPushButton:checked {
                background-color: #3a3a5e;
                color: #ffffff;
                font-weight: bold;
                border-left: 3px solid #6c63ff;
            }
        """
        self.setStyleSheet(style)


class MainWindow(QMainWindow):
    """Main admin application window."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("AlavaVision - Administrador")
        self.setMinimumSize(1200, 750)
        self.resize(1400, 850)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup the user interface."""
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar
        sidebar = self._create_sidebar()
        main_layout.addWidget(sidebar)

        # Content area
        self._content_stack = QStackedWidget()
        self._content_stack.setStyleSheet("background-color: #1a1a2e;")
        main_layout.addWidget(self._content_stack, 1)

        # Create views
        self._create_views()

        # Status bar
        self.statusBar().showMessage("Pronto")

        # Apply global stylesheet
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1a1a2e;
            }
            QStatusBar {
                background-color: #16213e;
                color: #a0a0b0;
                border-top: 1px solid #2a2a3e;
                padding: 4px;
            }
            QScrollBar:vertical {
                background-color: #1a1a2e;
                width: 10px;
                border: none;
            }
            QScrollBar::handle:vertical {
                background-color: #3a3a5e;
                border-radius: 5px;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

    def _create_sidebar(self) -> QFrame:
        """Create the sidebar navigation."""
        sidebar = QFrame()
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet("""
            QFrame {
                background-color: #16213e;
                border-right: 1px solid #2a2a3e;
            }
        """)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(12, 16, 12, 16)
        layout.setSpacing(4)

        # Logo / Title
        title = QLabel("AlavaVision")
        title.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: #6c63ff;
            padding: 8px 0 16px 0;
        """)
        layout.addWidget(title)

        # Navigation buttons
        self._nav_buttons: list[SidebarButton] = []
        nav_items = [
            ("dashboard", "📊", "Dashboard"),
            ("widgets", "🧩", "Widgets"),
            ("playlists", "📋", "Playlists"),
            ("alerts", "🔔", "Alertas"),
            ("schedules", "📅", "Agendamentos"),
            ("profiles", "🌐", "Perfis Navegador"),
            ("settings", "⚙️", "Configurações"),
            ("logs", "📝", "Logs"),
        ]

        for key, icon, label in nav_items:
            btn = SidebarButton(f"  {icon}  {label}")
            btn.clicked.connect(lambda checked=False, k=key: self._navigate_to(k))
            self._nav_buttons.append(btn)
            layout.addWidget(btn)

        layout.addStretch()

        # Version info
        version = QLabel("v0.1.0 MVP")
        version.setStyleSheet("color: #555; font-size: 11px; padding: 8px 0;")
        version.setAlignment(Qt.AlignCenter)
        layout.addWidget(version)

        return sidebar

    def _create_views(self) -> None:
        """Create all content views."""
        self._views = {}
        view_classes = {
            "dashboard": DashboardView,
            "widgets": WidgetView,
            "playlists": PlaylistView,
            "alerts": AlertView,
            "schedules": ScheduleView,
            "profiles": BrowserProfileView,
            "settings": SettingsView,
            "logs": LogView,
        }
        for key, view_class in view_classes.items():
            view = view_class(self)
            self._views[key] = view
            self._content_stack.addWidget(view)

        # Start with dashboard
        self._navigate_to("dashboard")

    def _navigate_to(self, view_key: str) -> None:
        """Navigate to a specific view."""
        if view_key in self._views:
            self._content_stack.setCurrentWidget(self._views[view_key])
            for btn in self._nav_buttons:
                btn.setChecked(False)
            # Find and check the matching button
            idx = ["dashboard", "widgets", "playlists", "alerts",
                   "schedules", "profiles", "settings", "logs"].index(view_key)
            if 0 <= idx < len(self._nav_buttons):
                self._nav_buttons[idx].setChecked(True)
            self.statusBar().showMessage(f"Seção: {view_key.capitalize()}")

    def show_status(self, message: str, timeout: int = 5000) -> None:
        """Show a status message."""
        self.statusBar().showMessage(message, timeout)