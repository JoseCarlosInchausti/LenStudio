from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSpacerItem, QSizePolicy,QGridLayout,QApplication, QStackedWidget,QLabel,QMessageBox,QFrame,QGraphicsDropShadowEffect,QComboBox,QStyledItemDelegate,QDialog,QPushButton
from PyQt6.QtCore import Qt, QUrl,QThread, pyqtSignal, QEvent, QPropertyAnimation, QParallelAnimationGroup, QEasingCurve, QPoint, QSize, QTimer
from PyQt6.QtGui import QPainter, QDesktopServices, QColor
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtCore import QRectF

import numpy as np
import time
# from Assets import SvgWidget, ImageWidget, InputField, ClickEffectButton
from Assets import Panel,SvgWidget, ImageWidget, StyledTextBox, MetadataField, ClickEffectStyleButton, StyledText, StyledInputBox,StatusWidget,CheckBox,StyledTabBar,InspectionSettings,ScrollPanel,StyledGroupBox,VoiceOverIndicator
from InspectionEngine import Inspection,ThreadImageFetcher
import Theme
from Icons import tabler_icon, tabler_pixmap, badge_pixmap, OutlineIcon, ICON_WHITE, ICON_SOFT
from VoiceOverEngine import VoiceOverThread

PRIMARY_BTN = f"""
QPushButton {{ background-color:{Theme.ACCENT}; color:white; border:none; border-radius:8px;
               font-size:14px; font-weight:700; }}
QPushButton:hover {{ background-color:{Theme.ACCENT_HI}; }}
QPushButton:pressed {{ background-color:{Theme.ACCENT_LO}; }}
QPushButton:disabled {{ background-color:#24405f; color:#5c6b85; }}
"""
GHOST_BTN = f"""
QPushButton {{ background-color:transparent; color:{Theme.TXT_SOFT}; border:1px solid #33425c;
               border-radius:8px; font-size:14px; font-weight:600; }}
QPushButton:hover {{ background-color:#17273f; color:white; }}
QPushButton:disabled {{ color:#51607a; border-color:#263549; }}
"""
SECONDARY_BTN = f"""
QPushButton {{ background-color:#1c2a42; color:{Theme.TXT}; border:1px solid #33425c;
               border-radius:8px; font-size:13px; font-weight:600; }}
QPushButton:hover {{ background-color:#243a5a; }}
QPushButton:pressed {{ background-color:#182942; }}
"""
CHECKBOX_QSS = f"""
QCheckBox {{ color:{Theme.TXT_SOFT}; font-size:14px; spacing:8px; background:transparent; padding:4px 6px; }}
QCheckBox::indicator {{ width:18px; height:18px; border:1px solid {Theme.FIELD_BRD};
                        border-radius:4px; background:{Theme.FIELD}; }}
QCheckBox::indicator:checked {{ background:{Theme.ACCENT}; border-color:{Theme.ACCENT}; }}
"""

class StudioScreenWidget(QWidget):
    def __init__(self,main_window):
        super().__init__()
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setObjectName("studioScreen")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(f"QWidget#studioScreen {{ background-color: {Theme.BG}; }}")

        self.Settings = InspectionSettings("JSON-for-settings-design-format.txt", "settings-state.txt")

        self.current_idx = 0
        self.main_window=main_window

        self.animating = False
        self.current_screen = "inspection"

        self.save_csv_worker=None

        self.window_layout = QVBoxLayout()
        self.window_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.window_layout)
        self.N_total_systems = len(self.main_window.df)

        self.panels_layout = QHBoxLayout()
        self.panels_layout.setContentsMargins(5, 0, 5, 0) #l, up, r, down

        self.metadata_panel = Panel()
        self.metadata_panel.add_title(title='Metadata',center_title=False)
        self.imaging_data_panel = Panel()
        self.imaging_data_panel.add_title(title='Imaging Data',center_title=False)
        self.inspector_input_panel = Panel()
        self.inspector_input_panel.add_title(title='Inspector Input',center_title=False)

        self.top_panel = Panel(border_radius=0,vertical=False)
        self.top_panel.layout.setContentsMargins(14, 4, 14, 4)
        self.top_panel.setMaximumHeight(46)
        self.bottom_panel = Panel(border_radius=0,vertical=False)
        # logo = SvgWidget(self.main_window.GRAPHICS_ADDRESSES['large app icon'])
        # logo.setFixedSize(40,40)

        #Buttons:
        self.next_system_button = ClickEffectStyleButton(text='Next', size=(150, 36))
        self.next_system_button.setStyleSheet(PRIMARY_BTN)
        self.next_system_button.setIcon(tabler_icon(OutlineIcon.ARROW_RIGHT, size=15, color=ICON_WHITE))
        self.next_system_button.setIconSize(QSize(15, 15))
        self.next_system_button.setLayoutDirection(Qt.LayoutDirection.RightToLeft)  # arrow on the right
        self.next_system_button.clicked.connect(self.load_next_system)
        self.next_system_button.setAutoDefault(True) #To have button respond to enter during quick inspection
        self.previous_system_button = ClickEffectStyleButton(text='Previous', size=(150, 36))
        self.previous_system_button.setStyleSheet(GHOST_BTN)
        self.previous_system_button.setIcon(tabler_icon(OutlineIcon.ARROW_LEFT, size=15, color=ICON_SOFT))
        self.previous_system_button.setIconSize(QSize(15, 15))
        self.previous_system_button.setEnabled(False)
        self.previous_system_button.clicked.connect(self.load_previous_system)

        #Inspection optional features:
        self.lock_inspection_checkbox = CheckBox("Lock Grades and Comments",self.main_window)
        self.lock_inspection_checkbox.checkbox.setStyleSheet(CHECKBOX_QSS)
        self.quick_inspection_checkbox = CheckBox("Quick Inspection Mode",self.main_window)
        self.quick_inspection_checkbox.checkbox.setStyleSheet(CHECKBOX_QSS)
        self.voiceover_checkbox = CheckBox("VoiceOver Mode",self.main_window)
        self.voiceover_checkbox.checkbox.setStyleSheet(CHECKBOX_QSS)
        # self.lock_inspection_toggle = StyledToggleSwitch("Lock Grades & Comments")

        # Labels:
        self.system_N_tracker = StyledText()
        self.save_status_widget = StatusWidget(text='Autosaving on', color='green', dot_size=12)

        #Add items to bottom panel
        self.bottom_panel.add_widget(self.previous_system_button)
        # self.bottom_panel.add_widget(logo,stretch=(True,True))
        self.bottom_panel.add_widget(self.lock_inspection_checkbox.checkbox)
        self.bottom_panel.add_widget(self.quick_inspection_checkbox.checkbox)
        self.bottom_panel.add_widget(self.voiceover_checkbox.checkbox)
        self.bottom_panel.add_widget(self.next_system_button)

        #Add items to top panel
        self.top_panel.add_widget(self.save_status_widget,stretch=(False,True))
        self.top_panel.add_widget(self.system_N_tracker,stretch=(False,True))

        # VoiceOver status — inserted at index 1 so it sits next to autosave when visible
        self.voiceover_status_widget = VoiceOverIndicator()
        self.voiceover_status_widget.hide()

        #Clipping widget for animated transitions:
        self.clipper = QWidget()
        self.clipper.setStyleSheet(f"background-color: {Theme.BG};")

        for panel,stretch_factor in zip([self.metadata_panel,self.imaging_data_panel,self.inspector_input_panel],(5,9,6)):
            self.panels_layout.addWidget(panel,stretch_factor)
        self.panels_container_widget = QWidget(self.clipper)
        self.panels_container_widget.setStyleSheet("background-color: transparent;")
        self.panels_container_widget.setLayout(self.panels_layout)

        self.window_layout.addWidget(self.top_panel,1)
        # self.window_layout.addWidget(self.panels_container_widget,20)
        self.window_layout.addWidget(self.clipper, 20)
        self.window_layout.addWidget(self.bottom_panel,2)

        # Settings window:
        self._create_settings_window()

        #Inspection (non-GUI)
        self.current_inspection = Inspection(self.main_window)
        self.current_inspection.simulation_mode = False
        self.CSV_save_path = self.current_inspection.inspection_parameters['save directory']+f'/{self.current_inspection.inspection_parameters['new df name']}.csv'

        # Place-holder of screens for animation:
        self.screen_name_to_container = {'inspection':self.panels_container_widget, 'settings':self.settings_layout_container_widget}
        self.screen_orders = {'inspection':0, 'settings':1}

        self.screen_switch_tab_bar = StyledTabBar({'Studio':'inspection','Settings':'settings'})
        self.screen_switch_tab_bar.tab_clicked.connect(self._switch_screens)
        self.top_panel.add_widget(self.screen_switch_tab_bar,stretch=(False,False))
        # Place voiceover status right after autosave widget (index 1 in horizontal layout)
        self.top_panel.layout.insertWidget(1, self.voiceover_status_widget)
        
    def _switch_screens(self,to_screen='settings'):
        if self.animating:
            return
        self.to_screen=to_screen
        self.screen_in, self.screen_out = self.screen_name_to_container[to_screen], self.screen_name_to_container[self.current_screen]
        self.animating = True

        if self.screen_orders[self.current_screen] < self.screen_orders[to_screen]:
            out_end = -self.clipper.width()
            in_start = self.clipper.width()
        else:
            out_end = self.clipper.width()
            in_start = -self.clipper.width()

        anim_out = QPropertyAnimation(self.screen_out, b"pos")
        anim_out.setDuration(400)
        anim_out.setStartValue(QPoint(0, 0))
        anim_out.setEndValue(QPoint(out_end, 0))
        anim_out.setEasingCurve(QEasingCurve.Type.InOutCubic)

        animate_bottom_panel=(self.current_screen == 'inspection' or to_screen == 'inspection')

        if animate_bottom_panel:
            anim_bottom = QPropertyAnimation(self.bottom_panel, b"maximumHeight")
            anim_bottom.setDuration(400)
            anim_bottom.setEasingCurve(QEasingCurve.Type.InOutCubic)
            bottom_height = self.bottom_panel.sizeHint().height()
            if self.current_screen=='inspection':
                anim_bottom.setStartValue(bottom_height)
                anim_bottom.setEndValue(0)
            else:
                anim_bottom.setStartValue(0)
                anim_bottom.setEndValue(bottom_height)

        self.screen_in.move(self.clipper.width(), 0)
        anim_in = QPropertyAnimation(self.screen_in, b"pos")
        anim_in.setDuration(400)
        anim_in.setStartValue(QPoint(in_start, 0))
        anim_in.setEndValue(QPoint(0, 0))
        anim_in.setEasingCurve(QEasingCurve.Type.InOutCubic)

        self.slide_group = QParallelAnimationGroup()
        self.slide_group.addAnimation(anim_out)
        self.slide_group.addAnimation(anim_in)
        if animate_bottom_panel:
            self.slide_group.addAnimation(anim_bottom)
            self.system_N_tracker.hide()
            self.save_status_widget.hide()
        self.slide_group.finished.connect(self._on_slide_finished)
        self.slide_group.start()

        #If leaving settings, update config file
        self.Settings.update_config_file()
        
    def _on_slide_finished(self):
        # self.screen_out.hide()
        self.animating = False
        self.current_screen = self.to_screen
        if self.to_screen == 'inspection':
            self.bottom_panel.setMaximumHeight(16777215)  # Qt's QWIDGETSIZE_MAX
            self.system_N_tracker.show()
            self.save_status_widget.show()
            self._apply_caps_lock_settings()
            self._rebuild_focus_order()
            if hasattr(self, 'vo_thread') and self.voiceover_checkbox.checkbox.isChecked():
                self.vo_thread.start_listening()
                self._vo_idle_timer.start()
        elif self.to_screen == 'settings':
            if hasattr(self, 'vo_thread'):
                self.vo_thread.stop_listening()
                self._vo_idle_timer.stop()
                self.voiceover_status_widget.hide()

    def _build_info_tab(self):
        import SettingsAssets
        return SettingsAssets.InfoPage()

    def _create_settings_window(self):
        self.dict_of_settings_menus = {tab_name:str(int(tab_i)) for tab_i, tab_name in enumerate(self.Settings.tabs_names)}
        # Append the static Info tab after the JSON-driven tabs
        self.dict_of_settings_menus['Info'] = str(len(self.Settings.tabs_names))
        self.list_settings_menus_names = list(self.dict_of_settings_menus.keys())
    
        self.settings_layout = QHBoxLayout()

        self.settings_left_panel = Panel()
        self.settings_left_panel.add_title(title='Options',center_title=False)
        self.settings_layout.addWidget(self.settings_left_panel,1)

        # self.settings_right_panel = Panel() # Not scrollable
        self.settings_right_panel = ScrollPanel()
        self.settings_right_panel.add_title(title=self.list_settings_menus_names[0]+' Settings',center_title=False)
        self.settings_layout.addWidget(self.settings_right_panel,5)
        self.stacked_settings_widget = self.Settings.get_stacked_widget()
        self.stacked_settings_widget.addWidget(self._build_info_tab())
        self.settings_right_panel.add_widget(self.stacked_settings_widget)

        self.settings_layout_container_widget=QWidget(self.clipper)
        self.settings_layout_container_widget.setStyleSheet("background-color: transparent;")
        self.settings_layout_container_widget.setLayout(self.settings_layout)

        #Populate the panels:
        self.settings_menu_tabs = StyledTabBar(self.dict_of_settings_menus,
                                               orientation='vertical',
                                               add_stretches=True)
        self.settings_menu_tabs.tab_clicked.connect(self._switch_setting_menu)
        self.settings_left_panel.add_widget(self.settings_menu_tabs,stretch=(False,True))

    def _switch_setting_menu(self,new_menu_index):
        new_menu_index = int(new_menu_index)
        tab_name = self.list_settings_menus_names[new_menu_index]
        title = 'About & Attribution' if tab_name == 'Info' else tab_name + ' Settings'
        self.settings_right_panel.change_title(title)
        self.stacked_settings_widget.setCurrentIndex(new_menu_index)

    def resizeEvent(self, event):
        '''
        Rewrites the resizeEvent function to set the size of the clipper widget for animations
        Also sets the settings layout out-of-screen
        '''
        super().resizeEvent(event)
        self.panels_container_widget.setGeometry(self.clipper.rect())
        self.settings_layout_container_widget.setGeometry(
            self.clipper.width(), 0,
            self.clipper.width(), self.clipper.height()+self.bottom_panel.height()
        )

    def _tag_image(self, image_widget, text):
        """Overlay a small band/label pill on the top-left of an image cutout."""
        tag = QLabel(text, image_widget)
        tag.setStyleSheet(
            "QLabel { background-color: rgba(10,22,40,0.82); color:#e8edf5;"
            " font-size:11px; font-weight:700; border-radius:5px; padding:2px 7px; }")
        tag.move(6, 6)
        tag.adjustSize()
        tag.raise_()

    def _frame_image(self, image_widget, tag_text):
        """Wrap an image cutout in a soft-edged rounded matte frame and tag it."""
        frame = QFrame()
        frame.setObjectName("imgFrame")
        frame.setStyleSheet(
            f"QFrame#imgFrame {{ background-color:#1b2b47; border:1px solid #33425c;"
            f" border-radius:12px; }}")
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(6, 6, 6, 6)
        lay.addWidget(image_widget)
        # Hug the fixed-size image (margins 6*2 + border 1*2) so the matte is symmetric
        frame.setFixedSize(image_widget.minimumWidth() + 14, image_widget.minimumHeight() + 14)
        shadow = QGraphicsDropShadowEffect(frame)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 140))
        shadow.setOffset(0, 3)
        frame.setGraphicsEffect(shadow)
        self._tag_image(image_widget, tag_text)
        return frame

    def _make_blank_overlay(self, image_widget):
        """Overlay that appears on a cutout when the returned image is uniform (out of footprint)."""
        overlay = QLabel("Not in\nfootprint", image_widget)
        overlay.setObjectName("blankOverlay")
        overlay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        overlay.setStyleSheet(
            "QLabel { background-color: rgba(10,22,40,0.88); color:#8a99b3;"
            " font-size:11px; font-weight:700; border-radius:8px; }")
        overlay.resize(image_widget.size())
        overlay.raise_()
        overlay.hide()
        return overlay

    def _change_survey(self, dr_label):
        """Switch cutout source (DR9/DR10/DR11) and refresh the current system."""
        self.current_inspection.set_survey(dr_label)          # clears cache
        self.survey_box.update_content(self.current_inspection.inspection_parameters['survey'])
        self.url_current_system = self.current_inspection.get_current_url()
        success_dict, data_dict = self.current_inspection.get_current_images(idx=self.current_idx)
        if success_dict['rgb']:
            self.images_on_layout['rgb'].update_image(data_dict['rgb'])
        if success_dict['grz']:
            for band in range(3):
                self.images_on_layout[self.idx_to_band_dict[band]].update_image(data_dict['grz'][band])
        self._update_blank_overlays(success_dict, data_dict)

    def _update_blank_overlays(self, success_dict, data_dict):
        """Show/hide per-image blank overlays based on fetch success and pixel uniformity."""
        if 'rgb' in self.blank_overlays:
            if not success_dict['rgb']:
                self.blank_overlays['rgb'].show()
            else:
                self.blank_overlays['rgb'].setVisible(
                    self.current_inspection._is_blank(data_dict['rgb']))
        if success_dict['grz'] and data_dict['grz'] is not None:
            for band in range(3):
                band_key = self.idx_to_band_dict[band]
                if band_key in self.blank_overlays:
                    self.blank_overlays[band_key].setVisible(
                        self.current_inspection._is_blank(data_dict['grz'][band]))
        else:
            for band_key in ['g', 'r', 'z']:
                if band_key in self.blank_overlays:
                    self.blank_overlays[band_key].show()

    def set_up_inspection_layout(self):
        #Images:
        success_dict, data_dict = self.current_inspection.get_current_images(idx=0)

        self.idx_to_band_dict = {0:'g',1:'r',2:'z'}
        self.images_on_layout = {}
        #Pyramid layout
        # if success_dict['rgb']:
        #     rgb_image = ImageWidget(data_dict['rgb'])
        #     rgb_layout = QHBoxLayout()
        #     rgb_layout.addStretch(),rgb_layout.addWidget(rgb_image),rgb_layout.addStretch()
        #     self.imaging_data_panel.add_layout(rgb_layout)
        #     self.images_on_layout['rgb'] = rgb_image
        # if success_dict['grz']:
        #     grz_layout = QHBoxLayout()
        #     grz_layout.addStretch()
        #     for band in range(3):
        #         band_image = ImageWidget(data_dict['grz'][band])
        #         grz_layout.addWidget(band_image)
        #         self.images_on_layout[self.idx_to_band_dict[band]] = band_image
        #     grz_layout.addStretch()
        #     self.imaging_data_panel.add_layout(grz_layout)
        # Grid layout
        grid_layout = QGridLayout()
        grid_layout.setSpacing(14)  # room for the soft shadows
        grid_layout.setColumnStretch(0, 1)
        grid_layout.setColumnStretch(1, 3)
        small_cutout_panel_size = 120
        self.blank_overlays = {}
        if success_dict['grz']:
            for band in range(3):
                band_key = self.idx_to_band_dict[band]
                band_image = ImageWidget(data_dict['grz'][band], panel_size=(small_cutout_panel_size, small_cutout_panel_size))
                grid_layout.addWidget(self._frame_image(band_image, band_key), band, 0, alignment=Qt.AlignmentFlag.AlignCenter)
                self.images_on_layout[band_key] = band_image
                self.blank_overlays[band_key] = self._make_blank_overlay(band_image)
                self.blank_overlays[band_key].setVisible(self.current_inspection._is_blank(data_dict['grz'][band]))
        if success_dict['rgb']:
            rgb_image = ImageWidget(data_dict['rgb'], panel_size=(3*small_cutout_panel_size, 3*small_cutout_panel_size))
            grid_layout.addWidget(self._frame_image(rgb_image, 'RGB'), 0, 1, 3, 1, alignment=Qt.AlignmentFlag.AlignCenter)
            self.images_on_layout['rgb'] = rgb_image
            self.blank_overlays['rgb'] = self._make_blank_overlay(rgb_image)
            self.blank_overlays['rgb'].setVisible(self.current_inspection._is_blank(data_dict['rgb']))
        self.imaging_data_panel.layout.addStretch()
        self.imaging_data_panel.add_layout(grid_layout)
        self.imaging_data_panel.layout.addStretch()

        # Add "open sky viewer button" + DR source dropdown
        self.url_current_system = self.current_inspection.get_current_url()
        self.sky_viewer_buttons_layout = QHBoxLayout()
        self.sky_viewer_buttons_layout.setSpacing(6)

        # DR source — "Survey" label to the left, combo to the right
        dr_group = QWidget()
        dr_group.setStyleSheet("background: transparent;")
        dr_hbox = QHBoxLayout(dr_group)
        dr_hbox.setContentsMargins(0, 0, 0, 0)
        dr_hbox.setSpacing(8)

        dr_label = QLabel("Survey")
        dr_label.setStyleSheet(
            f"color:{Theme.TXT_SOFT}; font-size:13px; font-weight:600;"
            f" background:transparent;")

        self.dr_dropdown = QComboBox()
        self.dr_dropdown.addItems(['DR9', 'DR10', 'DR11'])
        self.dr_dropdown.setCurrentText('DR10')
        self.dr_dropdown.setItemDelegate(QStyledItemDelegate(self.dr_dropdown))
        self.dr_dropdown.setFixedSize(110, 30)
        self.dr_dropdown.setStyleSheet(f"""
            QComboBox {{
                background-color: #1c2a42; color: {Theme.TXT};
                border: 1px solid #33425c; border-radius: 8px;
                font-size: 13px; font-weight: 600; padding: 0 10px;
            }}
            QComboBox:hover {{ background-color: #243a5a; }}
            QComboBox::drop-down {{ border: none; width: 20px; }}
            QComboBox QAbstractItemView {{
                background-color: #1c2a42; color: {Theme.TXT};
                selection-background-color: {Theme.ACCENT};
                outline: none;
            }}
            QComboBox QAbstractItemView::item {{ color: {Theme.TXT}; padding: 4px 10px; }}
        """)
        self.dr_dropdown.currentTextChanged.connect(self._change_survey)

        dr_hbox.addWidget(dr_label)
        dr_hbox.addWidget(self.dr_dropdown)

        self.open_skyviewer_button = ClickEffectStyleButton(text='Open SkyViewer', size=(160, 30))
        self.open_skyviewer_button.setStyleSheet(SECONDARY_BTN)
        self.open_skyviewer_button.setIcon(tabler_icon(OutlineIcon.TELESCOPE, size=15, color=Theme.TXT))
        self.open_skyviewer_button.setIconSize(QSize(15, 15))
        self.open_skyviewer_button.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(self.url_current_system)))
        self.copy_skyviewer_url_button = ClickEffectStyleButton(text='Copy URL', size=(100, 30))
        self.copy_skyviewer_url_button.setStyleSheet(SECONDARY_BTN)
        self.copy_skyviewer_url_button.setIcon(tabler_icon(OutlineIcon.COPY, size=15, color=Theme.TXT))
        self.copy_skyviewer_url_button.setIconSize(QSize(15, 15))
        self.copy_skyviewer_url_button.clicked.connect(lambda: QApplication.clipboard().setText(self.url_current_system))
        self.sky_viewer_buttons_layout.addWidget(dr_group)
        self.sky_viewer_buttons_layout.addStretch()
        self.sky_viewer_buttons_layout.addWidget(self.copy_skyviewer_url_button)
        self.sky_viewer_buttons_layout.addWidget(self.open_skyviewer_button)
        self.imaging_data_panel.add_layout(self.sky_viewer_buttons_layout)

        attrib = QLabel("Images: Legacy Surveys / D. Lang (Perimeter Institute)  ·  CC BY 4.0")
        attrib.setAlignment(Qt.AlignmentFlag.AlignCenter)
        attrib.setStyleSheet(
            f"color:{Theme.TXT_MUTE}; font-size:10px; background:transparent;")
        self.imaging_data_panel.layout.addWidget(attrib)

        #Meta data:
        metadata=self.current_inspection.get_current_metadata()
        # {'ra':ra,'dec':dec,'survey':survey,'user selected data':user_selected_data}
        self.metadata_panel.layout.setSpacing(4)
        self.ra_box=MetadataField('R.A.', str(metadata['ra']), mono=True)
        self.dec_box=MetadataField('DEC.', str(metadata['dec']), mono=True)
        self.survey_box=MetadataField('SURVEY', metadata['survey'])
        self.metadata_panel.add_widget(self.ra_box, stretch=(False,False))
        self.metadata_panel.add_widget(self.dec_box, stretch=(False,False))
        self.metadata_panel.add_widget(self.survey_box, stretch=(False,False))

        self.add_additional_boxes= True if type(metadata['user selected data'])==dict else False
        if self.add_additional_boxes:
            self.custom_metadata_widgets = []
            for var in metadata['user selected data'].keys():
                self.custom_metadata_widgets.append(MetadataField(str(var).upper(),str(metadata['user selected data'][var])))
                self.metadata_panel.add_widget(self.custom_metadata_widgets[-1], stretch=(False,False))
        self.metadata_panel.layout.addStretch()

        #System # tracker
        self.system_N_tracker.setText('System {} of {}'.format(1, self.N_total_systems))

        # Inspector input fields (custom might be added later):
        grader_name = metadata['grader name']
        first_comment_and_grade = self.current_inspection.get_current_comment_and_grade()
        caps_grade = bool(self.Settings.get_setting('caplock_grades'))
        caps_comment = bool(self.Settings.get_setting('caplock_comments'))
        self.grade_input = StyledInputBox('{} Grade'.format(grader_name),first_comment_and_grade['grade'],caps_lock=caps_grade,N_max_lines=1, center_text=True)
        self.grade_input.change_input_size(30)
        self.grade_input.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.grade_input.text_edit.installEventFilter(self)
        self.comment_input = StyledInputBox('{} Comment'.format(grader_name),first_comment_and_grade['comment'],caps_lock=caps_comment)
        self.comment_input.text_edit.installEventFilter(self)
        self.next_system_button.installEventFilter(self)
        all_input_field_widgets = [self.grade_input, self.comment_input]

        #Register fields with the drag-order widget (must happen after inputs are created)
        order_widget = self.Settings.name_to_widget_map.get('quick_inspection_field_order')
        if order_widget:
            order_widget.set_available_fields(['Grade', 'Comment'])

        #Connect action buttons:
        self.quick_inspection_activated=False
        self.focus_i = 0
        self._rebuild_focus_order()
        self.quick_inspection_checkbox.checkbox.stateChanged.connect(self.activate_deactivate_quick_inspection)
        self.lock_inspection_checkbox.checkbox.stateChanged.connect(self.lock_unlock_comments_and_grades)
        self.voiceover_checkbox.checkbox.stateChanged.connect(self._toggle_voiceover)

        # VoiceOver thread (starts/stops when checkbox is toggled)
        self._voiceover_consent_given = False
        self.vo_thread = VoiceOverThread(model_size='base', parent=self)
        self.vo_thread.listening.connect(self._on_vo_listening)
        self.vo_thread.processing.connect(self._on_vo_processing)
        self.vo_thread.transcript_ready.connect(self._on_vo_transcript)
        self.vo_thread.status_update.connect(self._on_vo_status)
        self.vo_thread.command_parsed.connect(self._handle_voice_command)
        self.vo_thread.error.connect(self._on_vo_error)

        # Idle auto-off: turns VoiceOver off after 60 s with no recognised command
        self._vo_idle_timer = QTimer(self)
        self._vo_idle_timer.setSingleShot(True)
        self._vo_idle_timer.setInterval(60_000)
        self._vo_idle_timer.timeout.connect(self._vo_idle_timeout)

        self.inspector_input_panel.layout.setSpacing(10)
        for input_field in all_input_field_widgets:
            self.inspector_input_panel.add_widget(input_field,stretch=(False,False))
        return
    
    def activate_deactivate_quick_inspection(self,state):
        if state == Qt.CheckState.Checked.value:
            self.quick_inspection_activated=True
            self.focus_order[self.focus_i].setFocus()
        else:
            self.quick_inspection_activated=False

    def lock_unlock_comments_and_grades(self,state):
        if state == Qt.CheckState.Checked.value:
            for field in [self.grade_input,self.comment_input]:
                field.disable_input()
        else:
            for field in [self.grade_input,self.comment_input]:
                field.enable_input()
    
    def _warn(self, title, text, confirm=False):
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setStyleSheet("""
            QMessageBox { background-color: black; }
            QLabel { color: white; font-size: 14px; }
            QPushButton {
                background-color: white;
                color: #152238;
                border-radius: 6px;
                padding: 4px 14px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #f0ffff; }
        """)
        if confirm:
            msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        else:
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        return msg.exec()

    def _rebuild_focus_order(self):
        field_map = {'Grade': self.grade_input, 'Comment': self.comment_input}
        field_order = self.Settings.get_setting('quick_inspection_field_order') or []
        ordered = [field_map[f] for f in field_order if f in field_map]
        self.focus_order = (ordered if ordered else list(field_map.values())) + [self.next_system_button]
        self.focus_i = 0

    def _apply_caps_lock_settings(self):
        self.grade_input.set_caps_lock(bool(self.Settings.get_setting('caplock_grades')))
        self.comment_input.set_caps_lock(bool(self.Settings.get_setting('caplock_comments')))

    # ── VoiceOver ─────────────────────────────────────────────────────

    def _toggle_voiceover(self, state):
        if state == Qt.CheckState.Checked.value:
            if not self._voiceover_consent_given and not self._show_voiceover_consent():
                self.voiceover_checkbox.checkbox.blockSignals(True)
                self.voiceover_checkbox.checkbox.setChecked(False)
                self.voiceover_checkbox.checkbox.blockSignals(False)
                return
            self.voiceover_status_widget.show()
            self.vo_thread.start_listening()
            self._vo_idle_timer.start()
        else:
            self.vo_thread.stop_listening()
            self._vo_idle_timer.stop()
            self.voiceover_status_widget.hide()

    def _show_voiceover_consent(self):
        dlg = QDialog(self)
        dlg.setWindowTitle('VoiceOver')
        dlg.setModal(True)
        dlg.setFixedWidth(420)
        dlg.setStyleSheet(f"""
            QDialog {{
                background-color: {Theme.SURFACE};
                border: 1px solid {Theme.BORDER};
                border-radius: 14px;
            }}
        """)

        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(30, 30, 30, 24)
        layout.setSpacing(0)

        # ── Icon badge ───────────────────────────────────────────────
        badge = QWidget()
        badge.setFixedSize(56, 56)
        badge.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        badge.setStyleSheet(f"background-color:{Theme.ACCENT}; border-radius:28px;")
        badge_layout = QVBoxLayout(badge)
        badge_layout.setContentsMargins(0, 0, 0, 0)
        mic_lbl = QLabel()
        mic_lbl.setPixmap(tabler_pixmap(OutlineIcon.MICROPHONE, size=26, color=ICON_WHITE))
        mic_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mic_lbl.setStyleSheet("background: transparent;")
        badge_layout.addWidget(mic_lbl)
        badge_wrapper = QHBoxLayout()
        badge_wrapper.addStretch()
        badge_wrapper.addWidget(badge)
        badge_wrapper.addStretch()
        layout.addLayout(badge_wrapper)
        layout.addSpacing(14)

        # ── Title ────────────────────────────────────────────────────
        title_lbl = QLabel("VoiceOver Privacy Notice")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_lbl.setStyleSheet(
            f"color:{Theme.TXT}; font-size:17px; font-weight:700; background:transparent;")
        layout.addWidget(title_lbl)
        layout.addSpacing(18)

        # ── Body ─────────────────────────────────────────────────────
        def row(icon_char, label, detail):
            w = QWidget()
            w.setStyleSheet("background: transparent;")
            h = QHBoxLayout(w)
            h.setContentsMargins(0, 0, 0, 0)
            h.setSpacing(12)
            dot = QLabel(icon_char)
            dot.setFixedWidth(22)
            dot.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
            dot.setStyleSheet(f"color:{Theme.ACCENT}; font-size:15px; background:transparent;")
            h.addWidget(dot)
            text = QLabel(f'<span style="color:{Theme.TXT}; font-weight:600;">{label}</span>'
                          f'<br><span style="color:{Theme.TXT_MUTE}; font-size:12px;">{detail}</span>')
            text.setTextFormat(Qt.TextFormat.RichText)
            text.setWordWrap(True)
            text.setStyleSheet("background: transparent;")
            h.addWidget(text, 1)
            return w

        layout.addWidget(row("◎", "Runs fully offline",
                             "Audio is processed on your device using a local Whisper model."))
        layout.addSpacing(12)
        layout.addWidget(row("◉", "Microphone access required",
                             "Your mic will be active while VoiceOver is on."))
        layout.addSpacing(12)
        layout.addWidget(row("◈", "First activation downloads the model",
                             "~150 MB downloaded once from Hugging Face, then cached locally."))
        layout.addSpacing(24)

        # ── Divider ──────────────────────────────────────────────────
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet(f"color:{Theme.BORDER};")
        layout.addWidget(divider)
        layout.addSpacing(18)

        # ── Buttons ──────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        decline_btn = QPushButton("Decline")
        decline_btn.setFixedHeight(38)
        decline_btn.setStyleSheet(GHOST_BTN)
        decline_btn.clicked.connect(dlg.reject)

        agree_btn = QPushButton("I Agree")
        agree_btn.setFixedHeight(38)
        agree_btn.setStyleSheet(PRIMARY_BTN)
        agree_btn.clicked.connect(dlg.accept)

        btn_row.addWidget(decline_btn)
        btn_row.addWidget(agree_btn)
        layout.addLayout(btn_row)

        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._voiceover_consent_given = True
            return True
        return False

    def _vo_idle_timeout(self):
        self.voiceover_checkbox.checkbox.blockSignals(True)
        self.voiceover_checkbox.checkbox.setChecked(False)
        self.voiceover_checkbox.checkbox.blockSignals(False)
        self.vo_thread.stop_listening()
        self.voiceover_status_widget.set_state('error', 'Idle timeout — VoiceOver off')
        self.voiceover_status_widget.show()
        QTimer.singleShot(3000, self.voiceover_status_widget.hide)

    def _on_vo_listening(self):
        self.voiceover_status_widget.set_state('listening', 'Listening...')

    def _on_vo_processing(self):
        self.voiceover_status_widget.set_state('processing', 'Processing...')

    def _on_vo_status(self, msg):
        self.voiceover_status_widget.set_state('processing', msg)

    def _on_vo_transcript(self, text):
        short = text if len(text) <= 40 else text[:37] + '...'
        self.voiceover_status_widget.set_state('heard', f'Heard: {short}')

    def _on_vo_error(self, msg):
        print(f'[VoiceOver error] {msg}')
        self.voiceover_status_widget.set_state('error', f'Error: {msg}')

    def _handle_voice_command(self, cmd):
        """Apply a parsed VoiceOver command dict to the current inspection entry."""
        self._vo_idle_timer.start()  # reset the 60 s idle countdown
        if cmd.get('grade') is not None:
            self.grade_input.update_text(cmd['grade'])
        if cmd.get('comment') is not None:
            self.comment_input.update_text(cmd['comment'])
        action = cmd.get('action')
        if action == 'next':
            self.load_next_system()
        elif action == 'previous':
            self.load_previous_system()

    def _validate_navigation(self):
        grade = self.grade_input.get_content().strip()
        comment = self.comment_input.get_content().strip()

        if self.Settings.get_setting('require_grade') and not grade:
            reply = self._warn('Missing Grade',
                'No grade has been entered for this system. Continue anyway?', confirm=True)
            if reply == QMessageBox.StandardButton.No:
                return False

        if self.Settings.get_setting('only_pre_defined_grades') and grade:
            allowed = self.Settings.get_setting('list_of_allowed_grades')
            if allowed and grade not in allowed:
                self._warn('Invalid Grade',
                    f'"{grade}" is not an allowed grade.\nAllowed grades: {", ".join(allowed)}')
                return False

        if self.Settings.get_setting('require_comment') and not comment:
            reply = self._warn('Missing Comment',
                'No comment has been entered for this system. Continue anyway?', confirm=True)
            if reply == QMessageBox.StandardButton.No:
                return False

        return True

    def load_next_system(self):
        if not self._validate_navigation():
            return
        self.current_inspection.update_df({'grade':self.grade_input.get_content(), 'comment':self.comment_input.get_content()})
        self.current_inspection.df_has_been_modified=True
        self.trigger_csv_save_thread()
        if self.current_idx==0:
            self.previous_system_button.setEnabled(True)
        self.current_idx+=1
        if self.current_idx == self.N_total_systems-1:
            self.next_system_button.setEnabled(False)
        self.update_onscreen_data()
        if self.quick_inspection_activated:
            self.focus_order[0].setFocus()
            self.focus_i=0

    def load_previous_system(self):
        if not self._validate_navigation():
            return
        self.current_inspection.update_df({'grade':self.grade_input.get_content(), 'comment':self.comment_input.get_content()})
        if self.current_idx == self.N_total_systems-1:
            self.next_system_button.setEnabled(True)
        self.current_idx-=1
        if self.current_idx==0:
            self.previous_system_button.setEnabled(False)
        self.update_onscreen_data()

    def update_onscreen_data(self):
        self.system_N_tracker.setText('System {} of {}'.format(self.current_idx+1, self.N_total_systems))
        success_dict, data_dict = self.current_inspection.get_current_images(idx=self.current_idx)
        current_comment_and_grade = self.current_inspection.get_current_comment_and_grade()

        #Update images
        if success_dict['rgb']:
            self.images_on_layout['rgb'].update_image(data_dict['rgb'])
        if success_dict['grz']:
            for band in range(3):
                self.images_on_layout[self.idx_to_band_dict[band]].update_image(data_dict['grz'][band])
        self._update_blank_overlays(success_dict, data_dict)
        #Update skyviewer hyperlink
        self.url_current_system = self.current_inspection.get_current_url()
        #Update grade and comment
        self.grade_input.update_text(current_comment_and_grade['grade'])
        self.comment_input.update_text(current_comment_and_grade['comment'])
        #Update metadata
        metadata=self.current_inspection.get_current_metadata()
        self.ra_box.update_content(str(metadata['ra']))
        self.dec_box.update_content(str(metadata['dec']))
        self.survey_box.update_content(metadata['survey'])

        if self.add_additional_boxes:
            for var_n,var in enumerate(metadata['user selected data'].keys()):
                self.custom_metadata_widgets[var_n].update_content(str(metadata['user selected data'][var]))

    def trigger_csv_save_thread(self):
        if self.save_csv_worker and self.save_csv_worker.isRunning():
            return
        self.save_status_widget.set_status(color='orange', text='Autosaving CSV')
        self.save_csv_worker = SaveCSVWorker(self.main_window.df, self.CSV_save_path)
        self.save_csv_worker.finished.connect(self.inform_success_saving_CSV)
        self.save_csv_worker.error.connect(self.inform_failure_saving_CSV)
        self.save_csv_worker.start()

    def inform_success_saving_CSV(self):
        self.save_status_widget.set_status(color='green', text='Autosaving on')

    def inform_failure_saving_CSV(self):
        self.save_status_widget.set_status(color='red', text='Autosaving failed')
    
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.FocusIn and self.quick_inspection_activated:
            if obj == self.grade_input.text_edit:
                self.grade_input._set_border(with_focus_outline=True)
            elif obj == self.comment_input.text_edit:
                self.comment_input._set_border(with_focus_outline=True)
        elif event.type() == QEvent.Type.FocusOut:
            if obj == self.grade_input.text_edit:
                self.grade_input._set_border(with_focus_outline=False)
            elif obj == self.comment_input.text_edit:
                self.comment_input._set_border(with_focus_outline=False)
        if event.type() == QEvent.Type.KeyPress and self.quick_inspection_activated:
            if event.key() in self._advance_keys():
                self._advance_focus()
                return True
        return super().eventFilter(obj, event)
    
    _KEY_MAP = {
        'Enter': (Qt.Key.Key_Return, Qt.Key.Key_Enter),
        'Tab':   (Qt.Key.Key_Tab,),
        'Space': (Qt.Key.Key_Space,),
    }

    def _advance_keys(self):
        choice = self.Settings.get_setting('quick_inspection_next_key_choice') or 'Enter'
        return self._KEY_MAP.get(choice, (Qt.Key.Key_Return, Qt.Key.Key_Enter))

    def _advance_focus(self):
        if self.focus_i == len(self.focus_order) - 1:
            if self.next_system_button.isEnabled():
                self.next_system_button.click()
        else:
            self.focus_i += 1
            self.focus_order[self.focus_i].setFocus()

        # self.focus_order = [self.grade_input,self.comment_input,self.next_system_button]
        # self.focus_i = 0

class SaveCSVWorker(QThread):
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, inspection_df,save_path):
        super().__init__()
        self.inspection_df = inspection_df
        self.save_path = save_path

    def run(self):
        try:
            self.inspection_df.to_csv(self.save_path)
            time.sleep(2)
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))