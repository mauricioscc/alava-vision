"""LogView - System log viewer with filtering."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QLineEdit, QDateEdit, QGroupBox,
)
from PySide6.QtCore import Qt, QDate

from core.database import Database
from core.models.log import Log


class LogView(QWidget):
    """System log viewer with filtering."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._db = Database()
        self._setup_ui()
        self._refresh_logs()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(16)

        # Header
        title = QLabel("Logs do Sistema")
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)

        # Filters
        filter_group = QGroupBox("Filtros")
        filter_group.setStyleSheet("""
            QGroupBox { color: #ffffff; font-weight: bold; border: 1px solid #2a2a3e; border-radius: 6px; margin-top: 12px; padding: 12px; padding-top: 20px; }
            QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; }
            QLabel { color: #ffffff; }
            QComboBox, QLineEdit, QDateEdit { color: #ffffff; background-color: #1a1a2e; border: 1px solid #2a2a3e; border-radius: 4px; padding: 6px; }
        """)
        filter_layout = QHBoxLayout(filter_group)
        filter_layout.setSpacing(12)

        self._level_filter = QComboBox()
        self._level_filter.addItems(["Todos", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self._level_filter.currentIndexChanged.connect(self._refresh_logs)
        filter_layout.addWidget(QLabel("Nível:"))
        filter_layout.addWidget(self._level_filter)

        self._source_filter = QComboBox()
        self._source_filter.addItems(["Todos", "admin", "player", "server", "system", "test"])
        self._source_filter.currentIndexChanged.connect(self._refresh_logs)
        filter_layout.addWidget(QLabel("Origem:"))
        filter_layout.addWidget(self._source_filter)

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Buscar mensagem...")
        self._search_input.textChanged.connect(self._refresh_logs)
        filter_layout.addWidget(self._search_input)

        refresh_btn = QPushButton("🔄 Atualizar")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #3a3a5e; color: white;
                padding: 8px 16px; border-radius: 4px;
            }
            QPushButton:hover { background-color: #4a4a6e; }
        """)
        refresh_btn.clicked.connect(self._refresh_logs)
        filter_layout.addWidget(refresh_btn)

        clear_btn = QPushButton("🗑️ Limpar")
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #e17055; color: white;
                padding: 8px 16px; border-radius: 4px;
            }
            QPushButton:hover { background-color: #d63031; }
        """)
        clear_btn.clicked.connect(self._clear_logs)
        filter_layout.addWidget(clear_btn)

        layout.addWidget(filter_group)

        # Log table
        self._table = QTableWidget()
        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels([
            "Data/Hora", "Nível", "Origem", "Categoria", "Mensagem", "Detalhes"
        ])
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setDefaultSectionSize(32)
        self._table.setStyleSheet("""
            QTableWidget {
                background-color: #16213e; color: #ffffff;
                border: 1px solid #2a2a3e; border-radius: 8px;
                gridline-color: #2a2a3e;
            }
            QTableWidget::item { padding: 6px; }
            QHeaderView::section {
                background-color: #1a1a2e; color: #a0a0b0;
                padding: 8px; border: none; font-weight: bold;
            }
        """)
        layout.addWidget(self._table)

    def _refresh_logs(self) -> None:
        """Refresh logs with current filters."""
        level = self._level_filter.currentText()
        source = self._source_filter.currentText()
        search = self._search_input.text().strip().lower()

        with self._db.get_session() as session:
            query = session.query(Log).order_by(Log.timestamp.desc())

            if level != "Todos":
                query = query.filter(Log.level == level)
            if source != "Todos":
                query = query.filter(Log.source == source)

            logs = query.limit(500).all()

            # Apply search filter in Python (case-insensitive)
            if search:
                logs = [l for l in logs if search in l.message.lower()]

            self._table.setRowCount(len(logs))

            for row, log in enumerate(logs):
                timestamp = log.timestamp.strftime("%d/%m/%Y %H:%M:%S")
                self._table.setItem(row, 0, QTableWidgetItem(timestamp))
                self._table.setItem(row, 1, QTableWidgetItem(log.level))
                self._table.setItem(row, 2, QTableWidgetItem(log.source))
                self._table.setItem(row, 3, QTableWidgetItem(log.category))
                self._table.setItem(row, 4, QTableWidgetItem(log.message[:100]))
                self._table.setItem(row, 5, QTableWidgetItem(log.details[:50] if log.details else ""))

                # Color code by level
                color_map = {
                    "ERROR": "#e17055",
                    "WARNING": "#fdcb6e",
                    "INFO": "#81ecec",
                    "DEBUG": "#a0a0b0",
                    "CRITICAL": "#d63031",
                }
                color = color_map.get(log.level, "#ffffff")
                self._table.item(row, 1).setForeground(Qt.GlobalColor.white)
                self._table.item(row, 1).setBackground(Qt.GlobalColor.darkGray)

    def _clear_logs(self) -> None:
        """Clear all logs after confirmation."""
        from PySide6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self, "Confirmar", "Limpar todos os logs?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            with self._db.get_session() as session:
                session.query(Log).delete()
                session.commit()
            self._refresh_logs()