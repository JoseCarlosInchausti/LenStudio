from PyQt6.QtWidgets import QSpacerItem,QWidget, QVBoxLayout,QHBoxLayout, QLabel, QFileDialog, QSizePolicy
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from Assets import ClickEffectButton, SvgWidget, show_popup_window

class LoadDataWidget(QWidget):
    def __init__(self,main_window):
        super().__init__()
        self.main_window=main_window

        self.page_layout = QVBoxLayout()
        self.page_layout.addStretch()
        self.add_logo_to_layout()
        self.page_layout.addSpacerItem(QSpacerItem(30,30,QSizePolicy.Policy.Minimum,QSizePolicy.Policy.Minimum))
        self.add_text("Welcome to LenStudio",size=30,bold=True)
        self.add_text("To start or open an inspection, please load a CSV file",size=15,bold=False)
        self.add_button()
        self.page_layout.addStretch()
        self.setLayout(self.page_layout)

    def add_logo_to_layout(self):
        logo = SvgWidget(self.main_window.GRAPHICS_ADDRESSES['large app icon'])
        logo.setFixedSize(110,110)
        layout = QHBoxLayout()
        layout.addStretch(), layout.addWidget(logo), layout.addStretch()
        self.page_layout.addLayout(layout)

    def add_text(self,text,size,bold=False):
        label = QLabel(text)
        font = QFont()
        if bold:
            font.setWeight(QFont.Weight.Bold)
        else:
            font.setWeight(QFont.Weight.Normal)
        font.setPointSize(size)
        label.setFont(font)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("color: white;")
        self.page_layout.addWidget(label)

    def add_button(self):
        button = ClickEffectButton(self.main_window.GRAPHICS_ADDRESSES['open csv unclicked'],self.main_window.GRAPHICS_ADDRESSES['open csv clicked'],size1=200, size2=100)
        button.clicked.connect(self.open_file_browser)

        wrapper_layout = QVBoxLayout()
        wrapper_layout.addWidget(button)

        wrapper_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.page_layout.addLayout(wrapper_layout)

    def open_file_browser(self):
        self.file_path, _ = QFileDialog.getOpenFileName(self, "Select a File")
        self.validate_file_path()
        
    def validate_file_path(self):
        if self.file_path[-3:] == 'csv':
            self.main_window.csv_path = self.file_path
            self.main_window.load_csv()
            self.main_window.switch_screens(1)
        else:
            show_popup_window(title='Error',text='Please select a .CSV file',header_icon_path=self.main_window.GRAPHICS_ADDRESSES['small app logo'])


