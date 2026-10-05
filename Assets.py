from PyQt6.QtWidgets import QWidget,QComboBox,QPushButton, QMessageBox, QLineEdit, QLabel, QHBoxLayout, QVBoxLayout, QListWidget,QCheckBox,QTextEdit,QFrame,QGroupBox,QStackedWidget,QScrollArea,QSizePolicy
from PyQt6.QtGui import QIcon,QFont,QPixmap, QPainter, QImage, QTextOption, QColor,QCursor,QPen
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtCore import QSize, Qt, QRectF, QRect, QEvent, pyqtSignal, QTimer
import math
import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets, QtCore
import numpy as np
import json
import SettingsAssets
import Theme

class CheckBox():
    def __init__(self,text,main_window,background_color=None):
        self.checkbox = QCheckBox(text)
        
        if background_color:
            self.checkbox.setStyleSheet(f"""
                                        QCheckBox {{
                                            background-color: {background_color};
                                            color: white;
                                            padding: 4px 8px;
                                            border-radius: 6px;
                                            }}
                                        """)
        else:
            self.checkbox.setStyleSheet("color: white;")
        font = QFont()
        font.setPointSize(main_window.FONT_SIZES["input box labels"])
        self.checkbox.setFont(font)

class StyledText(QLabel):
    def __init__(self, text = ""):
        super().__init__(text)
        self.setStyleSheet("""
                            QLabel {
                                color: white;
                                font-size: 16px;
                                }
                           """)

class ClickEffectStyleButton(QPushButton):
    def __init__(self, text="", parent=None, size=(150, 25)):
        super().__init__(text, parent)

        self.setFixedSize(size[0],size[1])

        self.setStyleSheet("""
            QPushButton {
                background-color: white;
                border-radius: 8px;
                color: #152238;
                font-size: 16px;
                font-weight: 600;
            }

            QPushButton:hover {
                background-color: #f0ffff;
            }

            QPushButton:pressed {
                background-color: #f0f8ff;
                padding-top: 2px;
                padding-left: 2px;
            }

            QPushButton:disabled {
                background-color: #a9a9a9;
                border: 2px solid #a9a9a9;
                color: #d3d3d3;
            }
                           
            QPushButton:focus {
                border: 3px solid #4A9EFF;
                border-radius: 8px;
            }
        """)

class ClickEffectButton(QPushButton):
    def __init__(self, icon_path_unclicked, icon_path_clicked, size1, size2, parent=None):
        super().__init__(parent)

        # Load icons
        self.normal_icon = QIcon(icon_path_unclicked)
        self.pressed_icon = QIcon(icon_path_clicked)

        # Get PNG size from file
        pixmap = QPixmap(icon_path_unclicked)
        w, h = pixmap.width(), pixmap.height()

        # Apply icon and sizes
        self.setIcon(self.normal_icon)
        # display_size = QSize(200, 50)
        display_size = QSize(int(0.25*w), int(0.25*h))
        self.setIconSize(display_size)
        # self.setFixedSize(display_size.width() + 4, display_size.height() + 4)  # small padding to avoid clipping

        # Remove button background/border if desired
        self.setStyleSheet("QPushButton { border: none; background: transparent; }")

        # Connect click effects
        self.pressed.connect(self.on_pressed)
        self.released.connect(self.on_released)

    def on_pressed(self):
        self.setIcon(self.pressed_icon)

    def on_released(self):
        self.setIcon(self.normal_icon)

class InputField(QHBoxLayout):
    def __init__(self,label_text,main_window,add_stretch=True, multi_line=False):
        super().__init__()
        self.label = QLabel(label_text)
        self.label.setStyleSheet("color: white;")
        font = QFont()
        font.setPointSize(main_window.FONT_SIZES["input box labels"])
        self.label.setFont(font)
        if multi_line:
            self.input_field = QTextEdit()
            self.input_field.setStyleSheet("""
                                            QTextEdit {
                                                    background-color: #2e2e2e;  /* dark gray */
                                                    color: white;               /* white text */
                                                    border: 1px solid white;     /* white border */
                                                    padding: 4px;
                                                    selection-background-color: #0078d7;  /* light blue selection */
                                                    selection-color: white;
                                                }
                                            """)
        else:
            self.input_field = QLineEdit()
            self.input_field.setStyleSheet("""
                                            QLineEdit {
                                                    background-color: #2e2e2e;  /* dark gray */
                                                    color: white;               /* white text */
                                                    border: 1px solid white;     /* white border */
                                                    padding: 4px;
                                                    selection-background-color: #0078d7;  /* light blue selection */
                                                    selection-color: white;
                                                }
                                            """)
        self.addWidget(self.label)
        if add_stretch:
            self.addStretch() 
        self.addWidget(self.input_field)

class ScrollableList(QListWidget):
    def __init__(self,items,connected_function):
        super().__init__()
        self.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        for item in items:
            self.addItem(item)
        self.itemSelectionChanged.connect(connected_function)
        self.style = """
                                QListWidget {
                                    background-color: #2e2e2e;  /* dark gray */
                                    color: white;               /* white text */
                                    border: 1px solid white;     /* white border */
                                }
                                QScrollBar:vertical {
                                    background: #2e2e2e;
                                    width: 12px;
                                    margin: 0px;
                                }
                                QScrollBar::handle:vertical {
                                    background: #555;
                                    min-height: 20px;
                                    border-radius: 4px;
                                }
                                QCheckBox {
                                    color: white;
                                    background-color: transparent;
                                }
                            """
        self.setStyleSheet(self.style)


class DropdownMenu(QHBoxLayout):
    def __init__(self,label_text,drop_down_items,main_window,preset_idx=0):
        super().__init__()
        self.label = QLabel(label_text)
        self.label.setStyleSheet("color: white;")
        font = QFont()
        font.setPointSize(main_window.FONT_SIZES["input box labels"])
        self.label.setFont(font)
        self.dropdown = QComboBox()
        self.dropdown.addItems(drop_down_items)
        self.dropdown.setCurrentIndex(preset_idx)
        self.dropdown.setStyleSheet("""
                                    QComboBox {
                                    background-color: #2e2e2e;  /* closed state */
                                    color: white;
                                    border: 1px solid white;
                                    padding: 4px;
                                    }
                                    QComboBox QAbstractItemView {   /* dropdown list */
                                    background-color: #2e2e2e;
                                    color: white;
                                    selection-background-color: #0078d7;
                                    selection-color: white;
                                    }
                                    """)
        self.addWidget(self.label)
        self.addStretch()
        self.addWidget(self.dropdown)
        view = self.dropdown.view()
        view.setMinimumWidth(
            max(self.dropdown.fontMetrics().horizontalAdvance(self.dropdown.itemText(i))
                for i in range(self.dropdown.count())) + 30)

class SvgWidget(QSvgWidget):
    def __init__(self, file_path, parent=None):
        super().__init__(file_path, parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setStyleSheet("background: transparent;")
        self.setMinimumSize(1,1)  # needed to allow proper scaling

    def resizeEvent(self, event):
        # keep aspect ratio and center
        self.renderer().setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatio)
        super().resizeEvent(event)

def show_popup_window(title,text,header_icon_path):
    msg = QMessageBox()
    msg.setWindowTitle(title)
    # msg.setWindowIcon(QIcon(header_icon_path)) #Removes the default icon
    msg.setText(text)
    msg.exec()

class ImageWidget(pg.GraphicsLayoutWidget):
    def __init__(self,image_arr,panel_size=(200,200)):
        super().__init__()
        # Remove outer margins of the GraphicsLayoutWidget
        self.ci.setContentsMargins(0, 0, 0, 0)
        self.ci.layout.setSpacing(0)

        # Remove Qt frame around widget
        self.setFrameStyle(0)

        # Create a ViewBox with no padding
        self.plot = self.addViewBox()
        self.plot.setAspectLocked(True)
        self.plot.suggestPadding(0)      # *** THIS removes most of the visible border ***
        self.plot.setBorder(None)    # removes ViewBox border

        panel_h, panel_w = panel_size[0], panel_size[1]
        self.img_h, self.img_w = image_arr.shape[0], image_arr.shape[1]
        # self.plot = self.addViewBox()
        # self.plot.setAspectLocked(True)
        self.img_item = pg.ImageItem()
        self.plot.addItem(self.img_item)
        self.img_item.setImage(image_arr)
        self.setFixedSize(panel_h, panel_w)
        self.plot.setLimits(xMin=0, xMax=self.img_w, yMin=0, yMax=self.img_h, minXRange=10, minYRange=10)

    def update_image(self,new_image):
        self.img_item.setImage(new_image)
        self.plot.setLimits(xMin=0, xMax=self.img_w, yMin=0, yMax=self.img_h, minXRange=10, minYRange=10)


class Panel(QFrame):
    def __init__(self,border_radius=12,vertical=True):
        super().__init__()
        self.border_radius=border_radius
        if vertical:
            self.layout = QVBoxLayout(self)
        else:
            self.layout = QHBoxLayout(self)

        self.setStyleSheet("""
            QFrame {{
                background-color: #152238;
                border-radius: {}px;
                padding: 0px;
            }}
        """.format(self.border_radius))

    def add_title(self,title='No title',center_title=False):
        self.title_widget=QLabel(title)
        if center_title:
            self.title_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_widget.setObjectName('title')

        self.setStyleSheet(""" 
            QFrame {{
                background-color: #152238;
                border-radius: {}px;
                padding: 0px;
            }}
            QLabel#title {{
                font-size: 18px;
                font-weight: 600;
                color: white;
            }}
        """.format(self.border_radius))
        
        self.layout.addWidget(self.title_widget, alignment=Qt.AlignmentFlag.AlignTop)
        # self.layout.addStretch()
    def change_title(self,new_title):
        self.title_widget.setText(new_title)

    def add_widget(self,new_widget,stretch=(True,True)):
        if stretch[0]:
            self.layout.addStretch()
        self.layout.addWidget(new_widget)
        if stretch[1]:
            self.layout.addStretch()

    def add_layout(self,new_layout):
        self.layout.addLayout(new_layout)

class ScrollPanel(QFrame):
    def __init__(self, border_radius=12, vertical=True):
        super().__init__()
        self.border_radius = border_radius

        # Outer layout holds the title + scroll area
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        # Scroll area setup
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Inner container widget inside the scroll area
        self.scroll_widget = QWidget()
        self.scroll_widget.setStyleSheet("background-color: transparent;")
        if vertical:
            self.inner_layout = QVBoxLayout(self.scroll_widget)
        else:
            self.inner_layout = QHBoxLayout(self.scroll_widget)
        self.inner_layout.setContentsMargins(8, 8, 8, 8)

        self.scroll_area.setWidget(self.scroll_widget)
        self.layout.addWidget(self.scroll_area)

        self._apply_stylesheet()

    def _apply_stylesheet(self):
        self.setStyleSheet("""
            QFrame {{
                background-color: #152238;
                border-radius: {r}px;
                padding: 0px;
            }}
            QScrollArea {{
                background-color: transparent;
                border: none;
            }}
            QLabel#title {{
                font-size: 18px;
                font-weight: 600;
                color: white;
                padding: 8px;
            }}
        """.format(r=self.border_radius))

    def add_title(self, title='No title', center_title=False):
        self.title_widget = QLabel(title)
        if center_title:
            self.title_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_widget.setObjectName('title')
        # Insert title at position 0, before the scroll area
        self.layout.insertWidget(0, self.title_widget, alignment=Qt.AlignmentFlag.AlignTop)
        self._apply_stylesheet()

    def change_title(self, new_title):
        self.title_widget.setText(new_title)

    def add_widget(self, new_widget, stretch=(True, True)):
        if stretch[0]:
            self.inner_layout.addStretch()
        self.inner_layout.addWidget(new_widget)
        if stretch[1]:
            self.inner_layout.addStretch()

    def add_layout(self, new_layout):
        self.inner_layout.addLayout(new_layout)

class StyledTextBox(QGroupBox):
    def __init__(self, title, content):
        super().__init__(title)

        # layout INSIDE the groupbox
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 5, 4, 5)
        layout.setSpacing(0)

        self.label = QLabel(content)
        self.label.setWordWrap(True)
        self.label.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        layout.addWidget(self.label)

        self.setStyleSheet(f"""
                            QGroupBox {{
                                border: 1px solid {Theme.BORDER};
                                border-radius: 8px;
                                margin-top: 10px;
                                background-color: #1a2a44;
                            }}

                            QGroupBox::title {{
                            subcontrol-origin: margin;
                            subcontrol-position: top left;
                            left: 8px;
                            padding: 0 4px;
                            background-color: {Theme.CARD};
                            color: {Theme.TXT_MUTE};
                            top: -1px;
                            }}
                            QLabel {{
                            color: {Theme.TXT};
                            }}
                            """)

    def update_content(self,new_text):
        self.label.setText(new_text)

class MetadataField(QWidget):
    """A clean label-over-value row for read-only metadata (no boxy frame)."""
    def __init__(self, label, value, mono=False):
        super().__init__()
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setObjectName("metaField")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(2, 7, 2, 8)
        lay.setSpacing(3)
        self.label = QLabel(str(label))
        self.label.setStyleSheet(
            f"color:{Theme.TXT_MUTE}; font-size:11px; font-weight:700; "
            f"letter-spacing:0.6px; background:transparent;")
        self.value = QLabel('' if str(value)=='nan' else str(value))
        self.value.setWordWrap(True)
        self.value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        mono_css = "font-family:'SF Mono','Menlo','Consolas',monospace;" if mono else ""
        self.value.setStyleSheet(
            f"color:{Theme.TXT}; font-size:15px; font-weight:600; {mono_css} background:transparent;")
        lay.addWidget(self.label)
        lay.addWidget(self.value)
        self.setStyleSheet(f"QWidget#metaField {{ border-bottom: 1px solid {Theme.BORDER}; }}")

    def update_content(self, new_text):
        self.value.setText('' if str(new_text)=='nan' else str(new_text))

class StyledInputBox(QWidget):
    def __init__(self, title, content, caps_lock=False, N_max_lines=None, center_text=False, quick_inspection_check=None):
        super().__init__()
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setObjectName("styledInputBox")
        self.setStyleSheet("QWidget#styledInputBox { background: transparent; }")
        self.quick_inspection_check = quick_inspection_check
        self.caps_lock = caps_lock
        self.greyed_out = False
        self.center_text = center_text
        self.N_max_lines = N_max_lines

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(4)

        # Label sits cleanly on top
        self.title_label = QLabel(str(title))
        self.title_label.setWordWrap(True)
        self.title_label.setStyleSheet(
            f"color:{Theme.TXT_MUTE}; font-size:11px; font-weight:700; "
            f"letter-spacing:0.5px; background:transparent;")

        # Text edit below
        self.text_edit = QTextEdit()
        self.text_edit.setWordWrapMode(QTextOption.WrapMode.WordWrap)
        self.text_edit.setFrameShape(QTextEdit.Shape.NoFrame)

        outer.addWidget(self.title_label)
        outer.addWidget(self.text_edit)

        self.update_text(str(content))
        if self.N_max_lines:
            self.text_edit.textChanged.connect(self._enforce_max_lines)
        if self.center_text:
            self.text_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if caps_lock:
            self.text_edit.textChanged.connect(self._force_uppercase)

        self._apply_style()
        self._set_line_count()

    def _apply_style(self, focus=False, disabled=False):
        border = Theme.ACCENT if focus else Theme.FIELD_BRD
        text = Theme.TXT_MUTE if disabled else Theme.TXT
        self.text_edit.setStyleSheet(f"""
            QTextEdit {{
                color: {text};
                background-color: {Theme.FIELD};
                border: 1px solid {border};
                border-radius: 8px;
                padding: 4px 8px;
            }}
        """)

    # def eventFilter(self,obj,event):
    #     if obj == self.text_edit:
    #         quick_inspection_active = self.quick_inspection_check() if self.quick_inspection_check else False
    #         if event.type() == QEvent.Type.FocusIn and quick_inspection_active:
    #             self._set_border(with_focus_outline=True)
    #         elif event.type() == QEvent.Type.FocusOut:
    #             self._set_border(with_focus_outline=False)
    #     return super().eventFilter(obj, event)
    
    def _set_border(self,with_focus_outline):
        self._apply_style(focus=with_focus_outline, disabled=self.greyed_out)

    def disable_input(self,grey_out=True):
        self.text_edit.setReadOnly(True)
        if grey_out:
            self.greyed_out=True
            self._apply_style(disabled=True)

    def enable_input(self):
        self.text_edit.setReadOnly(False)
        if self.greyed_out:
            self.greyed_out=False
            self._apply_style()

    def update_text(self,new_text):
        new_text=str(new_text)
        if self.caps_lock:
            self.text_edit.setPlainText('' if new_text=='nan' else new_text.upper())
        else:
            self.text_edit.setPlainText('' if new_text=='nan' else new_text)
        if self.center_text:
            self.text_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def get_content(self):
        current_content = self.text_edit.toPlainText()
        return current_content

    def change_input_size(self, new_size):
        font = QFont()
        font.setPointSize(int(new_size))
        self.text_edit.setFont(font)
        self._set_line_count()

    def _force_uppercase(self):
        cursor = self.text_edit.textCursor()
        pos = cursor.position()
        self.text_edit.blockSignals(True)
        self.text_edit.setPlainText(self.text_edit.toPlainText().upper())
        cursor.setPosition(pos)
        self.text_edit.setTextCursor(cursor)
        self.text_edit.blockSignals(False)

    def _enforce_max_lines(self):
        lines = self.text_edit.toPlainText().split('\n')
        if len(lines) > self.N_max_lines:
            cursor = self.text_edit.textCursor()
            pos = cursor.position()
            self.text_edit.blockSignals(True)
            self.text_edit.setPlainText('\n'.join(lines[:self.N_max_lines]))
            cursor.setPosition(min(pos, len(self.text_edit.toPlainText())))
            self.text_edit.setTextCursor(cursor)
            self.text_edit.blockSignals(False)

    def _set_line_count(self):
        if self.N_max_lines:
            font_metrics = self.text_edit.fontMetrics()
            line_height = font_metrics.lineSpacing()
            self.text_edit.setFixedHeight(self.N_max_lines * line_height + 30)
            if self.N_max_lines==1:
                self.text_edit.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
                self.text_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    def setFocus(self):
        self.text_edit.setFocus()

    def set_caps_lock(self, enabled: bool):
        if enabled == self.caps_lock:
            return
        self.caps_lock = enabled
        if enabled:
            self.text_edit.textChanged.connect(self._force_uppercase)
            self._force_uppercase()
        else:
            try:
                self.text_edit.textChanged.disconnect(self._force_uppercase)
            except RuntimeError:
                pass

class StatusLED(QWidget):
    COLORS = {"red":'#e74c3c',
              "yellow":'#f39c12',
              "orange":'#e67e22',
              "green":'#2ecc71',
            }
    def __init__(self, size=12):
        super().__init__()
        self.color = QColor(self.COLORS['red'])
        self.dot_size = size
        self.setFixedSize(size, size)

    def set_color(self, color):
        self.color = QColor(self.COLORS[color])
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(self.color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(0, 0, self.dot_size, self.dot_size)

class StatusWidget(QWidget):
    def __init__(self, text='', color='red', dot_size=12):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.indicator = StatusLED(size=dot_size)
        self.label = QLabel(text)
        self.label.setStyleSheet(f"color: {color};")

        layout.addWidget(self.indicator)
        layout.addWidget(self.label)

        self.set_status(color, text)

    def set_status(self, color: str, text: str = None):
        self.indicator.set_color(color)
        self.label.setStyleSheet(f"color: {color};")
        if text is not None:
            self.label.setText(text)

class StyledToggleSwitch(QCheckBox):
    def __init__(self,label='', accent="#4A9EFF", parent=None):
        super().__init__(label,parent)
        self.accent = accent
        self.setFixedHeight(28)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._apply_style()

    def _apply_style(self):
        self.setStyleSheet(f"""
            QCheckBox {{
                color: white;
                font-size: 15px;
                font-weight: 600;
                spacing: 12px;
            }}
            QCheckBox::indicator {{
                width: 54px;
                height: 28px;
                border-radius: 7px;
                background: rgba(255, 255, 255, 0.15);
                border: 1px solid rgba(255, 255, 255, 0.08);
            }}
            QCheckBox::indicator:checked {{
                background: {self.accent};
                border-color: {self.accent};
            }}
            QCheckBox::indicator:hover {{
                border-color: rgba(255, 255, 255, 0.25);
            }}
        """)


class StyledTabBar(QWidget):
    tab_clicked = pyqtSignal(str)  # emits the name of the clicked tab

    def __init__(self, tab_names: dict, orientation='horizontal',add_stretches=False,parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("""
            QWidget {
                background-color: #0a1628;
                border-radius: 10px;
            }
        """)

        self.tab_names_signals_dict = tab_names
        self.tab_names = list(self.tab_names_signals_dict.keys())
        self.active_tab = self.tab_names[0]
        self.buttons = {}

        self.orientation=orientation

        if self.orientation=='horizontal':
            layout = QHBoxLayout()
        elif self.orientation=='vertical':
            layout = QVBoxLayout()

        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(6)
        self.setLayout(layout)

        for tab_n,name in enumerate(tab_names):
            btn = QPushButton(name)
            btn.setCheckable(False)
            btn.clicked.connect(lambda checked, n=name: self._on_tab_clicked(n))
            self.buttons[name] = btn
            layout.addWidget(btn)
            if add_stretches and tab_n<len(tab_names)-1:
                layout.addStretch()
        if orientation == 'vertical' and add_stretches:
            layout.addStretch()
        self._update_styles()

    def _on_tab_clicked(self, name: str):
        if name == self.active_tab:
            return
        self.active_tab = name
        self._update_styles()
        self.tab_clicked.emit(self.tab_names_signals_dict[name])

    def set_active_tab(self, name: str):
        """Programmatically set the active tab without emitting the signal."""
        self.active_tab = name
        self._update_styles()

    def _update_styles(self):
        if self.orientation=='horizontal':
            active_style = f"""
                QPushButton {{
                    background-color: {Theme.ACCENT};
                    border-radius: 8px;
                    color: white;
                    font-size: 15px;
                    font-weight: 600;
                    padding: 6px 18px;
                    border: none;
                }}
                QPushButton:hover {{ background-color: {Theme.ACCENT_HI}; }}
            """
        else:
            active_style = f"""
                QPushButton {{
                    background-color: {Theme.ACCENT};
                    border-radius: 8px;
                    color: white;
                    font-size: 15px;
                    font-weight: 600;
                    padding: 6px 14px;
                    border: none;
                }}
                QPushButton:hover {{ background-color: {Theme.ACCENT_HI}; }}
            """
        inactive_style = f"""
            QPushButton {{
                background-color: transparent;
                border-radius: 8px;
                color: {Theme.TXT_MUTE};
                font-size: 15px;
                font-weight: 600;
                padding: 6px 14px;
                border: none;
            }}
            QPushButton:hover {{ background-color: #17273f; color: {Theme.TXT_SOFT}; }}
        """
        for name, btn in self.buttons.items():
            btn.setStyleSheet(active_style if name == self.active_tab else inactive_style)


class StyledGroupBox(QGroupBox):
    def __init__(self, title, vertical=True, parent=None):
        super().__init__(title)
        if vertical:
            self.inner_layout = QVBoxLayout(self)
        else:
            self.inner_layout = QHBoxLayout(self)
        self.inner_layout.setContentsMargins(4, 5, 4, 5)
        self.inner_layout.setSpacing(6)
        self.setStyleSheet(f"""
            QGroupBox {{
                border: 1px solid {Theme.BORDER};
                border-radius: 8px;
                margin-top: 10px;
                background-color: {Theme.CARD};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 8px;
                padding: 0 4px;
                background-color: {Theme.CARD};
                color: {Theme.TXT_MUTE};
                top: -1px;
            }}
        """)

    def add_widget(self, widget, stretch=0):
        self.inner_layout.addWidget(widget, stretch)

    def add_layout(self, layout, stretch=0):
        self.inner_layout.addLayout(layout, stretch)

    def add_stretch(self):
        self.inner_layout.addStretch()

    def add_spacing(self, spacing: int):
        self.inner_layout.addSpacing(spacing)

class StyledEmptyWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setObjectName("emptyWidget")
        self.setStyleSheet("QWidget#emptyWidget { background-color: #152238; }")

class InspectionSettings:
    def __init__(self,desing_file_path, config_file_path):
        self.desing_file_path, self.config_file_path = desing_file_path, config_file_path

        #Get design of menus
        with open(desing_file_path,'r') as design_file:
            self.desing_file_json = json.load(design_file)
        #Get configuration file
        with open(config_file_path,'r') as config_file:
            self.config_file_json = json.load(config_file)

        self.tabs_names = list(self.desing_file_json['tabs'].keys())

        self.name_to_widget_map={}

    def get_stacked_widget(self):
        self.stacked_settings_widget = QStackedWidget()

        for menu_name in self.tabs_names:
            temp_widget=StyledEmptyWidget()
            host_layout=QVBoxLayout()
            #Add function to populate settings
            host_layout = self._populate_layout(menu_name,host_layout)
            temp_widget.setLayout(host_layout)
            self.stacked_settings_widget.addWidget(temp_widget)
        self.stacked_settings_widget.setCurrentIndex(0)

        return self.stacked_settings_widget
    
    def get_setting(self, name):
        if name in self.name_to_widget_map:
            return self.name_to_widget_map[name].get_status()
        return self.config_file_json.get(name)

    def update_config_file(self):
        all_names = list(self.config_file_json.keys())
        existing_widgets_names = list(self.name_to_widget_map.keys())
        for widget_name in all_names:
            if widget_name in existing_widgets_names:
                self.config_file_json[widget_name] = self.name_to_widget_map[widget_name].get_status()
            else:
                print(f'{widget_name} does not exist in the UI')

        with open(self.config_file_path,'w') as old_config_file:
            json.dump(self.config_file_json, old_config_file, indent=4)

        print(self.name_to_widget_map)

    def _populate_layout(self,menu_name,host_layout):
        #Determine if a frame is needed:
        add_frame=True if type(self.desing_file_json['tabs'][menu_name])==dict else False
        if add_frame:
            frames_names_list = list(self.desing_file_json['tabs'][menu_name].keys())
            for frame_name in frames_names_list:
                #Create and add frame to host layout
                frame = StyledGroupBox(title=frame_name)
                host_layout.addWidget(frame)
                #Populate frame
                widgets_infos = self.desing_file_json['tabs'][menu_name][frame_name]
                for widget_info in widgets_infos:
                    #Create widget
                    widget=self._create_widget(widget_info)
                    if widget:
                        frame.add_widget(widget)
                        if 'activate if checked' in widget_info:
                            ctrl = self.name_to_widget_map.get(widget_info['activate if checked'])
                            if ctrl:
                                widget.setEnabled(ctrl.get_status())
                                ctrl.checkbox.stateChanged.connect(
                                    lambda state, w=widget: w.setEnabled(state == Qt.CheckState.Checked.value)
                                )
        host_layout.addStretch()
        return host_layout
    
    def _create_widget(self,widget_info):
        widget=None
        if widget_info['type']=='checkmark':
            widget=SettingsAssets.Checkbox(widget_info['label'], widget_info['caption'])
        elif widget_info['type']=='editable list':
            widget=SettingsAssets.ListWidget(title=widget_info['label'], caption=widget_info['caption'])
        elif widget_info['type']=='radio select':
            widget=SettingsAssets.RadioSelector(options=widget_info['options'], title=widget_info.get('label'))
        elif widget_info['type']=='drag order list':
            widget=SettingsAssets.DraggableOrderList()
        elif widget_info['type']=='section label':
            widget=SettingsAssets.SectionLabel(widget_info['label'], widget_info.get('caption'))

        if widget:
            if 'name' in widget_info:
                widget.set_status(self.config_file_json[widget_info['name']])
                self.name_to_widget_map[widget_info['name']]=widget
            return widget
        else:
            return


# ── VoiceOver animated indicator ─────────────────────────────────────────────

class VoiceOverIndicator(QWidget):
    """
    Jarvis-style arc animation for VoiceOver mode.

    Three concentric partial arcs rotate independently (middle one counter-
    clockwise) with speed and colour changing per state:
        'listening'  — slow blue arcs + pulsing centre dot
        'processing' — fast yellow arcs
        'heard'      — brief green flash, then back to listening speed
        'error'      — red arcs, stop rotating
    """

    _ARC_SPAN    = 240 * 16       # Qt arc units (1/16 °)
    _RADII       = (7, 11, 15)    # px, inner → outer
    _DIRECTIONS  = (1, -1, 1)     # CW, CCW, CW

    _COLORS = {
        'listening':  (74,  158, 255),   # accent blue
        'processing': (243, 156,  18),   # amber
        'heard':      (46,  204, 113),   # green
        'error':      (231,  76,  60),   # red
    }
    _SPEEDS = {                          # °/frame per arc (inner, mid, outer)
        'listening':  (0.6, 0.9, 0.4),
        'processing': (3.5, 5.0, 2.5),
        'heard':      (1.2, 1.8, 0.8),
        'error':      (0.0, 0.0, 0.0),
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._state  = 'listening'
        self._angles = [0.0, 120.0, 240.0]   # staggered start angles
        self._pulse  = 0.0                    # 0–2π for centre dot pulse
        self._heard_t = 0.0                   # countdown after 'heard'

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(33)                 # ~30 fps

        # Size: arc circle (36 px) + gap + label
        self.setFixedHeight(36)
        self._label_text = 'Listening...'

    def set_state(self, state: str, label: str = ''):
        self._state = state
        self._label_text = label
        if state == 'heard':
            self._heard_t = 18              # ~0.6 s at 30 fps, then back to listening
        self.update()

    def _tick(self):
        speeds = self._SPEEDS.get(self._state, (0, 0, 0))
        for i, (speed, direction) in enumerate(zip(speeds, self._DIRECTIONS)):
            self._angles[i] = (self._angles[i] + speed * direction) % 360

        self._pulse = (self._pulse + 0.08) % (2 * math.pi)

        if self._heard_t > 0:
            self._heard_t -= 1
            if self._heard_t == 0:
                self._state = 'listening'
                self._label_text = 'Listening...'

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        h  = self.height()
        r_outer = self._RADII[-1]
        cx = r_outer + 2          # circle centre x
        cy = h // 2

        r, g, b = self._COLORS.get(self._state, (74, 158, 255))

        # ── Arcs ─────────────────────────────────────────────────────
        alphas = (220, 160, 100)
        widths = (2.0, 1.5, 1.0)
        for i, (radius, alpha, width) in enumerate(zip(self._RADII, alphas, widths)):
            pen = QPen(QColor(r, g, b, alpha), width)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            start_angle = int(self._angles[i] * 16)
            rect = QRect(cx - radius, cy - radius, radius * 2, radius * 2)
            painter.drawArc(rect, start_angle, self._ARC_SPAN)

        # ── Centre dot (pulses in size) ───────────────────────────────
        pulse_r = 2.5 + 1.0 * (math.sin(self._pulse) * 0.5 + 0.5)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(r, g, b, 230))
        painter.drawEllipse(
            QRectF(cx - pulse_r, cy - pulse_r, pulse_r * 2, pulse_r * 2))

        # ── Label ────────────────────────────────────────────────────
        if self._label_text:
            text_x = cx + r_outer + 10
            painter.setPen(QColor(Theme.TXT_SOFT))
            font = painter.font()
            font.setPointSize(11)
            font.setWeight(QFont.Weight.Medium)
            painter.setFont(font)
            painter.drawText(
                QRect(text_x, 0, self.width() - text_x, h),
                Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                self._label_text,
            )

    def sizeHint(self):
        fm = self.fontMetrics()
        text_w = fm.horizontalAdvance(self._label_text) + 10
        return QSize(self._RADII[-1] * 2 + 14 + text_w, 36)