from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSpacerItem, QSizePolicy,QGridLayout,QApplication
from PyQt6.QtCore import Qt, QUrl,QThread, pyqtSignal, QEvent, QPropertyAnimation, QParallelAnimationGroup, QEasingCurve, QPoint
from PyQt6.QtGui import QPainter, QDesktopServices
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtCore import QRectF

import numpy as np
import time
# from Assets import SvgWidget, ImageWidget, InputField, ClickEffectButton
from Assets import Panel,SvgWidget, ImageWidget, StyledTextBox, ClickEffectStyleButton, StyledText, StyledInputBox,StatusWidget,CheckBox,StyledTabBar
from InspectionEngine import Inspection,ThreadImageFetcher

class StudioScreenWidget(QWidget):
    def __init__(self,main_window):
        super().__init__()
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
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
        self.bottom_panel = Panel(border_radius=0,vertical=False)
        # logo = SvgWidget(self.main_window.GRAPHICS_ADDRESSES['large app icon'])
        # logo.setFixedSize(40,40)

        #Buttons:
        self.next_system_button = ClickEffectStyleButton(text='Next →')
        self.next_system_button.clicked.connect(self.load_next_system)
        self.next_system_button.setAutoDefault(True) #To have button respond to enter during quick inspection
        self.previous_system_button = ClickEffectStyleButton(text='← Previous')
        self.previous_system_button.setEnabled(False)
        self.previous_system_button.clicked.connect(self.load_previous_system)

        #Inspection optional features:
        self.lock_inspection_checkbox = CheckBox("Lock Grades and Comments",self.main_window,background_color=self.main_window.COLOR_PALETTE["frame background"])
        self.quick_inspection_checkbox = CheckBox("Quick Inspection Mode",self.main_window,background_color=self.main_window.COLOR_PALETTE["frame background"])
        # self.lock_inspection_toggle = StyledToggleSwitch("Lock Grades & Comments")

        # Labels:
        self.system_N_tracker = StyledText()
        self.save_status_widget = StatusWidget(text='Autosaving on', color='green', dot_size=12)

        #Add items to bottom panel
        self.bottom_panel.add_widget(self.previous_system_button)
        # self.bottom_panel.add_widget(logo,stretch=(True,True))
        self.bottom_panel.add_widget(self.lock_inspection_checkbox.checkbox)
        self.bottom_panel.add_widget(self.quick_inspection_checkbox.checkbox)
        self.bottom_panel.add_widget(self.next_system_button)

        #Add items to top panel
        self.top_panel.add_widget(self.save_status_widget,stretch=(False,True))
        self.top_panel.add_widget(self.system_N_tracker,stretch=(False,True))

        #Clipping widget for animated transitions:
        self.clipper = QWidget()

        for panel,stretch_factor in zip([self.metadata_panel,self.imaging_data_panel,self.inspector_input_panel],(1,3,2)):
            self.panels_layout.addWidget(panel,stretch_factor)
        self.panels_container_widget = QWidget(self.clipper)
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

    def _on_slide_finished(self):
        # self.screen_out.hide()
        self.animating = False
        self.current_screen = self.to_screen
        if self.to_screen == 'inspection':
            self.bottom_panel.setMaximumHeight(16777215)  # Qt's QWIDGETSIZE_MAX
            self.system_N_tracker.show()
            self.save_status_widget.show()

    def _create_settings_window(self):
        self.settings_layout = QHBoxLayout()
        self.settings_left_panel = Panel()
        self.settings_left_panel.add_title(title='Options',center_title=False)
        self.settings_layout.addWidget(self.settings_left_panel,1)
        self.settings_right_panel = Panel()
        self.settings_right_panel.add_title(title='',center_title=False)
        self.settings_layout.addWidget(self.settings_right_panel,5)
        self.settings_layout_container_widget=QWidget(self.clipper)
        self.settings_layout_container_widget.setLayout(self.settings_layout)
        # self.settings_layout_container_widget.setGeometry(
        #                                         self.clipper.width(), 0,
        #                                         self.clipper.width(), self.clipper.height()
        #                                     )
        
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
        grid_layout.setSpacing(6)  # same gap horizontally and vertically
        grid_layout.setColumnStretch(0, 1)
        grid_layout.setColumnStretch(1, 3)
        grid_layout.setRowStretch(0, 1)
        grid_layout.setRowStretch(1, 1)
        grid_layout.setRowStretch(2, 1)
        small_cutout_panel_size=120
        if success_dict['grz']:
            for band in range(3):
                band_image = ImageWidget(data_dict['grz'][band],panel_size=(small_cutout_panel_size,small_cutout_panel_size))
                grid_layout.addWidget(band_image, band, 0)
                self.images_on_layout[self.idx_to_band_dict[band]] = band_image
        if success_dict['rgb']:
            rgb_image = ImageWidget(data_dict['rgb'],panel_size=(3*small_cutout_panel_size,3*small_cutout_panel_size))
            grid_layout.addWidget(rgb_image, 0, 1, 3, 1)
            self.images_on_layout['rgb'] = rgb_image
        self.imaging_data_panel.add_layout(grid_layout)

        # Add "open sky viewer button"
        self.url_current_system = self.current_inspection.get_current_url()
        self.sky_viewer_buttons_layout = QHBoxLayout()
        self.open_skyviewer_button = ClickEffectStyleButton(text='Open SkyViewer 🔭',size=(300,25))
        self.open_skyviewer_button.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(self.url_current_system)))
        self.copy_skyviewer_url_button = ClickEffectStyleButton(text='Copy SkyViewer URL 🔗',size=(300,25))
        self.copy_skyviewer_url_button.clicked.connect(lambda: QApplication.clipboard().setText(self.url_current_system))
        self.sky_viewer_buttons_layout.addWidget(self.copy_skyviewer_url_button)
        self.sky_viewer_buttons_layout.addWidget(self.open_skyviewer_button)
        self.imaging_data_panel.add_layout(self.sky_viewer_buttons_layout)
        # self.imaging_data_panel

        #Meta data:
        metadata=self.current_inspection.get_current_metadata()
        # {'ra':ra,'dec':dec,'survey':survey,'user selected data':user_selected_data}
        self.ra_box=StyledTextBox('R.A.', str(metadata['ra']))
        self.dec_box=StyledTextBox('Dec.', str(metadata['dec']))
        self.survey_box=StyledTextBox('Survey', metadata['survey'])
        self.metadata_panel.add_widget(self.ra_box)
        self.metadata_panel.add_widget(self.dec_box)
        self.metadata_panel.add_widget(self.survey_box)

        self.add_additional_boxes= True if type(metadata['user selected data'])==dict else False
        if self.add_additional_boxes:
            self.custom_metadata_widgets = []
            for var in metadata['user selected data'].keys():
                self.custom_metadata_widgets.append(StyledTextBox(str(var),str(metadata['user selected data'][var])))
                self.metadata_panel.add_widget(self.custom_metadata_widgets[-1])

        #System # tracker
        self.system_N_tracker.setText('System {} of {}'.format(1, self.N_total_systems))

        # Inspector input fields (custom might be added later):
        grader_name = metadata['grader name']
        first_comment_and_grade = self.current_inspection.get_current_comment_and_grade()
        self.grade_input = StyledInputBox('{} Grade'.format(grader_name),first_comment_and_grade['grade'],caps_lock=True,N_max_lines=1, center_text=True)
        self.grade_input.change_input_size(30)
        self.grade_input.text_edit.installEventFilter(self)
        self.comment_input = StyledInputBox('{} Comment'.format(grader_name),first_comment_and_grade['comment'])
        self.comment_input.text_edit.installEventFilter(self)
        all_input_field_widgets = [self.grade_input, self.comment_input]

        #Connect action buttons:
        self.quick_inspection_activated=False
        self.focus_order = [self.grade_input,self.comment_input,self.next_system_button]
        self.focus_i = 0
        self.quick_inspection_checkbox.checkbox.stateChanged.connect(self.activate_deactivate_quick_inspection)
        self.lock_inspection_checkbox.checkbox.stateChanged.connect(self.lock_unlock_comments_and_grades)

        for input_field_n,input_field in enumerate(all_input_field_widgets):
            if input_field_n == len(all_input_field_widgets)-1:
                self.inspector_input_panel.add_widget(input_field,stretch=(False,True))
            else:
                self.inspector_input_panel.add_widget(input_field,stretch=(False,False))
        return
    
    def activate_deactivate_quick_inspection(self,state):
        if state == Qt.CheckState.Checked.value:
            print('Quick inspection activated')
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
    
    def load_next_system(self):
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
            if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                self._advance_focus()
                return True
        return super().eventFilter(obj, event)
    
    def _advance_focus(self):
        self.focus_i+=1
        self.focus_order[self.focus_i].setFocus()
        print(f'Focus {self.focus_i} shown')

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