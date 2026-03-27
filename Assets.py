from PyQt6.QtWidgets import QWidget,QComboBox,QPushButton, QMessageBox, QLineEdit, QLabel, QHBoxLayout, QVBoxLayout, QListWidget,QCheckBox,QTextEdit,QFrame,QGroupBox
from PyQt6.QtGui import QIcon,QFont,QPixmap, QPainter, QImage, QTextOption, QColor,QCursor
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtCore import QSize, Qt, QRectF,QEvent,pyqtSignal
import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets, QtCore
import numpy as np

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

        DARK_BG = "#0f1c33"

        self.setStyleSheet("""
                            QGroupBox {
                                border: 1px solid lightgray;
                                border-radius: 5px;
                                margin-top: 10px;
                                background-color: #152238;
                            }

                            QGroupBox::title {
                            subcontrol-origin: margin;
                            subcontrol-position: top left;
                            background-color: #152238;
                            color: lightgray;
                            top: -1px;
                            }
                            QLabel {
                            color: white;
                            }
                            """)
    
    def update_content(self,new_text):
        self.label.setText(new_text)

class StyledInputBox(QGroupBox):
    def __init__(self, title, content,caps_lock=False, N_max_lines=None,center_text=False,quick_inspection_check=None):
        super().__init__(title)
        self.quick_inspection_check=quick_inspection_check

        self.caps_lock=caps_lock
        self.greyed_out=False
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 5, 4, 5)
        layout.setSpacing(0)

        self.text_edit = QTextEdit()
        self.center_text=center_text
        self.N_max_lines=N_max_lines
        self.update_text(str(content))
        if self.N_max_lines:
            self.text_edit.textChanged.connect(self._enforce_max_lines)
        if self.center_text:
            self.text_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text_edit.setWordWrapMode(QTextOption.WrapMode.WordWrap)
        self.text_edit.setFrameShape(QTextEdit.Shape.NoFrame)  # removes inner border
        
        if caps_lock:
            self.text_edit.textChanged.connect(self._force_uppercase)        
        layout.addWidget(self.text_edit)

        self.setStyleSheet("""
            QGroupBox {
                border: 1px solid lightgray;
                border-radius: 5px;
                margin-top: 10px;
                background-color: #152238;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                background-color: #152238;
                color: lightgray;
                top: -1px;
            }
            QTextEdit {
                color: white;
                background-color: #152238;
            }
            QTextEdit:focus {
                border: 1px solid #4A9EFF;
                border-radius: 3px;
            }
        """)
        self._set_line_count()

    # def eventFilter(self,obj,event):
    #     if obj == self.text_edit:
    #         quick_inspection_active = self.quick_inspection_check() if self.quick_inspection_check else False
    #         if event.type() == QEvent.Type.FocusIn and quick_inspection_active:
    #             self._set_border(with_focus_outline=True)
    #         elif event.type() == QEvent.Type.FocusOut:
    #             self._set_border(with_focus_outline=False)
    #     return super().eventFilter(obj, event)
    
    def _set_border(self,with_focus_outline):
        if with_focus_outline:
            self.setStyleSheet("""
                                QGroupBox {
                                    border: 1px solid lightgray;
                                    border-radius: 5px;
                                    margin-top: 10px;
                                    background-color: #152238;
                                }
                                QGroupBox::title {
                                    subcontrol-origin: margin;
                                    subcontrol-position: top left;
                                    background-color: #152238;
                                    color: lightgray;
                                    top: -1px;
                                }
                                QTextEdit {
                                    color: white;
                                    background-color: #152238;
                                }
                                QTextEdit:focus {
                                    border: 1px solid #4A9EFF;
                                    border-radius: 3px;
                                }
                                """)
        else:
            self.setStyleSheet("""
                    QGroupBox {
                        border: 1px solid lightgray;
                        border-radius: 5px;
                        margin-top: 10px;
                        background-color: #152238;
                    }
                    QGroupBox::title {
                        subcontrol-origin: margin;
                        subcontrol-position: top left;
                        background-color: #152238;
                        color: lightgray;
                        top: -1px;
                    }
                    QTextEdit {
                        color: white;
                        background-color: #152238;
                    }
                    """)

    def disable_input(self,grey_out=True):
        self.text_edit.setReadOnly(True)
        if grey_out:
            self.setStyleSheet("""
                QGroupBox {
                    border: 1px solid lightgray;
                    border-radius: 5px;
                    margin-top: 10px;
                    background-color: #152238;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    subcontrol-position: top left;
                    background-color: #152238;
                    color: lightgray;
                    top: -1px;
                }
                QTextEdit {
                    color: lightgray;
                    background-color: #152238;
                }
            """)
            self.greyed_out=True
    
    def enable_input(self):
        self.text_edit.setReadOnly(False)
        if self.greyed_out:
            self.setStyleSheet("""
            QGroupBox {
                border: 1px solid lightgray;
                border-radius: 5px;
                margin-top: 10px;
                background-color: #152238;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                background-color: #152238;
                color: lightgray;
                top: -1px;
            }
            QTextEdit {
                color: white;
                background-color: #152238;
            }
            """)

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

    def change_input_size(self,new_size):
        font = QFont()
        font.setPointSize(int(new_size))
        self.text_edit.setFont(font)

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
            active_style = """
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
                }
                QPushButton:focus {
                    border: 3px solid #4A9EFF;
                    border-radius: 8px;
                }
            """
        else:
            active_style = """
                QPushButton {
                    background-color: white;
                    border-radius: 8px;
                    color: #152238;
                    font-size: 16px;
                    font-weight: 600;
                    padding: 3px 9px;
                }
                QPushButton:hover {
                    background-color: #f0ffff;
                }
                QPushButton:pressed {
                    background-color: #f0f8ff;
                    padding-top: 2px;
                    padding-left: 2px;
                }
                QPushButton:focus {
                    border: 3px solid #4A9EFF;
                    border-radius: 8px;
                }
            """   
        inactive_style = """
            QPushButton {
                background-color: #d3d3d3;
                border-radius: 8px;
                color: #4a4a4a;
                font-size: 16px;
                font-weight: 600;
                padding: 3px 9px;
            }
            QPushButton:hover {
                background-color: #dcdcdc;
            }
            QPushButton:pressed {
                background-color: #c8c8c8;
                padding-top: 2px;
                padding-left: 2px;
            }
            QPushButton:focus {
                border: 3px solid #4A9EFF;
                border-radius: 8px;
            }
        """
        for name, btn in self.buttons.items():
            btn.setStyleSheet(active_style if name == self.active_tab else inactive_style)