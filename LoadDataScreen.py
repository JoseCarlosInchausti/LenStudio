from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFileDialog, QPushButton, QFrame
from PyQt6.QtCore import Qt, QSize
from Assets import SvgWidget, show_popup_window
from Icons import tabler_icon, OutlineIcon, ICON_WHITE

# Palette mirrors the inspection setup page (see PreInspectionScreen.py)
BG       = "#0a1628"
CARD     = "#152238"
BORDER   = "#27364d"
ACCENT   = "#4A9EFF"
TXT      = "#ffffff"
TXT_MUTE = "#8a99b3"


class LoadDataWidget(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        self.setObjectName("loadPage")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(f"""
            QWidget#loadPage {{ background-color: {BG}; }}
            QFrame#welcomeCard {{ background-color: {CARD}; border: 1px solid {BORDER};
                                  border-radius: 16px; }}
            QLabel {{ background: transparent; }}
            QLabel#title    {{ color: {TXT}; font-size: 26px; font-weight: 700; }}
            QLabel#subtitle {{ color: {TXT_MUTE}; font-size: 14px; }}
            QPushButton#cta {{ background: {ACCENT}; color: white; border: none; border-radius: 10px;
                               padding: 12px 34px; font-size: 15px; font-weight: 700; }}
            QPushButton#cta:hover   {{ background: #5fb0ff; }}
            QPushButton#cta:pressed {{ background: #3d8de0; }}
        """)

        outer = QVBoxLayout(self)
        outer.addStretch()
        row = QHBoxLayout()
        row.addStretch()
        row.addWidget(self._build_card())
        row.addStretch()
        outer.addLayout(row)
        outer.addStretch()

    def _build_card(self):
        card = QFrame()
        card.setObjectName("welcomeCard")
        card.setFixedWidth(460)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(48, 44, 48, 44)
        lay.setSpacing(0)

        logo = SvgWidget(self.main_window.GRAPHICS_ADDRESSES['large app icon'])
        logo.setFixedSize(84, 84)
        logo_row = QHBoxLayout()
        logo_row.addStretch()
        logo_row.addWidget(logo)
        logo_row.addStretch()
        lay.addLayout(logo_row)

        lay.addSpacing(22)
        title = QLabel("Welcome to LenStudio")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(title)

        lay.addSpacing(8)
        subtitle = QLabel("To start or open an inspection, load a CSV catalog.")
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setWordWrap(True)
        lay.addWidget(subtitle)

        lay.addSpacing(28)
        button = QPushButton("  Open CSV file")
        button.setObjectName("cta")
        button.setIcon(tabler_icon(OutlineIcon.FILE_TYPE_CSV, size=18, color=ICON_WHITE))
        button.setIconSize(QSize(18, 18))
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.clicked.connect(self.open_file_browser)
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(button)
        btn_row.addStretch()
        lay.addLayout(btn_row)
        return card

    def open_file_browser(self):
        self.file_path, _ = QFileDialog.getOpenFileName(
            self, "Select a CSV file", "", "CSV files (*.csv);;All files (*)")
        if not self.file_path:
            return  # user cancelled
        self.validate_file_path()

    def validate_file_path(self):
        if self.file_path.lower().endswith('.csv'):
            self.main_window.csv_path = self.file_path
            self.main_window.load_csv()
            self.main_window.switch_screens(1)
        else:
            show_popup_window(title='Error', text='Please select a .CSV file', header_icon_path=None)
