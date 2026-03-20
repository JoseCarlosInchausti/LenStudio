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
        self.GRAPHICS_ADDRESSES = {"taskbar icon":"Graphics/4x/Logo.png","open csv unclicked":"Graphics/Buttons/1x/Asset 9.png","open csv clicked":"Graphics/Buttons/1x/Asset 10.png",
                                   "large app icon":"Graphics/Icons/SVG/SVG/Asset 13.svg","small app icon":"Graphics/SVG/Asset 19.svg", #"small app icon":"Graphics/Icons/SVG/Asset 3.svg",
                                   "return home unclicked":"Graphics/Buttons/1x/Asset 4.png","return home clicked":"Graphics/Buttons/1x/Asset 7.png",
                                   "start inspection unclicked":"Graphics/Buttons/1x/Asset 5.png","start inspection clicked":"Graphics/Buttons/1x/Asset 8.png",
                                   "inspection background":"Graphics/Icons/SVG/SVG/Asset 14.svg",
                                   "next image unclicked":"Graphics/SVG/Asset 21.svg","next image clicked":"Graphics/SVG/Asset 21.svg",
                                   "previous image unclicked":"Graphics/SVG/Asset 22.svg","previous image clicked":"Graphics/SVG/Asset 22.svg"}
        self.FONT_SIZES = {"input box labels":15}
        self.csv_path = '/Users/joseinchausti/Desktop/DR2_knowns copy_v36.csv'
        self.inspection_parameters = {'grader name': 'JI', 'ra column name': 'Ra', 'dec column name': 'Dec', 'additional columns': None, 'new df name': 'DR2_knowns copy_v37', 'save directory': '/Users/joseinchausti/Desktop'}
        self.load_csv()

        super().__init__()
        self.setWindowTitle(self.APP_NAME)
        self.setGeometry(100, 100, 1000, 800)

        # Create stack of widgets
        self.stacked_widget = QStackedWidget()
        StudioScreen = StudioScreenWidget(self)
        StudioScreen.set_up_inspection_layout()
        self.stacked_widget.addWidget(StudioScreen)

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
        else:
            if index == 0:
                self.stacked_widget.addWidget(LoadDataWidget(self))
            elif index == 1:
                self.stacked_widget.addWidget(PreInspectionWidget(self))
            elif index == 2:
                StudioScreen = StudioScreenWidget(self)
                StudioScreen.set_up_inspection_layout()
                self.stacked_widget.addWidget(StudioScreen)
                
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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LenStudio()
    app.setApplicationName("A")
    app.setWindowIcon(QIcon(window.GRAPHICS_ADDRESSES['taskbar icon']))
    window.show()
    sys.exit(app.exec())