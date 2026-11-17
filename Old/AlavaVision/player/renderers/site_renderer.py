"""SiteRenderer - renders web pages using QWebEngineView with optimizations."""

import json
from pathlib import Path
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineProfile, QWebEnginePage, QWebEngineSettings
from PySide6.QtCore import QUrl, QTimer, Qt
from core.widgets.base_widget import BaseWidget
from core.database import Database
from core.models.browser_profile import BrowserProfile
from core.services.log_service import LogService
from player.renderers.base_renderer import BaseRenderer


# Modern Chrome User-Agent para evitar bloqueios de sites
MODERN_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


class CustomWebEnginePage(QWebEnginePage):
    """Custom QWebEnginePage that logs JavaScript errors."""

    def __init__(self, profile: QWebEngineProfile, log: LogService, parent=None) -> None:
        super().__init__(profile, parent)
        self._log = log
        self._widget_id: int = 0

    def javaScriptConsoleMessage(self, level: int, message: str, line: int, source: str) -> None:
        """Capture JavaScript console messages for debugging."""
        level_map = {0: "INFO", 1: "WARNING", 2: "ERROR"}
        level_name = level_map.get(level, "UNKNOWN")
        self._log.debug(
            f"[JS {level_name}] {message} (line {line}, {source})",
            source="player", category="site_js", widget_id=self._widget_id,
        )


class SiteRenderer(BaseRenderer):
    """Renderer for displaying web pages.

    Uses QWebEngineView with persistent profiles for session management.
    Supports auto-refresh, zoom, and scrollbar control.
    Optimized for performance with modern User-Agent and JS error logging.
    """

    def __init__(self, widget: BaseWidget, parent: QWidget | None = None) -> None:
        super().__init__(widget, parent)
        self._web_view: QWebEngineView | None = None
        self._profile: QWebEngineProfile | None = None
        self._page: CustomWebEnginePage | None = None
        self._refresh_timer: QTimer | None = None
        self._load_timeout: QTimer | None = None
        self._container: QWidget | None = None
        self._loading_label: QLabel | None = None
        self._log = LogService()
        self._load_started: bool = False

    def create_ui(self) -> QWidget:
        """Create the web view widget with loading indicator."""
        self._container = QWidget()
        layout = QVBoxLayout(self._container)
        layout.setContentsMargins(0, 0, 0, 0)

        # Loading indicator (shown briefly while page loads)
        self._loading_label = QLabel("Carregando...")
        self._loading_label.setAlignment(Qt.AlignCenter)
        self._loading_label.setStyleSheet("""
            QLabel {
                color: #888888;
                font-size: 24px;
                background-color: #000000;
            }
        """)
        layout.addWidget(self._loading_label)

        # Setup profile
        profile_name = f"widget_{self.widget.id}"
        profile_path = None

        if self.widget.browser_profile_id:
            profile_path = self._load_browser_profile_path()

        if profile_path:
            self._profile = QWebEngineProfile(profile_name, self._container)
            self._profile.setPersistentStoragePath(str(profile_path))
            self._profile.setPersistentCookiesPolicy(
                QWebEngineProfile.ForcePersistentCookies
            )
        else:
            self._profile = QWebEngineProfile(profile_name, self._container)
            profile_dir = str(Path("data/profiles") / f"widget_{self.widget.id}")
            self._profile.setPersistentStoragePath(profile_dir)
            self._profile.setPersistentCookiesPolicy(
                QWebEngineProfile.ForcePersistentCookies
            )

        # Set modern User-Agent
        self._profile.setHttpUserAgent(MODERN_UA)

        # Configure settings for maximum compatibility
        settings = self._profile.settings()
        settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.JavascriptCanOpenWindows, False)
        settings.setAttribute(QWebEngineSettings.LocalStorageEnabled, True)
        settings.setAttribute(QWebEngineSettings.PluginsEnabled, False)
        settings.setAttribute(QWebEngineSettings.FullScreenSupportEnabled, False)
        settings.setAttribute(QWebEngineSettings.WebGLEnabled, True)
        settings.setAttribute(QWebEngineSettings.Accelerated2dCanvasEnabled, True)
        settings.setAttribute(QWebEngineSettings.AutoLoadImages, True)
        settings.setAttribute(QWebEngineSettings.ErrorPageEnabled, False)
        settings.setAttribute(QWebEngineSettings.HyperlinkAuditingEnabled, False)
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessFileUrls, True)

        # Create custom page with JS error logging
        self._page = CustomWebEnginePage(self._profile, self._log, self._container)
        self._page._widget_id = self.widget.id

        # Create web view
        self._web_view = QWebEngineView(self._container)
        self._web_view.setPage(self._page)
        self._web_view.setStyleSheet("background-color: #000000;")

        # Hide the web view initially (will show when loaded)
        self._web_view.hide()

        layout.addWidget(self._web_view)

        # Connect signals
        self._web_view.loadStarted.connect(self._on_load_started)
        self._web_view.loadProgress.connect(self._on_load_progress)
        self._web_view.loadFinished.connect(self._on_load_finished)

        return self._container

    def _load_browser_profile_path(self) -> Path | None:
        """Load the browser profile path from database."""
        try:
            db = Database()
            with db.get_session() as session:
                profile = session.query(BrowserProfile).filter(
                    BrowserProfile.id == self.widget.browser_profile_id
                ).first()
                if profile:
                    return Path(profile.profile_path)
        except Exception as e:
            self._log.warning(
                f"Could not load browser profile: {e}",
                source="player",
                category="browser_profile",
            )
        return None

    def start(self) -> None:
        """Load the URL and start displaying."""
        url = self.widget.config.get("url", "")
        if not url:
            self._log.error(
                f"No URL configured for widget '{self.widget.name}'",
                source="player",
                category="site",
                widget_id=self.widget.id,
            )
            return

        self._load_started = False

        self._log.info(
            f"Loading URL: {url}",
            source="player",
            category="site",
            widget_id=self.widget.id,
        )

        # Show loading indicator
        if self._loading_label:
            self._loading_label.show()
        if self._web_view:
            self._web_view.hide()

        # Apply zoom
        zoom = self.widget.config.get("zoom_factor", 1.0)
        if self._web_view:
            self._web_view.setZoomFactor(zoom)

        # Load URL
        if self._web_view:
            self._web_view.load(QUrl(url))

        # Page load timeout (60 seconds for heavy pages)
        self._load_timeout = QTimer()
        self._load_timeout.setSingleShot(True)
        self._load_timeout.timeout.connect(self._on_load_timeout)
        self._load_timeout.start(60000)

        # Setup auto-refresh
        auto_refresh = self.widget.config.get("auto_refresh", 0)
        if auto_refresh > 0:
            self._refresh_timer = QTimer()
            self._refresh_timer.timeout.connect(self._refresh_page)
            self._refresh_timer.start(auto_refresh * 1000)

    def stop(self) -> None:
        """Stop the web view and clean up."""
        if self._refresh_timer:
            self._refresh_timer.stop()
            self._refresh_timer = None
        if self._load_timeout:
            self._load_timeout.stop()
            self._load_timeout = None
        if self._web_view:
            self._web_view.stop()
            self._web_view.load(QUrl("about:blank"))
            self._web_view = None
        self._page = None
        self._profile = None
        self._container = None
        self._loading_label = None

    def _refresh_page(self) -> None:
        """Reload the current page."""
        if self._web_view:
            self._web_view.reload()

    def _on_load_started(self) -> None:
        """Handle page load start."""
        self._load_started = True
        if self._loading_label:
            self._loading_label.setText("Carregando...")

    def _on_load_progress(self, progress: int) -> None:
        """Update loading progress."""
        if self._loading_label and progress < 100:
            self._loading_label.setText(f"Carregando... {progress}%")

    def _on_load_finished(self, ok: bool) -> None:
        """Handle page load completion."""
        if self._load_timeout:
            self._load_timeout.stop()

        if ok:
            # Hide loading, show web view
            if self._loading_label:
                self._loading_label.hide()
            if self._web_view:
                self._web_view.show()

            self._log.info(
                f"Page loaded successfully: {self.widget.config.get('url', '')}",
                source="player",
                category="site",
                widget_id=self.widget.id,
            )

            # Inject fixes after page load
            if self._web_view:
                js = """
                // Fix scrollbars
                document.body.style.overflow = 'hidden';
                document.documentElement.style.overflow = 'hidden';

                // Fix viewport for embedded display
                var meta = document.querySelector('meta[name=\"viewport\"]');
                if (!meta) {
                    meta = document.createElement('meta');
                    meta.name = 'viewport';
                    document.head.appendChild(meta);
                }
                meta.content = 'width=device-width, initial-scale=1.0';

                // Force re-render to fix "no data" issues
                document.body.style.display = 'none';
                document.body.offsetHeight; // trigger reflow
                document.body.style.display = '';
                """
                self._web_view.page().runJavaScript(js)

            # Apply scroll position if configured
            scroll_x = self.widget.config.get("scroll_horizontal", 0)
            scroll_y = self.widget.config.get("scroll_vertical", 0)
            if scroll_x or scroll_y and self._web_view:
                self._web_view.page().runJavaScript(
                    f"window.scrollTo({scroll_x}, {scroll_y});"
                )
        else:
            self._log.error(
                f"Failed to load page: {self.widget.config.get('url', '')}",
                source="player",
                category="site",
                widget_id=self.widget.id,
            )
            if self._loading_label:
                self._loading_label.setText("Erro ao carregar")

    def _on_load_timeout(self) -> None:
        """Handle page load timeout."""
        if self._web_view and self._load_started:
            self._web_view.stop()
            self._log.warning(
                f"Page load timed out: {self.widget.config.get('url', '')}",
                source="player",
                category="site",
                widget_id=self.widget.id,
            )
            if self._loading_label:
                self._loading_label.setText("Tempo esgotado")