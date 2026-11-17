"""PlaylistView - CRUD interface for managing playlists."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QDialog, QFormLayout, QLineEdit, QTextEdit, QCheckBox,
    QListWidget, QListWidgetItem, QComboBox, QSpinBox,
    QSplitter, QFrame, QGroupBox,
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QFont

from admin.controllers.playlist_controller import PlaylistController
from admin.controllers.widget_controller import WidgetController
from core.schemas.playlist_schema import PlaylistCreate, PlaylistUpdate, PlaylistItemCreate


class PlaylistDialog(QDialog):
    """Dialog for creating/editing playlists."""

    def __init__(self, controller: PlaylistController, playlist_id: int | None = None) -> None:
        super().__init__()
        self._controller = controller
        self._playlist_id = playlist_id
        self.setWindowTitle("Nova Playlist" if playlist_id is None else "Editar Playlist")
        self.setMinimumSize(450, 300)
        self._setup_ui()
        if playlist_id is not None:
            self._load_playlist()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        form = QFormLayout()
        form.setSpacing(12)

        self._name_input = QLineEdit()
        self._name_input.setPlaceholderText("Nome da playlist")
        form.addRow("Nome:", self._name_input)

        self._desc_input = QTextEdit()
        self._desc_input.setMaximumHeight(80)
        self._desc_input.setPlaceholderText("Descrição (opcional)")
        form.addRow("Descrição:", self._desc_input)

        self._loop_check = QCheckBox("Repetir automaticamente")
        self._loop_check.setChecked(True)
        form.addRow("", self._loop_check)

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Salvar")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c63ff; color: white;
                padding: 8px 24px; border-radius: 6px; font-weight: bold;
            }
            QPushButton:hover { background-color: #5a52e0; }
        """)
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

    def _load_playlist(self) -> None:
        playlist = self._controller.get_by_id(self._playlist_id)
        if not playlist:
            return
        self._name_input.setText(playlist.name)
        self._desc_input.setPlainText(playlist.description or "")
        self._loop_check.setChecked(playlist.loop)

    def _save(self) -> None:
        name = self._name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Validação", "Nome é obrigatório.")
            return

        if self._playlist_id is None:
            data = PlaylistCreate(
                name=name,
                description=self._desc_input.toPlainText().strip() or None,
                loop=self._loop_check.isChecked(),
            )
            self._controller.create(data)
        else:
            data = PlaylistUpdate(
                name=name,
                description=self._desc_input.toPlainText().strip() or None,
                loop=self._loop_check.isChecked(),
            )
            self._controller.update(self._playlist_id, data)
        self.accept()


class PlaylistView(QWidget):
    """Playlist management view."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._controller = PlaylistController()
        self._widget_controller = WidgetController()
        self._current_playlist_id: int | None = None
        self._setup_ui()
        self._refresh_playlists()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(16)

        # Header
        header = QLabel("Playlists")
        header.setStyleSheet("font-size: 28px; font-weight: bold; color: #ffffff;")
        layout.addWidget(header)

        # Splitter: playlist list on left, items on right
        splitter = QSplitter(Qt.Horizontal)

        # Left panel - playlist list
        left_panel = QFrame()
        left_panel.setStyleSheet("background-color: #16213e; border-radius: 8px;")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(16, 16, 16, 16)

        left_header = QHBoxLayout()
        left_title = QLabel("Playlists")
        left_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #ffffff;")
        left_header.addWidget(left_title)
        left_header.addStretch()

        add_playlist_btn = QPushButton("+")
        add_playlist_btn.setFixedSize(32, 32)
        add_playlist_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c63ff; color: white;
                border-radius: 16px; font-size: 18px; font-weight: bold;
            }
            QPushButton:hover { background-color: #5a52e0; }
        """)
        add_playlist_btn.clicked.connect(self._add_playlist)
        left_header.addWidget(add_playlist_btn)
        left_layout.addLayout(left_header)

        self._playlist_list = QListWidget()
        self._playlist_list.setStyleSheet("""
            QListWidget {
                background-color: #1a1a2e;
                border: 1px solid #2a2a3e;
                border-radius: 6px;
                color: #ffffff;
            }
            QListWidget::item {
                padding: 12px;
                border-bottom: 1px solid #2a2a3e;
            }
            QListWidget::item:selected {
                background-color: #3a3a5e;
            }
        """)
        self._playlist_list.currentRowChanged.connect(self._on_playlist_selected)
        left_layout.addWidget(self._playlist_list)

        # Delete playlist button
        del_playlist_btn = QPushButton("Excluir Playlist")
        del_playlist_btn.setStyleSheet("""
            QPushButton {
                background-color: #e17055; color: white;
                padding: 8px; border-radius: 6px;
            }
            QPushButton:hover { background-color: #d63031; }
        """)
        del_playlist_btn.clicked.connect(self._delete_playlist)
        left_layout.addWidget(del_playlist_btn)

        splitter.addWidget(left_panel)

        # Right panel - playlist items
        right_panel = QFrame()
        right_panel.setStyleSheet("background-color: #16213e; border-radius: 8px;")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(16, 16, 16, 16)

        right_header = QHBoxLayout()
        self._right_title = QLabel("Selecione uma playlist")
        self._right_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #ffffff;")
        right_header.addWidget(self._right_title)
        right_header.addStretch()

        add_item_btn = QPushButton("+ Adicionar Widget")
        add_item_btn.setStyleSheet("""
            QPushButton {
                background-color: #00b894; color: white;
                padding: 8px 16px; border-radius: 6px; font-weight: bold;
            }
            QPushButton:hover { background-color: #00a381; }
        """)
        add_item_btn.clicked.connect(self._add_item)
        right_header.addWidget(add_item_btn)
        right_layout.addLayout(right_header)

        self._items_table = QTableWidget()
        self._items_table.setColumnCount(5)
        self._items_table.setHorizontalHeaderLabels(["Ordem", "Widget", "Tipo", "Duração", "Ações"])
        self._items_table.horizontalHeader().setStretchLastSection(True)
        self._items_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self._items_table.setStyleSheet("""
            QTableWidget {
                background-color: #1a1a2e; color: #ffffff;
                border: 1px solid #2a2a3e; border-radius: 6px;
                gridline-color: #2a2a3e;
            }
            QHeaderView::section {
                background-color: #1a1a2e; color: #a0a0b0;
                padding: 8px; border: none; font-weight: bold;
            }
        """)
        right_layout.addWidget(self._items_table)

        splitter.addWidget(right_panel)
        splitter.setSizes([300, 700])
        layout.addWidget(splitter)

    def _refresh_playlists(self) -> None:
        """Refresh the playlist list."""
        self._playlist_list.clear()
        playlists = self._controller.get_all_with_counts()
        for pl in playlists:
            item = QListWidgetItem(f"{pl['name']}  ({pl['item_count']} itens)")
            item.setData(Qt.UserRole, pl["id"])
            self._playlist_list.addItem(item)

    def _on_playlist_selected(self, row: int) -> None:
        """Handle playlist selection."""
        if row < 0:
            return
        item = self._playlist_list.item(row)
        if not item:
            return
        self._current_playlist_id = item.data(Qt.UserRole)
        playlist = self._controller.get_by_id(self._current_playlist_id)
        if playlist:
            self._right_title.setText(f"Playlist: {playlist.name}")
            self._refresh_items()

    def _refresh_items(self) -> None:
        """Refresh the items table for the current playlist."""
        if not self._current_playlist_id:
            return
        items = self._controller.get_playlist_with_widgets(self._current_playlist_id)
        self._items_table.setRowCount(len(items))
        for row, item in enumerate(items):
            self._items_table.setItem(row, 0, QTableWidgetItem(str(item["order"] + 1)))
            self._items_table.setItem(row, 1, QTableWidgetItem(item["widget_name"]))
            self._items_table.setItem(row, 2, QTableWidgetItem(item["widget_type"]))
            self._items_table.setItem(row, 3, QTableWidgetItem(f"{item['duration']}s"))

            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 2, 4, 2)
            remove_btn = QPushButton("🗑️")
            remove_btn.setFixedSize(32, 28)
            remove_btn.clicked.connect(
                lambda checked=False, iid=item["item_id"]: self._remove_item(iid)
            )
            actions_layout.addWidget(remove_btn)
            self._items_table.setCellWidget(row, 4, actions_widget)

    def _add_playlist(self) -> None:
        dialog = PlaylistDialog(self._controller)
        if dialog.exec():
            self._refresh_playlists()

    def _delete_playlist(self) -> None:
        if not self._current_playlist_id:
            return
        reply = QMessageBox.question(
            self, "Confirmar", "Excluir esta playlist?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self._controller.delete(self._current_playlist_id)
            self._current_playlist_id = None
            self._right_title.setText("Selecione uma playlist")
            self._items_table.setRowCount(0)
            self._refresh_playlists()

    def _add_item(self) -> None:
        if not self._current_playlist_id:
            QMessageBox.information(self, "Aviso", "Selecione uma playlist primeiro.")
            return

        widgets = self._widget_controller.get_all()
        if not widgets:
            QMessageBox.information(self, "Aviso", "Crie widgets primeiro.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Adicionar Widget à Playlist")
        dialog.setMinimumSize(400, 200)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #16213e;
            }
            QLabel {
                color: #ffffff;
                font-size: 13px;
            }
            QComboBox {
                color: #ffffff;
                background-color: #1a1a2e;
                border: 1px solid #2a2a3e;
                border-radius: 4px;
                padding: 8px;
                font-size: 13px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                color: #ffffff;
                background-color: #1a1a2e;
                selection-background-color: #3a3a5e;
            }
            QSpinBox {
                color: #ffffff;
                background-color: #1a1a2e;
                border: 1px solid #2a2a3e;
                border-radius: 4px;
                padding: 6px;
                font-size: 13px;
            }
            QPushButton {
                padding: 8px 24px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
            }
        """)
        layout = QVBoxLayout(dialog)
        layout.setSpacing(16)

        form = QFormLayout()
        form.setSpacing(12)
        widget_combo = QComboBox()
        for w in widgets:
            widget_combo.addItem(f"{w.name} ({w.widget_type.value})", w.id)
        form.addRow("Widget:", widget_combo)

        duration_spin = QSpinBox()
        duration_spin.setRange(1, 86400)
        duration_spin.setValue(10)
        duration_spin.setSuffix(" segundos")
        form.addRow("Duração:", duration_spin)

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setStyleSheet("background-color: #2a2a3e; color: white;")
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(cancel_btn)
        add_btn = QPushButton("Adicionar")
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c63ff; color: white;
                padding: 8px 24px; border-radius: 6px; font-weight: bold;
            }
            QPushButton:hover { background-color: #5a52e0; }
        """)
        add_btn.clicked.connect(dialog.accept)
        btn_layout.addWidget(add_btn)
        layout.addLayout(btn_layout)

        if dialog.exec():
            items = self._controller.get_playlist_with_widgets(self._current_playlist_id)
            next_order = len(items)
            data = PlaylistItemCreate(
                widget_id=widget_combo.currentData(),
                order=next_order,
                duration=duration_spin.value(),
            )
            self._controller.add_item(self._current_playlist_id, data)
            self._refresh_items()
            self._refresh_playlists()

    def _remove_item(self, item_id: int) -> None:
        self._controller.remove_item(item_id)
        self._refresh_items()
        self._refresh_playlists()