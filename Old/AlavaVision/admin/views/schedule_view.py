"""ScheduleView - Schedule rules management for widgets and alerts."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QDialog, QFormLayout, QLineEdit, QComboBox, QCheckBox,
    QGroupBox, QTimeEdit, QDateEdit, QListWidget, QListWidgetItem,
    QSplitter, QFrame,
)
from PySide6.QtCore import Qt, QTime, QDate

from core.database import Database
from core.models.schedule import ScheduleRule, RuleType
from core.models.widget import Widget
from core.models.alert import Alert
from core.services.log_service import LogService


class ScheduleDialog(QDialog):
    """Dialog for creating/editing schedule rules."""

    def __init__(self, rule_id: int | None = None) -> None:
        super().__init__()
        self._db = Database()
        self._log = LogService()
        self._rule_id = rule_id
        self.setWindowTitle("Nova Regra" if rule_id is None else "Editar Regra")
        self.setMinimumSize(500, 400)
        self._setup_ui()
        if rule_id is not None:
            self._load_rule()

    def _setup_ui(self) -> None:
        self.setStyleSheet("""
            QDialog { background-color: #16213e; }
            QLabel { color: #ffffff; }
            QGroupBox { color: #ffffff; font-weight: bold; border: 1px solid #2a2a3e; border-radius: 6px; margin-top: 12px; padding-top: 16px; }
            QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; }
            QLineEdit, QTimeEdit, QDateEdit { color: #ffffff; background-color: #1a1a2e; border: 1px solid #2a2a3e; border-radius: 4px; padding: 8px; }
            QComboBox { color: #ffffff; background-color: #1a1a2e; border: 1px solid #2a2a3e; border-radius: 4px; padding: 6px; }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView { color: #ffffff; background-color: #1a1a2e; selection-background-color: #3a3a5e; }
            QCheckBox { color: #ffffff; }
        """)
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        form = QFormLayout()
        form.setSpacing(8)

        # Target: Widget or Alert
        self._target_combo = QComboBox()
        self._target_combo.addItems(["Widget", "Alerta"])
        self._target_combo.currentIndexChanged.connect(self._on_target_changed)
        form.addRow("Aplicar a:", self._target_combo)

        self._item_combo = QComboBox()
        form.addRow("Item:", self._item_combo)

        # Rule type
        self._rule_type_combo = QComboBox()
        self._rule_type_combo.addItems([
            "time_range", "day_of_week", "date_range",
            "specific_date", "specific_day"
        ])
        self._rule_type_combo.currentIndexChanged.connect(self._on_rule_type_changed)
        form.addRow("Tipo de Regra:", self._rule_type_combo)

        layout.addLayout(form)

        # Config group
        config_group = QGroupBox("Configuração")
        config_layout = QFormLayout(config_group)
        config_layout.setSpacing(8)

        # Time range
        self._time_group = QWidget()
        time_layout = QHBoxLayout(self._time_group)
        time_layout.setContentsMargins(0, 0, 0, 0)
        self._start_time = QTimeEdit(QTime(8, 0))
        self._start_time.setDisplayFormat("HH:mm")
        time_layout.addWidget(QLabel("De:"))
        time_layout.addWidget(self._start_time)
        self._end_time = QTimeEdit(QTime(18, 0))
        self._end_time.setDisplayFormat("HH:mm")
        time_layout.addWidget(QLabel("Até:"))
        time_layout.addWidget(self._end_time)
        config_layout.addRow("Horário:", self._time_group)

        # Days of week
        self._days_group = QWidget()
        days_layout = QHBoxLayout(self._days_group)
        days_layout.setContentsMargins(0, 0, 0, 0)
        self._day_checks = {}
        for day in ["seg", "ter", "qua", "qui", "sex", "sab", "dom"]:
            cb = QCheckBox(day)
            self._day_checks[day] = cb
            days_layout.addWidget(cb)
        config_layout.addRow("Dias:", self._days_group)

        # Date range
        self._date_group = QWidget()
        date_layout = QHBoxLayout(self._date_group)
        date_layout.setContentsMargins(0, 0, 0, 0)
        self._start_date = QDateEdit(QDate.currentDate())
        self._start_date.setDisplayFormat("dd/MM/yyyy")
        date_layout.addWidget(QLabel("De:"))
        date_layout.addWidget(self._start_date)
        self._end_date = QDateEdit(QDate.currentDate().addDays(30))
        self._end_date.setDisplayFormat("dd/MM/yyyy")
        date_layout.addWidget(QLabel("Até:"))
        date_layout.addWidget(self._end_date)
        config_layout.addRow("Período:", self._date_group)

        self._active_check = QCheckBox("Ativo")
        self._active_check.setChecked(True)
        config_layout.addRow("", self._active_check)

        layout.addWidget(config_group)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Salvar Regra")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c63ff; color: white;
                padding: 10px 28px; border-radius: 6px;
                font-weight: bold; font-size: 13px;
            }
            QPushButton:hover { background-color: #5a52e0; }
        """)
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

        # Initial state
        self._on_rule_type_changed(0)
        self._on_target_changed(0)
        self._refresh_items()

    def _on_target_changed(self, idx: int) -> None:
        self._refresh_items()

    def _refresh_items(self) -> None:
        self._item_combo.clear()
        with self._db.get_session() as session:
            if self._target_combo.currentIndex() == 0:  # Widget
                items = session.query(Widget).filter(Widget.active == True).all()
                for item in items:
                    self._item_combo.addItem(f"{item.name} ({item.widget_type.value})", ("widget", item.id))
            else:  # Alert
                items = session.query(Alert).filter(Alert.active == True).all()
                for item in items:
                    self._item_combo.addItem(item.title or item.message[:30], ("alert", item.id))

    def _on_rule_type_changed(self, idx: int) -> None:
        rule_type = self._rule_type_combo.currentText()
        self._time_group.setVisible(rule_type == "time_range")
        self._days_group.setVisible(rule_type in ("day_of_week", "specific_day"))
        self._date_group.setVisible(rule_type in ("date_range", "specific_date"))

    def _load_rule(self) -> None:
        with self._db.get_session() as session:
            rule = session.query(ScheduleRule).filter(ScheduleRule.id == self._rule_id).first()
            if not rule:
                return
            idx = self._rule_type_combo.findText(rule.rule_type.value)
            if idx >= 0:
                self._rule_type_combo.setCurrentIndex(idx)
            if rule.start_time:
                self._start_time.setTime(QTime.fromString(rule.start_time, "HH:mm"))
            if rule.end_time:
                self._end_time.setTime(QTime.fromString(rule.end_time, "HH:mm"))
            if rule.days_of_week:
                day_map = {"mon": "seg", "tue": "ter", "wed": "qua", "thu": "qui",
                          "fri": "sex", "sat": "sab", "sun": "dom"}
                for day in rule.days_of_week.split(","):
                    pt_day = day_map.get(day.strip(), day.strip())
                    if pt_day in self._day_checks:
                        self._day_checks[pt_day].setChecked(True)
            if rule.start_date:
                self._start_date.setDate(QDate.fromString(rule.start_date, "yyyy-MM-dd"))
            if rule.end_date:
                self._end_date.setDate(QDate.fromString(rule.end_date, "yyyy-MM-dd"))
            self._active_check.setChecked(rule.active)

            # Set target
            if rule.widget_id:
                self._target_combo.setCurrentIndex(0)
            elif rule.alert_id:
                self._target_combo.setCurrentIndex(1)

    def _save(self) -> None:
        rule_type = self._rule_type_combo.currentText()
        target_data = self._item_combo.currentData()
        if not target_data:
            QMessageBox.warning(self, "Validação", "Selecione um item.")
            return

        target_type, target_id = target_data
        start_time = None
        end_time = None
        days_of_week = None
        start_date = None
        end_date = None

        if rule_type == "time_range":
            start_time = self._start_time.time().toString("HH:mm")
            end_time = self._end_time.time().toString("HH:mm")
        elif rule_type in ("day_of_week", "specific_day"):
            rev_map = {"seg": "mon", "ter": "tue", "qua": "wed", "qui": "thu",
                      "sex": "fri", "sab": "sat", "dom": "sun"}
            days = []
            for pt_day, cb in self._day_checks.items():
                if cb.isChecked():
                    days.append(rev_map[pt_day])
            days_of_week = ",".join(days) if days else None
        elif rule_type in ("date_range", "specific_date"):
            start_date = self._start_date.date().toString("yyyy-MM-dd")
            end_date = self._end_date.date().toString("yyyy-MM-dd")

        with self._db.get_session() as session:
            if self._rule_id:
                rule = session.query(ScheduleRule).filter(ScheduleRule.id == self._rule_id).first()
                if not rule:
                    return
            else:
                rule = ScheduleRule()
                session.add(rule)

            rule.rule_type = RuleType(rule_type)
            rule.active = self._active_check.isChecked()
            rule.start_time = start_time
            rule.end_time = end_time
            rule.days_of_week = days_of_week
            rule.start_date = start_date
            rule.end_date = end_date

            if target_type == "widget":
                rule.widget_id = target_id
                rule.alert_id = None
            else:
                rule.alert_id = target_id
                rule.widget_id = None

            session.commit()

        self._log.info(
            f"Schedule rule {'updated' if self._rule_id else 'created'}: {rule_type}",
            source="admin", category="schedule",
        )
        self.accept()


class ScheduleView(QWidget):
    """Schedule rules management view."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._db = Database()
        self._setup_ui()
        self._refresh_table()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(16)

        header_layout = QHBoxLayout()
        title = QLabel("Agendamentos")
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #ffffff;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        add_btn = QPushButton("+ Nova Regra")
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c63ff; color: white;
                padding: 10px 20px; border-radius: 8px;
                font-weight: bold; font-size: 13px;
            }
            QPushButton:hover { background-color: #5a52e0; }
        """)
        add_btn.clicked.connect(self._add_rule)
        header_layout.addWidget(add_btn)
        layout.addLayout(header_layout)

        self._table = QTableWidget()
        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels([
            "ID", "Tipo", "Item", "Configuração", "Ativo", "Ações"
        ])
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.verticalHeader().setDefaultSectionSize(48)
        self._table.setStyleSheet("""
            QTableWidget {
                background-color: #16213e; color: #ffffff;
                border: 1px solid #2a2a3e; border-radius: 8px;
                gridline-color: #2a2a3e;
            }
            QTableWidget::item { padding: 8px; }
            QHeaderView::section {
                background-color: #1a1a2e; color: #a0a0b0;
                padding: 10px; border: none; font-weight: bold;
            }
        """)
        layout.addWidget(self._table)

    def _refresh_table(self) -> None:
        with self._db.get_session() as session:
            rules = session.query(ScheduleRule).order_by(ScheduleRule.id).all()
            self._table.setRowCount(len(rules))

            for row, rule in enumerate(rules):
                self._table.setItem(row, 0, QTableWidgetItem(str(rule.id)))
                self._table.setItem(row, 1, QTableWidgetItem(rule.rule_type.value))

                # Get item name
                item_name = "-"
                if rule.widget_id:
                    w = session.query(Widget).filter(Widget.id == rule.widget_id).first()
                    if w:
                        item_name = f"Widget: {w.name}"
                elif rule.alert_id:
                    a = session.query(Alert).filter(Alert.id == rule.alert_id).first()
                    if a:
                        item_name = f"Alerta: {a.title or a.message[:20]}"
                self._table.setItem(row, 2, QTableWidgetItem(item_name))

                # Config description
                config_parts = []
                if rule.start_time and rule.end_time:
                    config_parts.append(f"{rule.start_time}-{rule.end_time}")
                if rule.days_of_week:
                    config_parts.append(rule.days_of_week)
                if rule.start_date and rule.end_date:
                    config_parts.append(f"{rule.start_date} a {rule.end_date}")
                self._table.setItem(row, 3, QTableWidgetItem(", ".join(config_parts) or "-"))
                self._table.setItem(row, 4, QTableWidgetItem("✅" if rule.active else "❌"))

                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(4, 2, 4, 2)
                actions_layout.setSpacing(4)

                edit_btn = QPushButton("✏️")
                edit_btn.setFixedSize(32, 28)
                edit_btn.clicked.connect(lambda checked=False, rid=rule.id: self._edit_rule(rid))
                actions_layout.addWidget(edit_btn)

                delete_btn = QPushButton("🗑️")
                delete_btn.setFixedSize(32, 28)
                delete_btn.clicked.connect(lambda checked=False, rid=rule.id: self._delete_rule(rid))
                actions_layout.addWidget(delete_btn)

                self._table.setCellWidget(row, 5, actions_widget)

    def _add_rule(self) -> None:
        dialog = ScheduleDialog()
        if dialog.exec():
            self._refresh_table()

    def _edit_rule(self, rule_id: int) -> None:
        dialog = ScheduleDialog(rule_id)
        if dialog.exec():
            self._refresh_table()

    def _delete_rule(self, rule_id: int) -> None:
        reply = QMessageBox.question(
            self, "Confirmar", "Excluir esta regra?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            with self._db.get_session() as session:
                rule = session.query(ScheduleRule).filter(ScheduleRule.id == rule_id).first()
                if rule:
                    session.delete(rule)
                    session.commit()
            self._refresh_table()