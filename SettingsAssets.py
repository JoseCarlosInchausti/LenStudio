from PyQt6.QtWidgets import QWidget,QComboBox,QPushButton, QMessageBox, QLineEdit, QLabel, QHBoxLayout, QVBoxLayout, QListWidget,QListWidgetItem,QAbstractItemView,QCheckBox,QTextEdit,QFrame,QGroupBox,QStackedWidget
from PyQt6.QtGui import QIcon,QFont,QPixmap, QPainter, QImage, QTextOption, QColor,QCursor
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtCore import QSize, Qt, QRectF,QEvent,pyqtSignal

class StyledEmptyWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setObjectName("emptyWidget")
        self.setStyleSheet("QWidget#emptyWidget { background-color: #152238; }")

class ListWidget(StyledEmptyWidget):
    items_changed = pyqtSignal(list)

    def __init__(self, initial_items: list = None, max_item_length: int = 4, caption: str = "Enter item...", title=None):
        super().__init__()
        self.max_item_length = max_item_length
        self.items = list(initial_items) if initial_items else []

        outter_layout = QHBoxLayout()
        outter_layout.addSpacing(30)
        vertical_layout = QVBoxLayout()
        outter_layout.addLayout(vertical_layout)
        vertical_layout.setContentsMargins(0, 0, 0, 0)
        vertical_layout.setSpacing(6)
        self.setLayout(outter_layout)
        #Add title
        if title:
            self.title_label=QLabel(title)
            self.title_label.setStyleSheet("QLabel { color: white; font-size: 14px; }")
        vertical_layout.addWidget(self.title_label)

        # Input row
        input_layout = QHBoxLayout()
        input_layout.setSpacing(6)
        self.line_edit = QLineEdit()
        self.line_edit.setPlaceholderText(caption)
        self.line_edit.setMaxLength(max_item_length)
        self.line_edit.setFixedWidth(300)
        self.line_edit.setStyleSheet("""
                                                    QLineEdit {
                                                        border: 1px solid lightgray;
                                                        border-radius: 6px;
                                                        padding: 4px 8px;
                                                        background-color: white;
                                                        color: #152238;
                                                        font-size: 13px;
                                                    }
                                                    QLineEdit:focus {
                                                        border: 2px solid #4A9EFF;
                                                    }
                                                    """)
        self.line_edit.returnPressed.connect(self._add_item)
        self.add_button = QPushButton("Add")
        self.add_button.setStyleSheet("""
                                        QPushButton {
                                            background-color: white;
                                            border-radius: 8px;
                                            color: #152238;
                                            font-size: 16px;
                                            font-weight: 600;
                                            padding: 6px 18px;
                                        }
                                        QPushButton:hover {
                                            background-color: #f0ffff;
                                        }
                                        QPushButton:pressed {
                                            background-color: #f0f8ff;
                                            padding-top: 2px;
                                            padding-left: 2px;
                                        }""")
        self.add_button.clicked.connect(self._add_item)
        input_layout.addWidget(self.line_edit)
        input_layout.addWidget(self.add_button)
        input_layout.addStretch()
        vertical_layout.addLayout(input_layout)

        # Chips area
        self.chips_widget = QWidget()
        self.chips_widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.chips_layout = QHBoxLayout()
        self.chips_layout.setContentsMargins(0, 0, 0, 0)
        self.chips_layout.setSpacing(6)
        self.chips_widget.setLayout(self.chips_layout)
        vertical_layout.addWidget(self.chips_widget)

        self._rebuild_chips()

    def _add_item(self):
        item = self.line_edit.text().strip()
        if not item or item in self.items:
            self.line_edit.clear()
            return
        self.items.append(item)
        self.line_edit.clear()
        self._rebuild_chips()
        self.items_changed.emit(self.items)

    def _remove_item(self, item: str):
        if item in self.items:
            self.items.remove(item)
            self._rebuild_chips()
            self.items_changed.emit(self.items)

    def _rebuild_chips(self):
        while self.chips_layout.count():
            i = self.chips_layout.takeAt(0)
            if i.widget():
                i.widget().deleteLater()
        for item in self.items:
            self.chips_layout.addWidget(self._make_chip(item))
        self.chips_layout.addStretch()

    def _make_chip(self, item: str) -> QWidget:
        chip = QWidget()
        chip.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        chip.setObjectName("chip")
        chip.setStyleSheet("""
            QWidget#chip {
                background-color: #4A9EFF;
                border-radius: 6px;
            }
        """)
        layout = QHBoxLayout()
        layout.setContentsMargins(6, 2, 6, 2)
        layout.setSpacing(4)
        chip.setLayout(layout)

        label = QLabel(item)
        label.setStyleSheet("QLabel { color: white; font-size: 13px; font-weight: 600; background-color: transparent; }")
        remove_btn = QPushButton("×")
        remove_btn.setFixedSize(16, 16)
        remove_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                font-size: 13px;
                font-weight: 600;
                border: none;
                padding: 0px;
            }
            QPushButton:hover {
                color: #ffcccc;
            }
        """)
        remove_btn.clicked.connect(lambda: self._remove_item(item))

        layout.addWidget(label)
        layout.addWidget(remove_btn)
        return chip

    def get_status(self) -> list:
        return list(self.items)

    def set_status(self, items: list):
        self.items = list(items)
        self._rebuild_chips()

class SectionLabel(StyledEmptyWidget):
    def __init__(self, label: str, caption: str = None):
        super().__init__()
        # 30px left spacer aligns with labels in checkbox widgets — use this
        # pattern for any widget that has no checkbox on its left side.
        outer_layout = QHBoxLayout()
        outer_layout.addSpacing(30)
        inner_layout = QVBoxLayout()
        inner_layout.setContentsMargins(0, 0, 0, 0)
        inner_layout.setSpacing(2)
        outer_layout.addLayout(inner_layout)
        self.setLayout(outer_layout)

        title = QLabel(label)
        title.setStyleSheet("QLabel { color: white; font-size: 14px; }")
        inner_layout.addWidget(title)

        if caption:
            cap = QLabel(caption)
            cap.setStyleSheet("QLabel { color: #aaaaaa; font-size: 11px; }")
            cap.setWordWrap(True)
            inner_layout.addWidget(cap)


class DraggableOrderList(StyledEmptyWidget):
    order_changed = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self._available_fields = []
        self._saved_order = []

        outer_layout = QHBoxLayout()
        outer_layout.addSpacing(30)
        inner_layout = QVBoxLayout()
        inner_layout.setContentsMargins(0, 0, 0, 0)
        inner_layout.setSpacing(4)
        outer_layout.addLayout(inner_layout)
        self.setLayout(outer_layout)

        hint = QLabel("Drag to reorder  ·  uncheck to exclude from cycle")
        hint.setStyleSheet("QLabel { color: #888888; font-size: 11px; }")
        inner_layout.addWidget(hint)

        first_label = QLabel("↑ First")
        last_label = QLabel("↓ Last")
        for lbl in (first_label, last_label):
            lbl.setStyleSheet("QLabel { color: #666666; font-size: 11px; }")
        inner_layout.addWidget(first_label)
        inner_layout.addWidget(last_label)

        self.list_widget = QListWidget()
        self.list_widget.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.list_widget.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.list_widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.list_widget.setSpacing(2)
        self.list_widget.setStyleSheet("""
            QListWidget {
                background-color: #0f1c33;
                border: 1px solid #3a4a62;
                border-radius: 6px;
                color: white;
                font-size: 14px;
                padding: 4px;
            }
            QListWidget::item {
                padding: 6px 4px;
                border-radius: 4px;
            }
            QListWidget::item:selected {
                background-color: #2a3a52;
            }
            QListWidget::item:hover {
                background-color: #1e2e44;
            }
            QListWidget::indicator {
                width: 15px;
                height: 15px;
                border: 1px solid #4A9EFF;
                border-radius: 3px;
                background-color: transparent;
            }
            QListWidget::indicator:checked {
                background-color: #4A9EFF;
            }
            QListWidget::indicator:unchecked:disabled {
                border-color: #3a4a62;
            }
        """)
        self.list_widget.model().rowsMoved.connect(
            lambda: self.order_changed.emit(self.get_status())
        )
        self.list_widget.itemChanged.connect(
            lambda: self.order_changed.emit(self.get_status())
        )
        inner_layout.addWidget(self.list_widget)


    def set_available_fields(self, fields: list):
        self._available_fields = list(fields)
        self._populate()

    def _populate(self):
        self.list_widget.blockSignals(True)
        self.list_widget.clear()

        saved = self._saved_order
        ordered = [f for f in saved if f in self._available_fields]
        ordered += [f for f in self._available_fields if f not in ordered]

        for field in ordered:
            item = QListWidgetItem("⠿   " + field)
            item.setData(Qt.ItemDataRole.UserRole, field)
            item.setFlags(
                Qt.ItemFlag.ItemIsEnabled |
                Qt.ItemFlag.ItemIsSelectable |
                Qt.ItemFlag.ItemIsUserCheckable |
                Qt.ItemFlag.ItemIsDragEnabled
            )
            is_checked = (field in saved) if saved else True
            item.setCheckState(Qt.CheckState.Checked if is_checked else Qt.CheckState.Unchecked)
            self.list_widget.addItem(item)

        self.list_widget.blockSignals(False)

    def get_status(self) -> list:
        result = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                result.append(item.data(Qt.ItemDataRole.UserRole))
        return result

    def set_status(self, value):
        self._saved_order = list(value) if value else []
        if self._available_fields:
            self._populate()


class RadioSelector(StyledEmptyWidget):
    selection_changed = pyqtSignal(str)

    def __init__(self, options: list, title: str = None):
        super().__init__()
        self.options = options
        self.selected = options[0] if options else None
        self.buttons = {}

        outer_layout = QHBoxLayout()
        outer_layout.addSpacing(30)
        inner_layout = QVBoxLayout()
        inner_layout.setContentsMargins(0, 0, 0, 0)
        inner_layout.setSpacing(6)
        outer_layout.addLayout(inner_layout)
        self.setLayout(outer_layout)

        if title:
            title_label = QLabel(title)
            title_label.setStyleSheet("QLabel { color: white; font-size: 14px; }")
            inner_layout.addWidget(title_label)

        pills_layout = QHBoxLayout()
        pills_layout.setSpacing(8)
        pills_layout.setContentsMargins(0, 0, 0, 0)
        for option in options:
            btn = QPushButton(option)
            btn.setCheckable(False)
            btn.clicked.connect(lambda checked, o=option: self._select(o))
            self.buttons[option] = btn
            pills_layout.addWidget(btn)
        pills_layout.addStretch()
        inner_layout.addLayout(pills_layout)

        self._update_styles()

    def _select(self, option: str):
        self.selected = option
        self._update_styles()
        self.selection_changed.emit(option)

    def _update_styles(self):
        for option, btn in self.buttons.items():
            if option == self.selected:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #4A9EFF;
                        border-radius: 8px;
                        color: white;
                        font-size: 14px;
                        font-weight: 600;
                        padding: 4px 18px;
                        border: none;
                    }
                    QPushButton:disabled {
                        background-color: #2a3a52;
                        color: #556677;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #2a3a52;
                        border-radius: 8px;
                        color: #aaaaaa;
                        font-size: 14px;
                        font-weight: 600;
                        padding: 4px 18px;
                        border: 1px solid #3a4a62;
                    }
                    QPushButton:hover {
                        background-color: #3a4a62;
                        color: white;
                    }
                    QPushButton:disabled {
                        background-color: #1c2840;
                        color: #445566;
                        border-color: #2a3548;
                    }
                """)

    def get_status(self) -> str:
        return self.selected

    def set_status(self, value: str):
        if value in self.options:
            self.selected = value
        else:
            self.selected = self.options[0] if self.options else None
        self._update_styles()


class Checkbox(StyledEmptyWidget):
    def __init__(self,checkbox_title, checkbox_caption=None):
        super().__init__()
        self.horizontal_layout = QHBoxLayout()
        # self.horizontal_layout.setSpacing(8)
        checkmark_title_label=QLabel(checkbox_title)
        checkmark_title_label.setStyleSheet("QLabel { color: white; font-size: 14px; }")
        self.checkbox = QCheckBox()
        self.checkbox.setStyleSheet("""
                                    QCheckBox {
                                        background-color: transparent;
                                    }
                                    """)
        self.horizontal_layout.addWidget(self.checkbox)
        self.horizontal_layout.addSpacing(10)

        if checkbox_caption:
            labels_layout=QVBoxLayout()
            checkmark_caption_label=QLabel(checkbox_caption)
            labels_layout.addWidget(checkmark_title_label)
            labels_layout.addWidget(checkmark_caption_label)
            self.horizontal_layout.addLayout(labels_layout)
            checkmark_caption_label.setStyleSheet("QLabel { color: white; font-size: 10px; }")
        else:
            self.horizontal_layout.addWidget(checkmark_title_label)
        self.horizontal_layout.addStretch()
        self.setLayout(self.horizontal_layout)

    def get_status(self):
        return self.checkbox.isChecked() 
    
    def set_status(self,status):
        #status is str from json file
        is_checked=bool(status)
        self.checkbox.setChecked(is_checked)
