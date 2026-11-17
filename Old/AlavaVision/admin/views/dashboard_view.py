"""DashboardView - Main dashboard showing system status."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QGridLayout, QGroupBox,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont

from core.database import Database
from core.models.widget import Widget
from core.models.playlist import Playlist
from core.models.alert import Alert
from core.services.log_service import LogService


class StatCard(QFrame):
    """A card widget for displaying statistics."""

    def __init__(self, title: str, value: str, color: str = "#6c63ff") -> None:
        super().__init__()
        self.setStyleSheet(f"""
            QFrame {{
                background-color: #16213e;
                border-radius: 12px;
                border: 1px solid #2a2a3e;
                padding: 20px;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        self._value_label = QLabel(value)
        self._value_label.setStyleSheet(f"""
            font-size: 36px;
            font-weight: bold;
            color: {color};
        """)
        layout.addWidget(self._value_label)

        self._title_label = QLabel(title)
        self._title_label.setStyleSheet("""
            font-size: 13px;
            color: #a0a0b0;
        """)
        layout.addWidget(self._title_label)

    def update_value(self, value: str) -> None:
        """Update the displayed value."""
        self._value_label.setText(value)


class DashboardView(QWidget):
    """Dashboard view showing system overview."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._db = Database()
        self._log = LogService()
        self._setup_ui()
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._refresh_data)
        self._refresh_timer.start(5000)  # Refresh every 5 seconds

    def _setup_ui(self) -> None:
        """Setup the dashboard UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(24)

        # Header
        header = QLabel("Dashboard")
        header.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
            color: #ffffff;
        """)
        layout.addWidget(header)

        # Stats cards
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(16)

        self._widgets_card = StatCard("Widgets", "0", "#6c63ff")
        self._playlists_card = StatCard("Playlists", "0", "#00b894")
        self._alerts_card = StatCard("Alertas Ativos", "0", "#fdcb6e")
        self._items_card = StatCard("Itens na Playlist", "0", "#e17055")

        cards_layout.addWidget(self._widgets_card)
        cards_layout.addWidget(self._playlists_card)
        cards_layout.addWidget(self._alerts_card)
        cards_layout.addWidget(self._items_card)
        layout.addLayout(cards_layout)

        # Status section
        status_group = QGroupBox("Status do Sistema")
        status_group.setStyleSheet("""
            QGroupBox {
                color: #ffffff;
                font-size: 16px;
                font-weight: bold;
                border: 1px solid #2a2a3e;
                border-radius: 12px;
                margin-top: 16px;
                padding: 20px;
                padding-top: 32px;
                background-color: #16213e;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 20px;
                padding: 0 8px;
            }
        """)
        status_layout = QVBoxLayout(status_group)
        status_layout.setSpacing(12)

        self._status_labels: dict[str, QLabel] = {}
        status_items = [
            ("player_status", "Status do Player", "⏹️  Offline"),
            ("current_content", "Conteúdo Atual", "—"),
            ("next_content", "Próximo Conteúdo", "—"),
            ("time_remaining", "Tempo Restante", "—"),
            ("db_status", "Banco de Dados", "✅  Conectado"),
        ]

        for key, label, value in status_items:
            row = QHBoxLayout()
            title = QLabel(label)
            title.setStyleSheet("color: #a0a0b0; font-size: 13px;")
            title.setFixedWidth(180)
            row.addWidget(title)

            value_label = QLabel(value)
            value_label.setStyleSheet("color: #ffffff; font-size: 13px;")
            row.addWidget(value_label)
            row.addStretch()
            status_layout.addLayout(row)
            self._status_labels[key] = value_label

        layout.addWidget(status_group)
        layout.addStretch()

        # Initial data load
        self._refresh_data()

    def _refresh_data(self) -> None:
        """Refresh dashboard data."""
        try:
            with self._db.get_session() as session:
                widget_count = session.query(Widget).count()
                playlist_count = session.query(Playlist).count()
                alert_count = session.query(Alert).filter(Alert.active == True).count()
                total_items = sum(
                    len(p.items) for p in session.query(Playlist).all()
                )

            self._widgets_card.update_value(str(widget_count))
            self._playlists_card.update_value(str(playlist_count))
            self._alerts_card.update_value(str(alert_count))
            self._items_card.update_value(str(total_items))
        except Exception:
            self._status_labels["db_status"].setText("❌  Erro de conexão")