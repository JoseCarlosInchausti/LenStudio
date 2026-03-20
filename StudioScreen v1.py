from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSpacerItem, QSizePolicy
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtCore import QRectF
import numpy as np
from Assets import SvgWidget, ImageWidget, InputField, ClickEffectButton
from InspectionEngine import Inspection,ThreadImageFetcher

class StudioScreenWidget(QWidget):
    def __init__(self,main_window):
        super().__init__()
        self.main_window=main_window

        self.empty_image=np.zeros((101,101))

        self.window_layout = QVBoxLayout()
        self.window_layout.setContentsMargins(15, 5, 15, 10)
        self.top_bar_layout = QHBoxLayout()
        self.top_bar_layout.setContentsMargins(0, 0, 0, 0)
        self.inspection_central_layout = QHBoxLayout()
        self.inspection_central_layout.setSpacing(0)
        self.inspection_central_layout.setContentsMargins(0, 0, 0, 0)
        self.bottom_central_layout = QHBoxLayout()
        top_spacer = QSpacerItem(100, 100)

        self.window_layout.addLayout(self.top_bar_layout),self.window_layout.addSpacerItem(top_spacer),self.window_layout.addLayout(self.inspection_central_layout),self.window_layout.addStretch(),self.window_layout.addLayout(self.bottom_central_layout)

        self.current_inspection = Inspection(self.main_window)
        self.current_inspection.simulation_mode = False

        # Background
        self.setLayout(self.window_layout)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.background_svg = QSvgRenderer(self.main_window.GRAPHICS_ADDRESSES['inspection background'])

        # Top bar
        # Add icon
        app_icon_svg = SvgWidget(self.main_window.GRAPHICS_ADDRESSES["small app icon"])
        self.top_bar_layout.addWidget(app_icon_svg)
        self.top_bar_layout.addStretch()

        # self.window_layout.addStretch()

        # Set up grading area:
        self.set_up_grading_area()
    

    def paintEvent(self, event):
        painter = QPainter(self)
        self.background_svg.render(painter, QRectF(self.rect()))
        super().paintEvent(event)

    def set_up_inspection_layout(self):
        success_dict, data_dict = self.current_inspection.get_current_images(idx=0)

        self.idx_to_band_dict = {0:'g',1:'r',2:'z'}
        self.inspection_central_layout.addStretch()
        self.images_on_layout = {}
        if success_dict['rgb']:
            rgb_image = ImageWidget(data_dict['rgb'])
            rgb_image.setBackground('#2e2e2e')
            self.inspection_central_layout.addWidget(rgb_image)
            self.images_on_layout['rgb'] = rgb_image
        if success_dict['grz']:
            for band in range(3):
                band_image = ImageWidget(data_dict['grz'][band])
                band_image.setBackground('#2e2e2e')
                self.inspection_central_layout.addWidget(band_image)
                self.images_on_layout[self.idx_to_band_dict[band]] = band_image

        self.inspection_central_layout.addStretch()

    def set_up_grading_area(self):
        self.grading_field = InputField(label_text='Grade:',main_window=self.main_window, add_stretch=False)
        self.grading_field.label.setStyleSheet("""
                                        QLabel {
                                                background-color: #2e2e2e;  /* dark gray */
                                                color: white;               /* white text */
                                            }
                                        """)
        self.grading_field.input_field.setMaxLength(1)
        self.grading_field.input_field.setMinimumHeight(40)
        self.comments_field = InputField(label_text='Comment:',main_window=self.main_window, add_stretch=False,multi_line=True)
        self.comments_field.label.setStyleSheet("""
                                        QLabel {
                                                background-color: #2e2e2e;  /* dark gray */
                                                color: white;               /* white text */
                                            }
                                        """)
        self.comments_field.input_field.setFixedHeight(100)
        self.bottom_central_layout.addLayout(self.grading_field,1)
        self.bottom_central_layout.addLayout(self.comments_field,10)
        self.next_button = ClickEffectButton(icon_path_unclicked=self.main_window.GRAPHICS_ADDRESSES['next image unclicked'], icon_path_clicked=self.main_window.GRAPHICS_ADDRESSES['next image clicked'], size1=50, size2=100)
        self.next_button.clicked.connect(lambda:self.change_system(which='next'))
        self.previous_button = ClickEffectButton(icon_path_unclicked=self.main_window.GRAPHICS_ADDRESSES['previous image unclicked'], icon_path_clicked=self.main_window.GRAPHICS_ADDRESSES['previous image clicked'], size1=50, size2=100)
        self.previous_button.clicked.connect(lambda:self.change_system(which='previous'))
        self.button_stack = QVBoxLayout()
        self.button_stack.addWidget(self.next_button), self.button_stack.addWidget(self.previous_button)
        self.bottom_central_layout.addLayout(self.button_stack, 2)
        self.bottom_central_layout.addStretch()

    def change_system(self,which='next'):
        if type(which)==int:
            next_idx = which
        elif which=='next':
            next_idx = self.current_inspection.current_idx+1
        elif which=='previous':
            next_idx = self.current_inspection.current_idx-1
        
        success_dict, data_dict = self.current_inspection.get_current_images(idx=next_idx)
        
        # self.images_on_layout.keys
        if success_dict['rgb']:
            self.images_on_layout['rgb'].update_image(data_dict['rgb'])
        else:
            self.images_on_layout['rgb'].update_image(self.empty_image)
        if success_dict['grz']:
            for band in range(3):
                self.images_on_layout[self.idx_to_band_dict[band]].update_image(data_dict['grz'][band])
        else:
            for band in range(3):
                self.images_on_layout[self.idx_to_band_dict[band]].update_image(self.empty_image)

        self.queue_images()
        
        
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Right:
            self.change_system(which='next')
        elif event.key() == Qt.Key.Key_Left:
            self.change_system(which='previous')
        else:
            super().keyPressEvent(event)

    def queue_images(self):
        prev_next_ras, prev_next_decs, prev_next_idxs = [], [], []

        if not self.current_inspection.is_cached(self.current_inspection.current_idx+1):
            prev_next_ras.append(self.main_window.df[self.current_inspection.ra_col_name].values[self.current_inspection.current_idx+1])
            prev_next_decs.append(self.main_window.df[self.current_inspection.dec_col_name].values[self.current_inspection.current_idx+1])
            prev_next_idxs.append(self.current_inspection.current_idx+1)

        if not self.current_inspection.is_cached(self.current_inspection.current_idx-1):
            prev_next_ras.append(self.main_window.df[self.current_inspection.ra_col_name].values[self.current_inspection.current_idx-1])
            prev_next_decs.append(self.main_window.df[self.current_inspection.dec_col_name].values[self.current_inspection.current_idx-1])
            prev_next_idxs.append(self.current_inspection.current_idx-1)

        if len(prev_next_ras)>0:
            self.cache_fetcher = ThreadImageFetcher(ra=prev_next_ras,dec=prev_next_decs,idxs=prev_next_idxs,inspection_class = self.current_inspection)
            self.cache_fetcher.output.connect(lambda thread_output: self.current_inspection.add_to_cache(list_of_new_images=thread_output[:2],idx=thread_output[2]))
            self.cache_fetcher.start()