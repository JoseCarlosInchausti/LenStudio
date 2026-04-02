from PyQt6.QtWidgets import QWidget,QComboBox,QPushButton, QMessageBox, QLineEdit, QLabel, QHBoxLayout, QVBoxLayout, QListWidget,QCheckBox,QTextEdit,QFrame,QGroupBox,QStackedWidget
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
