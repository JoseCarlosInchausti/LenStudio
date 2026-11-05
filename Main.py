from PyQt6.QtWidgets import QApplication, QStackedWidget, QMainWindow
from PyQt6.QtGui import QIcon
import sys
import pandas as pd
from LoadDataScreen import LoadDataWidget
from PreInspectionScreen import PreInspectionWidget
from StudioScreen import StudioScreenWidget

class LenStudio(QMainWindow):
    def __init__(self):
        # Set up parameters
        self.APP_NAME = "LenStudio"
        self.GRAPHICS_ADDRESSES = {"taskbar icon": "assets/logo.png",
                                   "large app icon": "assets/logo.svg"}
        self.FONT_SIZES = {"input box labels":15}
        self.COLOR_PALETTE = {"frame background":'#152238'}
        self.csv_path = None
        self.inspection_parameters = None

        super().__init__()
        self.setWindowTitle(self.APP_NAME)

        screen = QApplication.primaryScreen().availableGeometry()
        w = min(max(int(screen.width()  * 0.80), 1000), 1600)
        h = min(max(int(screen.height() * 0.85), 800),  1100)
        self.resize(w, h)
        self.move(screen.center() - self.rect().center())

        # Create stack of widgets
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.addWidget(LoadDataWidget(self))

        self.setCentralWidget(self.stacked_widget)
        self.stacked_widget.setCurrentIndex(0)

        # Set app appearance:
        self.setStyleSheet("background-color: black;")

    def switch_screens(self,index):
        if index < self.stacked_widget.count():
            if index == 0:
                self.replace_widget(index,LoadDataWidget(self))
            elif index == 1:
                self.replace_widget(index,PreInspectionWidget(self))
            elif index == 2:
                StudioScreen = StudioScreenWidget(self)
                StudioScreen.set_up_inspection_layout()
                self.replace_widget(index,StudioScreen)
                StudioScreen.setFocus()
        else:
            if index == 0:
                self.stacked_widget.addWidget(LoadDataWidget(self))
            elif index == 1:
                self.stacked_widget.addWidget(PreInspectionWidget(self))
            elif index == 2:
                StudioScreen = StudioScreenWidget(self)
                StudioScreen.set_up_inspection_layout()
                self.stacked_widget.addWidget(StudioScreen)
                StudioScreen.setFocus()
                
        self.stacked_widget.setCurrentIndex(index)

    def load_csv(self):
        self.df = pd.read_csv(self.csv_path)
        self.df.reset_index(drop=True,inplace=True)
        self.df_existing_columns = list(self.df.columns)

    def replace_widget(self,index,new_widget):
        old_widget = self.stacked_widget.widget(index)
        self.stacked_widget.removeWidget(old_widget)
        old_widget.deleteLater()
        self.stacked_widget.insertWidget(index, new_widget)

    def closeEvent(self, event):
        studio = self.stacked_widget.currentWidget()
        if hasattr(studio, 'Settings') and bool(studio.Settings.get_setting('confirm_on_close')):
            from Assets import show_branded_dialog
            from Icons import OutlineIcon
            confirmed = show_branded_dialog(
                self, 'Close LenStudio',
                'Any unsaved changes will be lost. Close anyway?',
                icon=OutlineIcon.ALERT_TRIANGLE, icon_bg='#f59e0b',
                confirm=True, yes_label='Close', no_label='Cancel',
            )
            if not confirmed:
                event.ignore()
                return
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LenStudio()
    app.setApplicationName("A")
    app.setWindowIcon(QIcon(window.GRAPHICS_ADDRESSES['taskbar icon']))
    window.show()
    sys.exit(app.exec())