"""BrowserProfileView - CRUD interface for browser profiles."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QDialog, QFormLayout, QLineEdit, QCheckBox, QDoubleSpinBox,
    QTextEdit, QGroupBox, QFileDialog,
)
from PySide6.QtCore import Qt

from admin.controllers.browser_profile_controller import BrowserProfileController
from core.schemas.browser_profile_schema import BrowserProfileCreate, BrowserProfileUpdate


class BrowserProfileDialog(QDialog):
    """Dialog for creating/editing browser profiles."""

    def __init__(self, controller: BrowserProfileController, profile_id: int | None = None) -> None:
        super().__init__()
        self._controller = controller
        self._profile_id = profile_id
        self.setWindowTitle("Novo Perfil" if profile_id is None else "Editar Perfil")
        self.setMinimumSize(500, 400)
        self._setup_ui()
        if profile_id is not None:
            self._load_profile()

    def _setup_ui(self) -> None:
        self.setStyleSheet("""
            QDialog { background-color: #16213e; }
            QLabel { color: #ffffff; }
            QGroupBox { color: #ffffff; font-weight: bold; border: 1px solid #2a2a3e; border-radius: 6px; margin-top: 12px; padding-top: 16px; }
            QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; }
            QLineEdit, QTextEdit { color: #ffffff; background-color: #1a1a2e; border: 1px solid #2a2a3e; border-radius: 4px; padding: 8px; }
            QDoubleSpinBox { color: #ffffff; background-color: #1a1a2e; border: 1px solid #2a2a3e; border-radius: 4px; padding: 6px; }
            QCheckBox { color: #ffffff; }
        """)
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        form = QFormLayout()
        form.setSpacing(8)

        self._name_input = QLineEdit()
        self._name_input.setPlaceholderText("Ex: dashboard_comercial")
        form.addRow("Nome:", self._name_input)

        # Profile path with browse
        path_layout = QHBoxLayout()
        self._path_input = QLineEdit()
        self._path_input.setPlaceholderText("Caminho da pasta do perfil...")
        path_layout.addWidget(self._path_input)
        browse_btn = QPushButton("Procurar...")
        browse_btn.setStyleSheet("""
            QPushButton { background-color: #3a3a5e; color: white; padding: 6px 16px; border-radius: 4px; }
            QPushButton:hover { background-color: #4a4a6e; }
        """)
        browse_btn.clicked.connect(self._browse_folder)
        path_layout.addWidget(browse_btn)
        form.addRow("Pasta do Perfil:", path_layout)

        layout.addLayout(form)

        # Options group
        options_group = QGroupBox("Opções do Navegador")
        options_layout = QFormLayout(options_group)
        options_layout.setSpacing(8)

        self._js_check = QCheckBox("JavaScript habilitado")
        self._js_check.setChecked(True)
        options_layout.addRow("", self._js_check)

        self._cookies_check = QCheckBox("Cookies habilitados")
        self._cookies_check.setChecked(True)
        options_layout.addRow("", self._cookies_check)

        self._zoom_spin = QDoubleSpinBox()
        self._zoom_spin.setRange(0.1, 5.0)
        self._zoom_spin.setValue(1.0)
        self._zoom_spin.setSingleStep(0.1)
        options_layout.addRow("Zoom:", self._zoom_spin)

        self._user_agent = QLineEdit()
        self._user_agent.setPlaceholderText("User-Agent personalizado (opcional)")
        options_layout.addRow("User-Agent:", self._user_agent)

        self._extra_args = QTextEdit()
        self._extra_args.setPlaceholderText("Argumentos extras (JSON, opcional)")
        self._extra_args.setMaximumHeight(60)
        options_layout.addRow("Args Extras:", self._extra_args)

        self._active_check = QCheckBox("Ativo")
        self._active_check.setChecked(True)
        options_layout.addRow("", self._active_check)

        layout.addWidget(options_group)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Salvar Perfil")
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

    def _browse_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Selecionar Pasta do Perfil")
        if folder:
            self._path_input.setText(folder)

    def _load_profile(self) -> None:
        profile = self._controller.get_by_id(self._profile_id)
        if not profile:
            return
        self._name_input.setText(profile.name)
        self._path_input.setText(profile.profile_path)
        self._js_check.setChecked(profile.javascript_enabled)
        self._cookies_check.setChecked(profile.cookies_enabled)
        self._zoom_spin.setValue(profile.zoom_factor)
        self._user_agent.setText(profile.user_agent or "")
        self._extra_args.setPlainText(profile.extra_args or "")
        self._active_check.setChecked(profile.active)

    def _save(self) -> None:
        name = self._name_input.text().strip()
        path = self._path_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Validação", "Nome é obrigatório.")
            return
        if not path:
            QMessageBox.warning(self, "Validação", "Caminho do perfil é obrigatório.")
            return

        if self._profile_id is None:
            data = BrowserProfileCreate(
                name=name,
                profile_path=path,
                user_agent=self._user_agent.text().strip() or None,
                javascript_enabled=self._js_check.isChecked(),
                cookies_enabled=self._cookies_check.isChecked(),
                zoom_factor=self._zoom_spin.value(),
                extra_args=self._extra_args.toPlainText().strip() or None,
                active=self._active_check.isChecked(),
            )
            self._controller.create(data)
        else:
            data = BrowserProfileUpdate(
                name=name,
                profile_path=path,
                user_agent=self._user_agent.text().strip() or None,
                javascript_enabled=self._js_check.isChecked(),
                cookies_enabled=self._cookies_check.isChecked(),
                zoom_factor=self._zoom_spin.value(),
                extra_args=self._extra_args.toPlainText().strip() or None,
                active=self._active_check.isChecked(),
            )
            self._controller.update(self._profile_id, data)
        self.accept()


class BrowserProfileView(QWidget):
    """Browser profile management view."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._controller = BrowserProfileController()
        self._setup_ui()
        self._refresh_table()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(16)

        header_layout = QHBoxLayout()
        title = QLabel("Perfis de Navegador")
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #ffffff;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        add_btn = QPushButton("+ Novo Perfil")
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c63ff; color: white;
                padding: 10px 20px; border-radius: 8px;
                font-weight: bold; font-size: 13px;
            }
            QPushButton:hover { background-color: #5a52e0; }
        """)
        add_btn.clicked.connect(self._add_profile)
        header_layout.addWidget(add_btn)
        layout.addLayout(header_layout)

        self._table = QTableWidget()
        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels([
            "ID", "Nome", "JavaScript", "Cookies", "Zoom", "Ações"
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
        profiles = self._controller.get_all()
        self._table.setRowCount(len(profiles))

        for row, profile in enumerate(profiles):
            self._table.setItem(row, 0, QTableWidgetItem(str(profile.id)))
            self._table.setItem(row, 1, QTableWidgetItem(profile.name))
            self._table.setItem(row, 2, QTableWidgetItem("✅" if profile.javascript_enabled else "❌"))
            self._table.setItem(row, 3, QTableWidgetItem("✅" if profile.cookies_enabled else "❌"))
            self._table.setItem(row, 4, QTableWidgetItem(f"{profile.zoom_factor:.1f}x"))

            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 2, 4, 2)
            actions_layout.setSpacing(4)

            edit_btn = QPushButton("✏️")
            edit_btn.setFixedSize(32, 28)
            edit_btn.clicked.connect(lambda checked=False, pid=profile.id: self._edit_profile(pid))
            actions_layout.addWidget(edit_btn)

            delete_btn = QPushButton("🗑️")
            delete_btn.setFixedSize(32, 28)
            delete_btn.clicked.connect(lambda checked=False, pid=profile.id: self._delete_profile(pid))
            actions_layout.addWidget(delete_btn)

            self._table.setCellWidget(row, 5, actions_widget)

    def _add_profile(self) -> None:
        dialog = BrowserProfileDialog(self._controller)
        if dialog.exec():
            self._refresh_table()

    def _edit_profile(self, profile_id: int) -> None:
        dialog = BrowserProfileDialog(self._controller, profile_id)
        if dialog.exec():
            self._refresh_table()

    def _delete_profile(self, profile_id: int) -> None:
        reply = QMessageBox.question(
            self, "Confirmar", "Excluir este perfil?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self._controller.delete(profile_id)
            self._refresh_table()