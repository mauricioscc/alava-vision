"""SettingsView - Application settings management."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QDialog, QFormLayout, QLineEdit, QTextEdit, QGroupBox,
    QSpinBox, QComboBox, QCheckBox,
)
from PySide6.QtCore import Qt

from core.database import Database
from core.models.setting import Setting
from core.services.log_service import LogService


class SettingsView(QWidget):
    """Application settings management view."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._db = Database()
        self._log = LogService()
        self._setup_ui()
        self._load_settings()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(16)

        title = QLabel("Configurações")
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)

        # Player settings group
        player_group = QGroupBox("Player")
        player_group.setStyleSheet("""
            QGroupBox { color: #ffffff; font-weight: bold; border: 1px solid #2a2a3e; border-radius: 6px; margin-top: 12px; padding: 16px; padding-top: 24px; }
            QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; }
            QLabel { color: #ffffff; }
            QLineEdit, QSpinBox { color: #ffffff; background-color: #1a1a2e; border: 1px solid #2a2a3e; border-radius: 4px; padding: 6px; }
        """)
        player_layout = QFormLayout(player_group)
        player_layout.setSpacing(8)

        self._monitor_combo = QComboBox()
        self._monitor_combo.addItems(["Automático", "Monitor 1", "Monitor 2", "Monitor 3"])
        player_layout.addRow("Monitor:", self._monitor_combo)

        self._refresh_rate = QSpinBox()
        self._refresh_rate.setRange(1, 60)
        self._refresh_rate.setValue(5)
        self._refresh_rate.setSuffix(" segundos")
        player_layout.addRow("Refresh Playlist:", self._refresh_rate)

        self._fullscreen_check = QCheckBox("Iniciar em fullscreen")
        self._fullscreen_check.setChecked(True)
        player_layout.addRow("", self._fullscreen_check)

        self._hide_cursor_check = QCheckBox("Ocultar cursor do mouse")
        self._hide_cursor_check.setChecked(True)
        player_layout.addRow("", self._hide_cursor_check)

        layout.addWidget(player_group)

        # Server settings group
        server_group = QGroupBox("Servidor (futuro)")
        server_group.setStyleSheet("""
            QGroupBox { color: #ffffff; font-weight: bold; border: 1px solid #2a2a3e; border-radius: 6px; margin-top: 12px; padding: 16px; padding-top: 24px; }
            QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; }
            QLabel { color: #ffffff; }
            QLineEdit, QSpinBox { color: #ffffff; background-color: #1a1a2e; border: 1px solid #2a2a3e; border-radius: 4px; padding: 6px; }
        """)
        server_layout = QFormLayout(server_group)
        server_layout.setSpacing(8)

        self._server_host = QLineEdit()
        self._server_host.setPlaceholderText("localhost")
        server_layout.addRow("Host:", self._server_host)

        self._server_port = QSpinBox()
        self._server_port.setRange(1024, 65535)
        self._server_port.setValue(8000)
        server_layout.addRow("Porta:", self._server_port)

        self._api_key = QLineEdit()
        self._api_key.setPlaceholderText("API Key (opcional)")
        self._api_key.setEchoMode(QLineEdit.Password)
        server_layout.addRow("API Key:", self._api_key)

        layout.addWidget(server_group)

        # Logging settings group
        log_group = QGroupBox("Logs")
        log_group.setStyleSheet("""
            QGroupBox { color: #ffffff; font-weight: bold; border: 1px solid #2a2a3e; border-radius: 6px; margin-top: 12px; padding: 16px; padding-top: 24px; }
            QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; }
            QLabel { color: #ffffff; }
            QComboBox { color: #ffffff; background-color: #1a1a2e; border: 1px solid #2a2a3e; border-radius: 4px; padding: 6px; }
        """)
        log_layout = QFormLayout(log_group)
        log_layout.setSpacing(8)

        self._log_level = QComboBox()
        self._log_level.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        log_layout.addRow("Nível mínimo:", self._log_level)

        self._log_retention = QSpinBox()
        self._log_retention.setRange(1, 365)
        self._log_retention.setValue(30)
        self._log_retention.setSuffix(" dias")
        log_layout.addRow("Retenção:", self._log_retention)

        layout.addWidget(log_group)

        # Save button
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        save_btn = QPushButton("Salvar Configurações")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c63ff; color: white;
                padding: 12px 32px; border-radius: 8px;
                font-weight: bold; font-size: 14px;
            }
            QPushButton:hover { background-color: #5a52e0; }
        """)
        save_btn.clicked.connect(self._save_settings)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

        layout.addStretch()

    def _get_setting(self, key: str, default: str = "") -> str:
        with self._db.get_session() as session:
            setting = session.query(Setting).filter(Setting.key == key).first()
            return setting.value if setting else default

    def _set_setting(self, key: str, value: str, description: str = "") -> None:
        with self._db.get_session() as session:
            setting = session.query(Setting).filter(Setting.key == key).first()
            if setting:
                setting.value = value
            else:
                setting = Setting(key=key, value=value, description=description)
                session.add(setting)
            session.commit()

    def _load_settings(self) -> None:
        self._monitor_combo.setCurrentText(self._get_setting("player_monitor", "Automático"))
        self._refresh_rate.setValue(int(self._get_setting("player_refresh_rate", "5")))
        self._fullscreen_check.setChecked(self._get_setting("player_fullscreen", "true") == "true")
        self._hide_cursor_check.setChecked(self._get_setting("player_hide_cursor", "true") == "true")
        self._server_host.setText(self._get_setting("server_host", "localhost"))
        self._server_port.setValue(int(self._get_setting("server_port", "8000")))
        self._api_key.setText(self._get_setting("server_api_key", ""))
        self._log_level.setCurrentText(self._get_setting("log_level", "INFO"))
        self._log_retention.setValue(int(self._get_setting("log_retention_days", "30")))

    def _save_settings(self) -> None:
        self._set_setting("player_monitor", self._monitor_combo.currentText(), "Monitor para exibição do Player")
        self._set_setting("player_refresh_rate", str(self._refresh_rate.value()), "Intervalo de refresh da playlist (s)")
        self._set_setting("player_fullscreen", "true" if self._fullscreen_check.isChecked() else "false", "Iniciar em fullscreen")
        self._set_setting("player_hide_cursor", "true" if self._hide_cursor_check.isChecked() else "false", "Ocultar cursor")
        self._set_setting("server_host", self._server_host.text().strip(), "Host do servidor")
        self._set_setting("server_port", str(self._server_port.value()), "Porta do servidor")
        self._set_setting("server_api_key", self._api_key.text().strip(), "Chave de API")
        self._set_setting("log_level", self._log_level.currentText(), "Nível mínimo de log")
        self._set_setting("log_retention_days", str(self._log_retention.value()), "Dias de retenção de logs")

        self._log.info("Settings saved", source="admin", category="settings")
        QMessageBox.information(self, "Configurações", "Configurações salvas com sucesso!")