"""WidgetView - CRUD interface for managing widgets with friendly forms."""

import json
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QDialog, QFormLayout, QLineEdit, QComboBox, QSpinBox,
    QTextEdit, QCheckBox, QGroupBox, QFrame, QSplitter,
    QFileDialog, QColorDialog, QStackedWidget,
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QFont

from admin.controllers.widget_controller import WidgetController
from core.schemas.widget_schema import WidgetCreate, WidgetUpdate
from core.models.widget import WidgetType


class SiteConfigForm(QWidget):
    """Form for Site widget configuration."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setStyleSheet("QLabel { color: #ffffff; }")
        layout = QFormLayout(self)
        layout.setSpacing(8)

        self._url_input = QLineEdit()
        self._url_input.setPlaceholderText("https://www.exemplo.com/dashboard")
        self._url_input.setStyleSheet("padding: 6px; border-radius: 4px; color: #ffffff; background-color: #1a1a2e;")
        layout.addRow("URL:", self._url_input)

        self._refresh_spin = QSpinBox()
        self._refresh_spin.setRange(0, 3600)
        self._refresh_spin.setValue(0)
        self._refresh_spin.setSuffix(" segundos (0 = sem refresh)")
        self._refresh_spin.setStyleSheet("color: #ffffff; background-color: #1a1a2e;")
        layout.addRow("Auto Refresh:", self._refresh_spin)

        self._scroll_check = QCheckBox("Ocultar barras de rolagem")
        self._scroll_check.setChecked(True)
        self._scroll_check.setStyleSheet("color: #ffffff;")
        layout.addRow("", self._scroll_check)

    def get_config(self) -> dict:
        return {
            "url": self._url_input.text().strip(),
            "auto_refresh": self._refresh_spin.value(),
            "hide_scrollbars": self._scroll_check.isChecked(),
        }

    def set_config(self, config: dict) -> None:
        self._url_input.setText(config.get("url", ""))
        self._refresh_spin.setValue(config.get("auto_refresh", 0))
        self._scroll_check.setChecked(config.get("hide_scrollbars", True))

    def validate(self) -> bool:
        url = self._url_input.text().strip()
        if not url:
            return False
        if not url.startswith(("http://", "https://")):
            self._url_input.setText(f"https://{url}")
        return True


class ImageConfigForm(QWidget):
    """Form for Image widget configuration."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setStyleSheet("QLabel { color: #ffffff; }")
        layout = QFormLayout(self)
        layout.setSpacing(8)

        file_layout = QHBoxLayout()
        self._file_path = QLineEdit()
        self._file_path.setPlaceholderText("Selecione uma imagem...")
        self._file_path.setReadOnly(True)
        self._file_path.setStyleSheet("padding: 6px; border-radius: 4px; color: #ffffff; background-color: #1a1a2e;")
        file_layout.addWidget(self._file_path)

        browse_btn = QPushButton("Procurar...")
        browse_btn.setStyleSheet("""
            QPushButton {
                background-color: #3a3a5e; color: white;
                padding: 6px 16px; border-radius: 4px;
            }
            QPushButton:hover { background-color: #4a4a6e; }
        """)
        browse_btn.clicked.connect(self._browse_file)
        file_layout.addWidget(browse_btn)
        layout.addRow("Arquivo:", file_layout)

        self._fit_combo = QComboBox()
        self._fit_combo.addItems(["Ajustar", "Preencher", "Esticar", "Tamanho real"])
        self._fit_combo.setStyleSheet("color: #ffffff; background-color: #1a1a2e;")
        self._fit_combo.setCurrentText("Ajustar")
        layout.addRow("Ajuste:", self._fit_combo)

    def _browse_file(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Selecionar Imagem", "",
            "Imagens (*.png *.jpg *.jpeg *.webp *.gif);;Todos (*)"
        )
        if file_path:
            self._file_path.setText(file_path)

    def get_config(self) -> dict:
        return {
            "file_path": self._file_path.text().strip(),
            "fit_mode": self._fit_combo.currentText(),
        }

    def set_config(self, config: dict) -> None:
        self._file_path.setText(config.get("file_path", ""))
        fit_mode = config.get("fit_mode", "Ajustar")
        # Handle old English values
        pt_map = {"contain": "Ajustar", "cover": "Preencher", "fill": "Esticar", "none": "Tamanho real"}
        fit_mode = pt_map.get(fit_mode, fit_mode)
        idx = self._fit_combo.findText(fit_mode)
        if idx >= 0:
            self._fit_combo.setCurrentIndex(idx)

    def validate(self) -> bool:
        return bool(self._file_path.text().strip())


class TextConfigForm(QWidget):
    """Form for Text widget configuration."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setStyleSheet("QLabel { color: #ffffff; }")
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        self._text_input = QTextEdit()
        self._text_input.setPlaceholderText("Digite o texto a ser exibido...")
        self._text_input.setMaximumHeight(120)
        self._text_input.setStyleSheet("padding: 6px; border-radius: 4px; color: #ffffff; background-color: #1a1a2e;")
        content_label = QLabel("Conteúdo:")
        content_label.setStyleSheet("color: #ffffff;")
        layout.addWidget(content_label)
        layout.addWidget(self._text_input)

        form = QFormLayout()
        self._font_size = QSpinBox()
        self._font_size.setRange(12, 300)
        self._font_size.setValue(48)
        self._font_size.setStyleSheet("color: #ffffff; background-color: #1a1a2e;")
        form.addRow("Tamanho:", self._font_size)

        color_layout = QHBoxLayout()
        self._font_color = QPushButton("#FFFFFF")
        self._font_color.setStyleSheet(
            "background-color: #FFFFFF; border: 1px solid #555; padding: 6px; border-radius: 4px;"
        )
        self._font_color.clicked.connect(self._pick_font_color)
        color_layout.addWidget(self._font_color)

        self._bg_color = QPushButton("#000000")
        self._bg_color.setStyleSheet(
            "background-color: #000000; border: 1px solid #555; padding: 6px; border-radius: 4px; color: white;"
        )
        self._bg_color.clicked.connect(self._pick_bg_color)
        color_layout.addWidget(self._bg_color)
        form.addRow("Cor Fonte/Fundo:", color_layout)

        self._bold_check = QCheckBox("Negrito")
        self._bold_check.setStyleSheet("color: #ffffff;")
        form.addRow("", self._bold_check)

        self._align_combo = QComboBox()
        self._align_combo.addItems(["center", "left", "right"])
        self._align_combo.setStyleSheet("color: #ffffff; background-color: #1a1a2e;")
        form.addRow("Alinhamento:", self._align_combo)

        layout.addLayout(form)

    def _pick_font_color(self) -> None:
        color = QColorDialog.getColor()
        if color.isValid():
            self._font_color.setText(color.name())
            self._font_color.setStyleSheet(
                f"background-color: {color.name()}; border: 1px solid #555; "
                f"padding: 6px; border-radius: 4px; "
                f"color: {'white' if color.lightness() < 128 else 'black'};"
            )

    def _pick_bg_color(self) -> None:
        color = QColorDialog.getColor()
        if color.isValid():
            self._bg_color.setText(color.name())
            self._bg_color.setStyleSheet(
                f"background-color: {color.name()}; border: 1px solid #555; "
                f"padding: 6px; border-radius: 4px; "
                f"color: {'white' if color.lightness() < 128 else 'black'};"
            )

    def get_config(self) -> dict:
        return {
            "text": self._text_input.toPlainText().strip(),
            "font_size": self._font_size.value(),
            "font_color": self._font_color.text(),
            "background_color": self._bg_color.text(),
            "bold": self._bold_check.isChecked(),
            "alignment": self._align_combo.currentText(),
        }

    def set_config(self, config: dict) -> None:
        self._text_input.setPlainText(config.get("text", ""))
        self._font_size.setValue(config.get("font_size", 48))
        self._font_color.setText(config.get("font_color", "#FFFFFF"))
        self._bg_color.setText(config.get("background_color", "#000000"))
        self._bold_check.setChecked(config.get("bold", False))
        idx = self._align_combo.findText(config.get("alignment", "center"))
        if idx >= 0:
            self._align_combo.setCurrentIndex(idx)

    def validate(self) -> bool:
        return bool(self._text_input.toPlainText().strip())


class WidgetDialog(QDialog):
    """Dialog for creating/editing widgets with friendly forms."""

    def __init__(self, controller: WidgetController, widget_id: int | None = None) -> None:
        super().__init__()
        self._controller = controller
        self._widget_id = widget_id
        self.setWindowTitle("Novo Widget" if widget_id is None else "Editar Widget")
        self.setMinimumSize(520, 450)
        self._setup_ui()

        if widget_id is not None:
            self._load_widget()

    def _setup_ui(self) -> None:
        """Setup the dialog UI."""
        self.setStyleSheet("""
            QDialog { background-color: #16213e; }
            QLabel { color: #ffffff; }
            QGroupBox { color: #ffffff; font-weight: bold; border: 1px solid #2a2a3e; border-radius: 6px; margin-top: 12px; padding-top: 16px; }
            QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; }
            QLineEdit { color: #ffffff; background-color: #1a1a2e; border: 1px solid #2a2a3e; border-radius: 4px; padding: 8px; }
            QComboBox { color: #ffffff; background-color: #1a1a2e; border: 1px solid #2a2a3e; border-radius: 4px; padding: 6px; }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView { color: #ffffff; background-color: #1a1a2e; selection-background-color: #3a3a5e; }
            QSpinBox { color: #ffffff; background-color: #1a1a2e; border: 1px solid #2a2a3e; border-radius: 4px; padding: 6px; }
            QCheckBox { color: #ffffff; }
            QTextEdit { color: #ffffff; background-color: #1a1a2e; border: 1px solid #2a2a3e; border-radius: 4px; }
        """)
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # Name and type
        top_form = QFormLayout()
        top_form.setSpacing(10)

        self._name_input = QLineEdit()
        self._name_input.setPlaceholderText("Ex: Dashboard Vendas, Logo Institucional...")
        top_form.addRow("Nome:", self._name_input)

        self._type_combo = QComboBox()
        type_labels = {
            WidgetType.SITE: "🌐 Site / Página Web",
            WidgetType.IMAGE: "🖼️ Imagem",
            WidgetType.TEXT: "📝 Texto",
            WidgetType.VIDEO: "🎬 Vídeo",
            WidgetType.PDF: "📄 PDF",
            WidgetType.HTML: "📁 HTML Local",
            WidgetType.CLOCK: "🕐 Relógio",
            WidgetType.COUNTDOWN: "⏱️ Contador Regressivo",
            WidgetType.WEATHER: "🌤️ Previsão do Tempo",
        }
        for wt in WidgetType:
            label = type_labels.get(wt, wt.value.capitalize())
            self._type_combo.addItem(label, wt.value)  # Store string value
        self._type_combo.currentIndexChanged.connect(self._on_type_changed)
        top_form.addRow("Tipo:", self._type_combo)

        dur_layout = QHBoxLayout()
        self._duration_spin = QSpinBox()
        self._duration_spin.setRange(1, 86400)
        self._duration_spin.setValue(10)
        self._duration_spin.setSuffix(" segundos")
        dur_layout.addWidget(self._duration_spin)

        self._priority_spin = QSpinBox()
        self._priority_spin.setRange(1, 1000)
        self._priority_spin.setValue(1)
        self._priority_spin.setPrefix("Prioridade: ")
        dur_layout.addWidget(self._priority_spin)

        top_form.addRow("Duração:", dur_layout)

        self._active_check = QCheckBox("Ativo")
        self._active_check.setChecked(True)
        top_form.addRow("", self._active_check)

        layout.addLayout(top_form)

        # Config section - dynamic form per type
        config_group = QGroupBox("Configuração do Widget")
        self._config_stack = QStackedWidget()

        # Page 0: Site
        self._site_form = SiteConfigForm()
        self._config_stack.addWidget(self._site_form)

        # Page 1: Image
        self._image_form = ImageConfigForm()
        self._config_stack.addWidget(self._image_form)

        # Page 2: Text
        self._text_form = TextConfigForm()
        self._config_stack.addWidget(self._text_form)

        # Page 3: Video (placeholder with file picker)
        self._video_form = self._create_file_form("Vídeo", "Vídeos (*.mp4 *.webm *.avi *.mkv)")
        self._config_stack.addWidget(self._video_form)

        # Page 4: PDF (placeholder with file picker)
        self._pdf_form = self._create_file_form("PDF", "PDF (*.pdf)")
        self._config_stack.addWidget(self._pdf_form)

        # Page 5: HTML local
        self._html_form = self._create_folder_form()
        self._config_stack.addWidget(self._html_form)

        # Page 6: Clock
        self._clock_form = self._create_clock_form()
        self._config_stack.addWidget(self._clock_form)

        # Page 7: Countdown
        self._countdown_form = self._create_countdown_form()
        self._config_stack.addWidget(self._countdown_form)

        # Page 8: Weather
        self._weather_form = self._create_weather_form()
        self._config_stack.addWidget(self._weather_form)

        config_layout = QVBoxLayout(config_group)
        config_layout.addWidget(self._config_stack)
        layout.addWidget(config_group)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Salvar Widget")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c63ff;
                color: white;
                padding: 10px 28px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #5a52e0;
            }
        """)
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def _create_file_form(self, label: str, filter_str: str) -> QWidget:
        """Create a generic file picker form."""
        w = QWidget()
        layout = QFormLayout(w)
        file_layout = QHBoxLayout()
        file_path = QLineEdit()
        file_path.setPlaceholderText(f"Selecione um arquivo {label}...")
        file_path.setReadOnly(True)
        file_path.setStyleSheet("padding: 6px; border-radius: 4px;")
        file_layout.addWidget(file_path)

        browse_btn = QPushButton("Procurar...")
        browse_btn.setStyleSheet("""
            QPushButton {
                background-color: #3a3a5e; color: white;
                padding: 6px 16px; border-radius: 4px;
            }
        """)
        browse_btn.clicked.connect(
            lambda: self._browse_file(file_path, f"{label} ({filter_str})")
        )
        file_layout.addWidget(browse_btn)
        layout.addRow("Arquivo:", file_layout)

        w._file_path = file_path
        w.get_config = lambda: {"file_path": file_path.text().strip()}
        w.set_config = lambda c: file_path.setText(c.get("file_path", ""))
        w.validate = lambda: bool(file_path.text().strip())
        return w

    def _create_folder_form(self) -> QWidget:
        """Create a folder picker form for HTML local."""
        w = QWidget()
        layout = QFormLayout(w)
        folder_layout = QHBoxLayout()
        folder_path = QLineEdit()
        folder_path.setPlaceholderText("Selecione a pasta com arquivos HTML...")
        folder_path.setReadOnly(True)
        folder_layout.addWidget(folder_path)

        browse_btn = QPushButton("Procurar...")
        browse_btn.setStyleSheet("""
            QPushButton {
                background-color: #3a3a5e; color: white;
                padding: 6px 16px; border-radius: 4px;
            }
        """)
        browse_btn.clicked.connect(
            lambda: self._browse_folder(folder_path)
        )
        folder_layout.addWidget(browse_btn)
        layout.addRow("Pasta:", folder_layout)

        index_label = QLabel("index.html")
        index_label.setStyleSheet("color: #888; font-size: 11px;")
        layout.addRow("", index_label)

        w._file_path = folder_path
        w.get_config = lambda: {"file_path": folder_path.text().strip()}
        w.set_config = lambda c: folder_path.setText(c.get("file_path", ""))
        w.validate = lambda: bool(folder_path.text().strip())
        return w

    def _create_clock_form(self) -> QWidget:
        """Create a clock configuration form."""
        w = QWidget()
        layout = QFormLayout(w)
        fmt_combo = QComboBox()
        fmt_combo.addItems(["HH:mm:ss", "HH:mm", "dd/MM HH:mm", "dd/MM/yyyy HH:mm"])
        layout.addRow("Formato:", fmt_combo)

        font_spin = QSpinBox()
        font_spin.setRange(12, 300)
        font_spin.setValue(72)
        layout.addRow("Tamanho:", font_spin)

        w._fmt = fmt_combo
        w._font = font_spin
        w.get_config = lambda: {"format": fmt_combo.currentText(), "font_size": font_spin.value()}
        w.set_config = lambda c: (
            setattr(fmt_combo, "setCurrentText", c.get("format", "HH:mm:ss")),
            font_spin.setValue(c.get("font_size", 72)),
        )
        w.validate = lambda: True
        return w

    def _create_weather_form(self) -> QWidget:
        """Create a weather configuration form."""
        w = QWidget()
        layout = QFormLayout(w)
        layout.setSpacing(8)
        w.setStyleSheet("QLabel { color: #ffffff; }")

        city_input = QLineEdit()
        city_input.setPlaceholderText("Ex: São Paulo, Rio de Janeiro, New York...")
        city_input.setText("São Paulo")
        city_input.setStyleSheet("padding: 6px; border-radius: 4px; color: #ffffff; background-color: #1a1a2e;")
        layout.addRow("Cidade:", city_input)

        unit_combo = QComboBox()
        unit_combo.addItems(["celsius", "fahrenheit"])
        unit_combo.setStyleSheet("color: #ffffff; background-color: #1a1a2e;")
        layout.addRow("Unidade:", unit_combo)

        update_spin = QSpinBox()
        update_spin.setRange(10, 3600)
        update_spin.setValue(30)
        update_spin.setSuffix(" segundos")
        update_spin.setStyleSheet("color: #ffffff; background-color: #1a1a2e;")
        layout.addRow("Atualizar a cada:", update_spin)

        info_label = QLabel("Configure a chave OPENWEATHER_API_KEY no .env")
        info_label.setStyleSheet("color: #888; font-size: 11px;")
        layout.addRow("", info_label)

        w._city = city_input
        w._unit = unit_combo
        w._update = update_spin
        w.get_config = lambda: {"city": city_input.text().strip(), "unit": unit_combo.currentText(), "update_interval": update_spin.value()}
        w.set_config = lambda c: (
            city_input.setText(c.get("city", "São Paulo")),
            unit_combo.setCurrentText(c.get("unit", "celsius")),
            update_spin.setValue(c.get("update_interval", 30)),
        )
        w.validate = lambda: True
        return w

    def _create_countdown_form(self) -> QWidget:
        """Create a countdown configuration form."""
        w = QWidget()
        layout = QFormLayout(w)
        target_input = QLineEdit()
        target_input.setPlaceholderText("2026-12-31 23:59:59")
        layout.addRow("Data alvo:", target_input)

        w._target = target_input
        w.get_config = lambda: {"target": target_input.text().strip()}
        w.set_config = lambda c: target_input.setText(c.get("target", ""))
        w.validate = lambda: bool(target_input.text().strip())
        return w

    def _browse_file(self, line_edit: QLineEdit, filter_str: str) -> None:
        file_path, _ = QFileDialog.getOpenFileName(self, "Selecionar Arquivo", "", filter_str)
        if file_path:
            line_edit.setText(file_path)

    def _browse_folder(self, line_edit: QLineEdit) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Selecionar Pasta")
        if folder:
            line_edit.setText(folder)

    def _get_current_form(self) -> QWidget:
        """Get the config form for the current widget type."""
        widget_type = self._type_combo.currentData()
        mapping = {
            "site": 0,
            "image": 1,
            "text": 2,
            "video": 3,
            "pdf": 4,
            "html": 5,
            "clock": 6,
            "countdown": 7,
            "weather": 8,
        }
        idx = mapping.get(widget_type, 0)
        self._config_stack.setCurrentIndex(idx)
        return self._config_stack.currentWidget()

    def _on_type_changed(self, index: int) -> None:
        """Update config form when widget type changes."""
        self._get_current_form()

    def _load_widget(self) -> None:
        """Load widget data for editing."""
        widget = self._controller.get_by_id(self._widget_id)
        if not widget:
            return
        self._name_input.setText(widget.name)
        idx = self._type_combo.findData(widget.widget_type.value)
        if idx >= 0:
            self._type_combo.setCurrentIndex(idx)
        self._duration_spin.setValue(widget.duration)
        self._priority_spin.setValue(widget.priority)
        self._active_check.setChecked(widget.active)

        # Load config into the form
        try:
            config = json.loads(widget.config) if widget.config else {}
        except json.JSONDecodeError:
            config = {}
        form = self._get_current_form()
        form.set_config(config)

    def _save(self) -> None:
        """Save widget data."""
        name = self._name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Validação", "Nome é obrigatório.")
            return

        widget_type = self._type_combo.currentData()
        form = self._get_current_form()

        if not form.validate():
            QMessageBox.warning(self, "Validação", "Preencha todos os campos obrigatórios.")
            return

        config = form.get_config()

        if self._widget_id is None:
            data = WidgetCreate(
                name=name,
                widget_type=widget_type,
                duration=self._duration_spin.value(),
                config=config,
                priority=self._priority_spin.value(),
                active=self._active_check.isChecked(),
            )
            self._controller.create(data)
        else:
            data = WidgetUpdate(
                name=name,
                duration=self._duration_spin.value(),
                config=config,
                priority=self._priority_spin.value(),
                active=self._active_check.isChecked(),
            )
            self._controller.update(self._widget_id, data)

        self.accept()


class WidgetView(QWidget):
    """Widget management view."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._controller = WidgetController()
        self._setup_ui()
        self._refresh_table()

    def _setup_ui(self) -> None:
        """Setup the view UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()
        title = QLabel("Widgets")
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #ffffff;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        add_btn = QPushButton("+ Novo Widget")
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c63ff;
                color: white;
                padding: 10px 20px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #5a52e0; }
        """)
        add_btn.clicked.connect(self._add_widget)
        header_layout.addWidget(add_btn)
        layout.addLayout(header_layout)

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(7)
        self._table.setHorizontalHeaderLabels([
            "ID", "Nome", "Tipo", "Duração", "Prioridade", "Ativo", "Ações"
        ])
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.setAlternatingRowColors(True)
        self._table.setStyleSheet("""
            QTableWidget {
                background-color: #16213e;
                color: #ffffff;
                border: 1px solid #2a2a3e;
                border-radius: 8px;
                gridline-color: #2a2a3e;
            }
            QTableWidget::item { padding: 8px; }
            QHeaderView::section {
                background-color: #1a1a2e;
                color: #a0a0b0;
                padding: 10px;
                border: none;
                font-weight: bold;
            }
        """)
        layout.addWidget(self._table)

    def _refresh_table(self) -> None:
        """Refresh the widgets table."""
        widgets = self._controller.get_all()
        self._table.setRowCount(len(widgets))
        self._table.verticalHeader().setDefaultSectionSize(48)

        for row, widget in enumerate(widgets):
            self._table.setItem(row, 0, QTableWidgetItem(str(widget.id)))
            self._table.setItem(row, 1, QTableWidgetItem(widget.name))
            self._table.setItem(row, 2, QTableWidgetItem(widget.widget_type.value))
            self._table.setItem(row, 3, QTableWidgetItem(f"{widget.duration}s"))
            self._table.setItem(row, 4, QTableWidgetItem(str(widget.priority)))
            self._table.setItem(row, 5, QTableWidgetItem("✅" if widget.active else "❌"))

            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 2, 4, 2)
            actions_layout.setSpacing(4)

            edit_btn = QPushButton("✏️")
            edit_btn.setFixedSize(32, 28)
            edit_btn.clicked.connect(lambda checked=False, wid=widget.id: self._edit_widget(wid))
            actions_layout.addWidget(edit_btn)

            delete_btn = QPushButton("🗑️")
            delete_btn.setFixedSize(32, 28)
            delete_btn.clicked.connect(lambda checked=False, wid=widget.id: self._delete_widget(wid))
            actions_layout.addWidget(delete_btn)

            self._table.setCellWidget(row, 6, actions_widget)

    def _add_widget(self) -> None:
        """Open dialog to add a new widget."""
        dialog = WidgetDialog(self._controller)
        if dialog.exec():
            self._refresh_table()

    def _edit_widget(self, widget_id: int) -> None:
        """Open dialog to edit a widget."""
        dialog = WidgetDialog(self._controller, widget_id)
        if dialog.exec():
            self._refresh_table()

    def _delete_widget(self, widget_id: int) -> None:
        """Delete a widget after confirmation."""
        reply = QMessageBox.question(
            self, "Confirmar", "Excluir este widget?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self._controller.delete(widget_id)
            self._refresh_table()