"""AlertView - CRUD interface for managing alerts."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QDialog, QFormLayout, QLineEdit, QComboBox, QSpinBox,
    QTextEdit, QCheckBox, QGroupBox, QColorDialog,
)
from PySide6.QtCore import Qt

from admin.controllers.alert_controller import AlertController
from core.schemas.alert_schema import AlertCreate, AlertUpdate


class AlertDialog(QDialog):
    """Dialog for creating/editing alerts."""

    def __init__(self, controller: AlertController, alert_id: int | None = None) -> None:
        super().__init__()
        self._controller = controller
        self._alert_id = alert_id
        self.setWindowTitle("Novo Alerta" if alert_id is None else "Editar Alerta")
        self.setMinimumSize(550, 500)
        self._setup_ui()
        if alert_id is not None:
            self._load_alert()

    def _setup_ui(self) -> None:
        """Setup the dialog UI."""
        self.setStyleSheet("""
            QDialog { background-color: #16213e; }
            QLabel { color: #ffffff; }
            QGroupBox { color: #ffffff; font-weight: bold; border: 1px solid #2a2a3e; border-radius: 6px; margin-top: 12px; padding-top: 16px; }
            QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; }
            QLineEdit, QTextEdit { color: #ffffff; background-color: #1a1a2e; border: 1px solid #2a2a3e; border-radius: 4px; padding: 8px; }
            QComboBox { color: #ffffff; background-color: #1a1a2e; border: 1px solid #2a2a3e; border-radius: 4px; padding: 6px; }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView { color: #ffffff; background-color: #1a1a2e; selection-background-color: #3a3a5e; }
            QSpinBox { color: #ffffff; background-color: #1a1a2e; border: 1px solid #2a2a3e; border-radius: 4px; padding: 6px; }
            QCheckBox { color: #ffffff; }
        """)
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Title and message
        form = QFormLayout()
        form.setSpacing(8)

        self._title_input = QLineEdit()
        self._title_input.setPlaceholderText("Título do alerta (opcional)")
        form.addRow("Título:", self._title_input)

        self._message_input = QTextEdit()
        self._message_input.setPlaceholderText("Mensagem do alerta...")
        self._message_input.setMaximumHeight(80)
        form.addRow("Mensagem:", self._message_input)

        layout.addLayout(form)

        # Alert type config
        config_group = QGroupBox("Configuração do Alerta")
        config_layout = QFormLayout(config_group)
        config_layout.setSpacing(8)

        self._type_combo = QComboBox()
        self._type_combo.addItems([
            "overlay_center", "banner_top", "banner_bottom",
            "fullscreen", "toast", "ticker"
        ])
        config_layout.addRow("Tipo:", self._type_combo)

        self._position_combo = QComboBox()
        self._position_combo.addItems(["center", "top_left", "top_right", "bottom_left", "bottom_right"])
        config_layout.addRow("Posição:", self._position_combo)

        self._animation_combo = QComboBox()
        self._animation_combo.addItems(["fade", "slide", "zoom", "none"])
        config_layout.addRow("Animação:", self._animation_combo)

        # Colors
        color_layout = QHBoxLayout()
        self._bg_color_btn = QPushButton("#333333")
        self._bg_color_btn.setStyleSheet("background-color: #333333; border: 1px solid #555; padding: 6px; border-radius: 4px; color: white;")
        self._bg_color_btn.clicked.connect(lambda: self._pick_color(self._bg_color_btn))
        color_layout.addWidget(self._bg_color_btn)

        self._text_color_btn = QPushButton("#FFFFFF")
        self._text_color_btn.setStyleSheet("background-color: #FFFFFF; border: 1px solid #555; padding: 6px; border-radius: 4px;")
        self._text_color_btn.clicked.connect(lambda: self._pick_color(self._text_color_btn))
        color_layout.addWidget(self._text_color_btn)
        config_layout.addRow("Fundo/Texto:", color_layout)

        # Duration and priority
        dur_prio_layout = QHBoxLayout()
        self._duration_spin = QSpinBox()
        self._duration_spin.setRange(1, 3600)
        self._duration_spin.setValue(10)
        self._duration_spin.setSuffix(" segundos")
        dur_prio_layout.addWidget(self._duration_spin)

        self._priority_spin = QSpinBox()
        self._priority_spin.setRange(1, 1000)
        self._priority_spin.setValue(10)
        self._priority_spin.setPrefix("Prioridade: ")
        dur_prio_layout.addWidget(self._priority_spin)
        config_layout.addRow("Duração:", dur_prio_layout)

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

        save_btn = QPushButton("Salvar Alerta")
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

    def _pick_color(self, button: QPushButton) -> None:
        color = QColorDialog.getColor()
        if color.isValid():
            button.setText(color.name())
            button.setStyleSheet(
                f"background-color: {color.name()}; border: 1px solid #555; "
                f"padding: 6px; border-radius: 4px; "
                f"color: {'white' if color.lightness() < 128 else 'black'};"
            )

    def _load_alert(self) -> None:
        alert = self._controller.get_by_id(self._alert_id)
        if not alert:
            return
        self._title_input.setText(alert.title or "")
        self._message_input.setPlainText(alert.message)
        idx = self._type_combo.findText(alert.alert_type.value)
        if idx >= 0:
            self._type_combo.setCurrentIndex(idx)
        idx = self._position_combo.findText(alert.position.value)
        if idx >= 0:
            self._position_combo.setCurrentIndex(idx)
        idx = self._animation_combo.findText(alert.animation.value)
        if idx >= 0:
            self._animation_combo.setCurrentIndex(idx)
        self._bg_color_btn.setText(alert.background_color or "#333333")
        self._text_color_btn.setText(alert.text_color or "#FFFFFF")
        self._duration_spin.setValue(alert.duration)
        self._priority_spin.setValue(alert.priority)
        self._active_check.setChecked(alert.active)

    def _save(self) -> None:
        message = self._message_input.toPlainText().strip()
        if not message:
            QMessageBox.warning(self, "Validação", "Mensagem é obrigatória.")
            return

        if self._alert_id is None:
            data = AlertCreate(
                title=self._title_input.text().strip() or None,
                message=message,
                alert_type=self._type_combo.currentText(),
                position=self._position_combo.currentText(),
                animation=self._animation_combo.currentText(),
                background_color=self._bg_color_btn.text(),
                text_color=self._text_color_btn.text(),
                duration=self._duration_spin.value(),
                priority=self._priority_spin.value(),
                active=self._active_check.isChecked(),
            )
            self._controller.create(data)
        else:
            data = AlertUpdate(
                title=self._title_input.text().strip() or None,
                message=message,
                alert_type=self._type_combo.currentText(),
                position=self._position_combo.currentText(),
                animation=self._animation_combo.currentText(),
                background_color=self._bg_color_btn.text(),
                text_color=self._text_color_btn.text(),
                duration=self._duration_spin.value(),
                priority=self._priority_spin.value(),
                active=self._active_check.isChecked(),
            )
            self._controller.update(self._alert_id, data)
        self.accept()


class AlertView(QWidget):
    """Alert management view."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._controller = AlertController()
        self._setup_ui()
        self._refresh_table()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()
        title = QLabel("Alertas")
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #ffffff;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        add_btn = QPushButton("+ Novo Alerta")
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c63ff; color: white;
                padding: 10px 20px; border-radius: 8px;
                font-weight: bold; font-size: 13px;
            }
            QPushButton:hover { background-color: #5a52e0; }
        """)
        add_btn.clicked.connect(self._add_alert)
        header_layout.addWidget(add_btn)
        layout.addLayout(header_layout)

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(7)
        self._table.setHorizontalHeaderLabels([
            "ID", "Título", "Tipo", "Duração", "Prioridade", "Ativo", "Ações"
        ])
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
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
        alerts = self._controller.get_all()
        self._table.setRowCount(len(alerts))

        for row, alert in enumerate(alerts):
            self._table.setItem(row, 0, QTableWidgetItem(str(alert.id)))
            self._table.setItem(row, 1, QTableWidgetItem(alert.title or alert.message[:40]))
            self._table.setItem(row, 2, QTableWidgetItem(alert.alert_type.value))
            self._table.setItem(row, 3, QTableWidgetItem(f"{alert.duration}s"))
            self._table.setItem(row, 4, QTableWidgetItem(str(alert.priority)))
            self._table.setItem(row, 5, QTableWidgetItem("✅" if alert.active else "❌"))

            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 2, 4, 2)
            actions_layout.setSpacing(4)

            edit_btn = QPushButton("✏️")
            edit_btn.setFixedSize(32, 28)
            edit_btn.clicked.connect(lambda checked=False, aid=alert.id: self._edit_alert(aid))
            actions_layout.addWidget(edit_btn)

            delete_btn = QPushButton("🗑️")
            delete_btn.setFixedSize(32, 28)
            delete_btn.clicked.connect(lambda checked=False, aid=alert.id: self._delete_alert(aid))
            actions_layout.addWidget(delete_btn)

            self._table.setCellWidget(row, 6, actions_widget)

    def _add_alert(self) -> None:
        dialog = AlertDialog(self._controller)
        if dialog.exec():
            self._refresh_table()

    def _edit_alert(self, alert_id: int) -> None:
        dialog = AlertDialog(self._controller, alert_id)
        if dialog.exec():
            self._refresh_table()

    def _delete_alert(self, alert_id: int) -> None:
        reply = QMessageBox.question(
            self, "Confirmar", "Excluir este alerta?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self._controller.delete(alert_id)
            self._refresh_table()