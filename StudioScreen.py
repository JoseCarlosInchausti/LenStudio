from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSpacerItem, QSizePolicy,QGridLayout,QApplication, QStackedWidget,QLabel,QMessageBox,QFrame,QGraphicsDropShadowEffect,QComboBox,QStyledItemDelegate,QDialog,QPushButton,QSlider,QToolTip,QProgressBar,QScrollArea,QTableWidget,QTableWidgetItem,QHeaderView
from PyQt6.QtCore import Qt, QUrl,QThread, pyqtSignal, QEvent, QPropertyAnimation, QParallelAnimationGroup, QEasingCurve, QPoint, QSize, QTimer
from PyQt6.QtGui import QPainter, QDesktopServices, QColor, QCursor, QBrush, QPen, QFont
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtCore import QRectF

import os
import math
import numpy as np
import time
# from Assets import SvgWidget, ImageWidget, InputField, ClickEffectButton
from Assets import Panel,SvgWidget, ImageWidget, StyledTextBox, MetadataField, ClickEffectStyleButton, StyledText, StyledInputBox,StatusWidget,CheckBox,StyledTabBar,InspectionSettings,ScrollPanel,StyledGroupBox,VoiceOverIndicator,SystemJumpWidget
from InspectionEngine import Inspection, PrefetchThread
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
QPushButton:disabled {{ color:#3a4e68; border-color:#1f3148; background-color:#0f1a28; }}
"""
ER_ACTIVE_BTN = f"""
QPushButton {{ background-color:#1c2a42; color:{Theme.ACCENT}; border:1px solid {Theme.ACCENT};
               border-radius:8px; font-size:13px; font-weight:600; }}
QPushButton:hover {{ background-color:#243a5a; }}
QPushButton:pressed {{ background-color:#182942; }}
"""
MC_ACTIVE_BTN = f"""
QPushButton {{ background-color:#1c2a42; color:#f59e0b; border:1px solid #f59e0b;
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

# ─── Summary screen helper widgets ────────────────────────────────────────────

class _SummaryProgressBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._v = 0.0
        self.setFixedHeight(4)

    def set_value(self, v: float):
        self._v = max(0.0, min(1.0, v))
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = self.rect()
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(Theme.FIELD)))
        p.drawRoundedRect(QRectF(r), 2, 2)
        if self._v > 0:
            fw = max(4, int(r.width() * self._v))
            p.setBrush(QBrush(QColor(Theme.ACCENT)))
            p.drawRoundedRect(QRectF(0, 0, fw, r.height()), 2, 2)
        p.end()


class _SummaryHistogram(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._counts: dict = {}

    def set_data(self, counts: dict):
        self._counts = dict(counts)
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        if not self._counts:
            p.end()
            return
        w, h = self.width(), self.height()
        PAD_TOP, PAD_BOT, PAD_H = 22, 32, 4
        sorted_g  = sorted(self._counts.keys())
        n         = len(sorted_g)
        max_c     = max(self._counts.values())
        slot_w    = (w - 2 * PAD_H) / n
        bar_w     = max(10.0, slot_w * 0.52)
        bar_area_h = h - PAD_TOP - PAD_BOT

        accent = QColor(Theme.ACCENT)
        track  = QColor('#1a2f4a')
        txt_c  = QColor(Theme.TXT_SOFT)
        mute_c = QColor(Theme.TXT_MUTE)

        f_count = QFont(); f_count.setPixelSize(11); f_count.setWeight(QFont.Weight.Bold)
        f_grade = QFont(); f_grade.setPixelSize(12); f_grade.setWeight(QFont.Weight.DemiBold)

        p.setPen(Qt.PenStyle.NoPen)
        for i, grade in enumerate(sorted_g):
            count = self._counts[grade]
            ratio = count / max_c
            bh    = max(4.0, bar_area_h * ratio)
            bx    = PAD_H + i * slot_w + (slot_w - bar_w) / 2
            by    = PAD_TOP + (bar_area_h - bh)

            p.setBrush(QBrush(track))
            p.drawRoundedRect(QRectF(bx, PAD_TOP, bar_w, bar_area_h), 4, 4)
            p.setBrush(QBrush(accent))
            p.drawRoundedRect(QRectF(bx, by, bar_w, bh), 4, 4)

            p.setPen(txt_c);  p.setFont(f_count)
            p.drawText(QRectF(bx - 20, by - 20, bar_w + 40, 18),
                       Qt.AlignmentFlag.AlignCenter, str(count))
            p.setPen(mute_c); p.setFont(f_grade)
            p.drawText(QRectF(bx - 20, h - PAD_BOT + 4, bar_w + 40, PAD_BOT),
                       Qt.AlignmentFlag.AlignCenter, grade)
            p.setPen(Qt.PenStyle.NoPen)
        p.end()


class _InlineBar(QWidget):
    def __init__(self, fill: float, parent=None):
        super().__init__(parent)
        self._fill = fill

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = self.rect()
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(Theme.FIELD)))
        p.drawRoundedRect(QRectF(r), 2.5, 2.5)
        fw = r.width() * self._fill
        if fw > 0:
            p.setBrush(QBrush(QColor(Theme.ACCENT)))
            p.drawRoundedRect(QRectF(0, 0, fw, r.height()), 2.5, 2.5)
        p.end()


class _GradeRow(QWidget):
    def __init__(self, grade: str, count: int, pct: float, fill: float, parent=None):
        super().__init__(parent)
        self.setFixedHeight(46)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        gl = QLabel(grade)
        gl.setFixedWidth(56)
        gl.setStyleSheet(
            f"color:{Theme.TXT}; font-size:15px; font-weight:700; background:transparent;")

        bar_wrap = QWidget()
        bar_wrap.setStyleSheet("background:transparent;")
        bw_lay = QVBoxLayout(bar_wrap)
        bw_lay.setContentsMargins(0, 0, 0, 0)
        bw_lay.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        ib = _InlineBar(fill)
        ib.setFixedHeight(5)
        bw_lay.addWidget(ib)

        cl = QLabel(str(count))
        cl.setFixedWidth(50)
        cl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        cl.setStyleSheet(
            f"color:{Theme.TXT}; font-size:14px; font-weight:600; background:transparent;")

        pl = QLabel(f'{pct:.1f}%')
        pl.setFixedWidth(58)
        pl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        pl.setStyleSheet(
            f"color:{Theme.TXT_MUTE}; font-size:13px; background:transparent;")

        lay.addWidget(gl)
        lay.addWidget(bar_wrap, 1)
        lay.addSpacing(20)
        lay.addWidget(cl)
        lay.addSpacing(8)
        lay.addWidget(pl)

# ──────────────────────────────────────────────────────────────────────────────

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
        self._prefetch_threads = {}

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
        self.tools_panel = Panel()
        self.tools_panel.add_title(title='Tools',center_title=False)

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
        self.system_N_tracker = SystemJumpWidget()
        self.system_N_tracker.jump_requested.connect(self._jump_to_system)
        self.save_status_widget = StatusWidget(text='Autosaving on', color='green', dot_size=12)

        #Add items to bottom panel
        self.bottom_panel.add_widget(self.previous_system_button)
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

        self.left_column = QWidget()
        self.left_column.setStyleSheet("background: transparent;")
        _left_col_layout = QVBoxLayout(self.left_column)
        _left_col_layout.setContentsMargins(0, 0, 0, 0)
        _left_col_layout.setSpacing(5)
        _left_col_layout.addWidget(self.metadata_panel, 2)
        _left_col_layout.addWidget(self.tools_panel, 1)

        for panel,stretch_factor in zip([self.left_column,self.imaging_data_panel,self.inspector_input_panel],(5,9,6)):
            self.panels_layout.addWidget(panel,stretch_factor)
        self.panels_container_widget = QWidget(self.clipper)
        self.panels_container_widget.setStyleSheet("background-color: transparent;")
        self.panels_container_widget.setLayout(self.panels_layout)

        self.summary_container_widget = QWidget(self.clipper)
        self.summary_container_widget.setStyleSheet("background-color: transparent;")

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
        self.screen_name_to_container = {
            'inspection': self.panels_container_widget,
            'summary':    self.summary_container_widget,
            'settings':   self.settings_layout_container_widget,
        }
        self.screen_orders = {'inspection': 0, 'summary': 1, 'settings': 2}

        self.screen_switch_tab_bar = StyledTabBar({'Studio': 'inspection', 'Summary': 'summary', 'Settings': 'settings'})
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
        elif self.to_screen == 'summary':
            if hasattr(self, 'vo_thread'):
                self.vo_thread.stop_listening()
                self._vo_idle_timer.stop()
                self.voiceover_status_widget.hide()
            if hasattr(self, '_summary_chart'):
                self._refresh_summary()
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
        self.summary_container_widget.setGeometry(
            self.clipper.width(), 0,
            self.clipper.width(), self.clipper.height()
        )
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
        self._stop_all_prefetches()
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
        if success_dict.get('bad_coords'):
            ra_val  = data_dict.get('ra_val', '?')
            dec_val = data_dict.get('dec_val', '?')
            msg = f"Invalid coordinates\nRA: {ra_val}\nDEC: {dec_val}"
            for overlay in self.blank_overlays.values():
                overlay.setText(msg)
                overlay.show()
            return

        for overlay in self.blank_overlays.values():
            overlay.setText("Not in\nfootprint")

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
        grid_layout.setColumnStretch(0, 0)  # sliders — fixed width
        grid_layout.setColumnStretch(1, 1)  # GRZ frames
        grid_layout.setColumnStretch(2, 3)  # RGB frame
        small_cutout_panel_size = 120
        frame_size = small_cutout_panel_size + 14  # image + frame margins
        self.blank_overlays = {}
        self.contrast_sliders = {}
        blank_band = np.zeros((101, 101), dtype=np.float32)
        blank_rgb  = np.zeros((101, 101, 3), dtype=np.uint8)

        slider_qss = f"""
            QSlider::groove:vertical {{
                background: {Theme.BORDER}; width: 4px; border-radius: 2px;
            }}
            QSlider::handle:vertical {{
                background: {Theme.ACCENT}; width: 14px; height: 14px;
                margin: 0 -5px; border-radius: 7px;
            }}
            QSlider::add-page:vertical {{
                background: {Theme.FIELD}; border-radius: 2px;
            }}
        """

        for band in range(3):
            band_key = self.idx_to_band_dict[band]
            arr = data_dict['grz'][band] if (success_dict['grz'] and data_dict['grz'] is not None) else blank_band
            band_image = ImageWidget(arr, panel_size=(small_cutout_panel_size, small_cutout_panel_size))

            slider = QSlider(Qt.Orientation.Vertical)
            slider.setRange(1, 100)
            slider.setValue(50)
            slider.setFixedWidth(20)
            slider.setFixedHeight(frame_size)
            slider.setStyleSheet(slider_qss)
            slider.valueChanged.connect(band_image.set_contrast_scale)
            self.contrast_sliders[band_key] = slider

            grid_layout.addWidget(slider, band, 0, alignment=Qt.AlignmentFlag.AlignCenter)
            grid_layout.addWidget(self._frame_image(band_image, band_key), band, 1, alignment=Qt.AlignmentFlag.AlignCenter)
            self.images_on_layout[band_key] = band_image
            self.blank_overlays[band_key] = self._make_blank_overlay(band_image)

        rgb_arr = data_dict['rgb'] if (success_dict['rgb'] and data_dict['rgb'] is not None) else blank_rgb
        rgb_image = ImageWidget(rgb_arr, panel_size=(3*small_cutout_panel_size, 3*small_cutout_panel_size))
        grid_layout.addWidget(self._frame_image(rgb_image, 'RGB'), 0, 2, 3, 1, alignment=Qt.AlignmentFlag.AlignCenter)
        self.images_on_layout['rgb'] = rgb_image
        self.blank_overlays['rgb'] = self._make_blank_overlay(rgb_image)
        self._update_blank_overlays(success_dict, data_dict)
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
        attrib_btn = QPushButton()
        attrib_btn.setFixedSize(30, 30)
        attrib_btn.setIcon(tabler_icon(OutlineIcon.INFO_CIRCLE, size=16, color=Theme.TXT_MUTE))
        attrib_btn.setIconSize(QSize(16, 16))
        attrib_btn.setToolTip("Images: Legacy Surveys / D. Lang (Perimeter Institute)  ·  CC BY 4.0")
        attrib_btn.setStyleSheet(f"""
            QPushButton {{ background-color:transparent; border:none; border-radius:6px; }}
            QPushButton:hover {{ background-color:#1c2a42; }}
        """)

        self._er_mode = False
        self._er_points = []
        self._er_overlay_items = []
        self._er_overlay_visible = False

        self._mc_mode = False
        self._mc_point = None
        self._mc_overlay_items = []
        self._mc_ra = None
        self._mc_dec = None
        self._mc_overlay_visible = False

        self.sky_viewer_buttons_layout.addWidget(dr_group)
        self.sky_viewer_buttons_layout.addStretch()
        self.sky_viewer_buttons_layout.addWidget(self.copy_skyviewer_url_button)
        self.sky_viewer_buttons_layout.addWidget(self.open_skyviewer_button)
        self.sky_viewer_buttons_layout.addWidget(attrib_btn)
        self.imaging_data_panel.add_layout(self.sky_viewer_buttons_layout)

        self.images_on_layout['rgb'].scene().sigMouseClicked.connect(self._on_er_rgb_click)
        self.images_on_layout['rgb'].scene().sigMouseClicked.connect(self._on_mc_rgb_click)

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

        self._setup_tools_panel()

        #System # tracker
        self.system_N_tracker.set_system(1, self.N_total_systems)

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

        self.inspector_input_panel.layout.addStretch()
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {Theme.BORDER}; background-color: {Theme.BORDER};")
        sep.setFixedHeight(1)
        self.inspector_input_panel.layout.addWidget(sep)
        self.inspector_input_panel.layout.setContentsMargins(12, 8, 12, 12)
        for cb in [self.lock_inspection_checkbox.checkbox,
                   self.quick_inspection_checkbox.checkbox,
                   self.voiceover_checkbox.checkbox]:
            self.inspector_input_panel.layout.addWidget(cb)

        self._setup_summary_screen()

        self._er_restore()
        self._mc_restore()

        self._start_prefetch(1)

    def activate_deactivate_quick_inspection(self,state):
        if state == Qt.CheckState.Checked.value:
            self.quick_inspection_activated=True
            self.focus_order[self.focus_i].setFocus()
        else:
            self.quick_inspection_activated=False

    def lock_unlock_comments_and_grades(self,state):
        locked = state == Qt.CheckState.Checked.value
        for field in [self.grade_input, self.comment_input]:
            if locked:
                field.disable_input()
            else:
                field.enable_input()
            field.show_lock(locked)
    
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

    def _jump_to_system(self, idx):
        if idx == self.current_idx:
            return
        if not self._validate_navigation():
            return
        self.current_inspection.update_df({'grade': self.grade_input.get_content(), 'comment': self.comment_input.get_content()})
        self.current_inspection.df_has_been_modified = True
        self.trigger_csv_save_thread()
        self.current_idx = idx
        self.previous_system_button.setEnabled(self.current_idx > 0)
        self.next_system_button.setEnabled(self.current_idx < self.N_total_systems - 1)
        self.update_onscreen_data()
        if self.quick_inspection_activated:
            self.focus_order[0].setFocus()
            self.focus_i = 0

    def update_onscreen_data(self):
        self._er_restore()
        self._mc_restore()
        self.system_N_tracker.set_system(self.current_idx + 1, self.N_total_systems)
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

        self._start_prefetch(self.current_idx + 1)

    # ── Einstein Radius measurement ──────────────────────────────────────────

    def _toggle_er_mode(self):
        self._er_mode = not self._er_mode
        if self._er_mode:
            self._er_button.setStyleSheet(ER_ACTIVE_BTN)
            self._er_button.setIcon(tabler_icon(OutlineIcon.RULER_MEASURE, size=15, color=Theme.ACCENT))
            self._er_clear()
        else:
            self._er_button.setStyleSheet(SECONDARY_BTN)
            self._er_button.setIcon(tabler_icon(OutlineIcon.RULER_MEASURE, size=15, color=Theme.TXT))
            self._er_clear()

    def _on_er_rgb_click(self, event):
        if not self._er_mode:
            return
        if event.button() != Qt.MouseButton.LeftButton:
            return
        import pyqtgraph as pg
        rgb_widget = self.images_on_layout['rgb']
        vb = rgb_widget.plot
        if not vb.sceneBoundingRect().contains(event.scenePos()):
            return
        pos = vb.mapSceneToView(event.scenePos())
        x, y = pos.x(), pos.y()
        if not (0 <= x <= rgb_widget.img_w and 0 <= y <= rgb_widget.img_h):
            return
        if len(self._er_points) >= 2:
            self._er_points = []
            self._er_clear_overlay()
            self._er_result_label.setText('—')
            self._er_overlay_visible = False
            self._er_show_btn.setEnabled(False)
            self._er_show_btn.setText('Show ER')
            self._er_show_btn.setIcon(tabler_icon(OutlineIcon.EYE, size=15, color=Theme.TXT))
            self._er_show_btn.setIconSize(QSize(15, 15))
            self._er_show_btn.setStyleSheet(SECONDARY_BTN)
        self._er_points.append((x, y))
        self._er_draw_overlay()

    def _er_draw_overlay(self):
        import pyqtgraph as pg
        self._er_clear_overlay()
        vb = self.images_on_layout['rgb'].plot
        pts = self._er_points
        pix_scale = self.current_inspection.pixscale

        x1, y1 = pts[0]
        dot1 = pg.ScatterPlotItem([x1], [y1], pen=None,
                                  brush=pg.mkBrush(Theme.ACCENT), size=10)
        vb.addItem(dot1)
        self._er_overlay_items.append(dot1)

        if len(pts) == 2:
            x2, y2 = pts[1]
            line = pg.PlotDataItem(
                [x1, x2], [y1, y2],
                pen=pg.mkPen(color=Theme.ACCENT, width=1.5,
                             style=Qt.PenStyle.DashLine))
            dot2 = pg.ScatterPlotItem([x2], [y2], pen=None,
                                      brush=pg.mkBrush(Theme.ACCENT), size=10)
            d_arcsec = ((x2-x1)**2 + (y2-y1)**2)**0.5 * pix_scale
            lbl = pg.TextItem(f'ER = {d_arcsec:.2f}″', color=(255, 255, 255),
                              anchor=(0.5, 1.4))
            lbl.setPos((x1+x2)/2, (y1+y2)/2)
            vb.addItem(line)
            vb.addItem(dot2)
            vb.addItem(lbl)
            self._er_overlay_items.extend([line, dot2, lbl])
            self._er_result_label.setText(f'ER ≈ {d_arcsec:.2f}″')
            self._er_overlay_visible = True
            self._er_show_btn.setEnabled(True)
            self._er_show_btn.setText('Hide ER')
            self._er_show_btn.setIcon(tabler_icon(OutlineIcon.EYE_OFF, size=15, color=Theme.ACCENT))
            self._er_show_btn.setIconSize(QSize(15, 15))
            self._er_show_btn.setStyleSheet(ER_ACTIVE_BTN)
            grader = self.current_inspection.inspection_parameters['grader name']
            col_er = f'ER_arcsec_{grader}_VI'
            if col_er not in self.main_window.df.columns:
                self.main_window.df[col_er] = ''
            self.main_window.df.loc[self.current_idx, col_er] = round(d_arcsec, 3)
            self.current_inspection.df_has_been_modified = True
            self.trigger_csv_save_thread()

    def _er_clear_overlay(self):
        if hasattr(self, 'images_on_layout') and 'rgb' in self.images_on_layout:
            vb = self.images_on_layout['rgb'].plot
            for item in self._er_overlay_items:
                try:
                    vb.removeItem(item)
                except Exception:
                    pass
        self._er_overlay_items = []

    def _er_clear(self):
        self._er_clear_overlay()
        self._er_points = []
        self._er_overlay_visible = False
        if hasattr(self, '_er_result_label'):
            self._er_result_label.setText('—')
        if hasattr(self, '_er_show_btn'):
            self._er_show_btn.setEnabled(False)
            self._er_show_btn.setText('Show ER')
            self._er_show_btn.setIcon(tabler_icon(OutlineIcon.EYE, size=15, color=Theme.TXT))
            self._er_show_btn.setIconSize(QSize(15, 15))
            self._er_show_btn.setStyleSheet(SECONDARY_BTN)

    def _er_toggle_visibility(self):
        self._er_overlay_visible = not self._er_overlay_visible
        for item in self._er_overlay_items:
            item.setVisible(self._er_overlay_visible)
        if self._er_overlay_visible:
            self._er_show_btn.setText('Hide ER')
            self._er_show_btn.setIcon(tabler_icon(OutlineIcon.EYE_OFF, size=15, color=Theme.ACCENT))
            self._er_show_btn.setIconSize(QSize(15, 15))
            self._er_show_btn.setStyleSheet(ER_ACTIVE_BTN)
        else:
            self._er_show_btn.setText('Show ER')
            self._er_show_btn.setIcon(tabler_icon(OutlineIcon.EYE, size=15, color=Theme.TXT))
            self._er_show_btn.setIconSize(QSize(15, 15))
            self._er_show_btn.setStyleSheet(SECONDARY_BTN)

    # ─────────────────────────────────────────────────────────────────────────

    def _on_tool_changed(self, text):
        if text == 'Measure ER':
            self._tool_stacked.setCurrentIndex(0)
            if self._mc_mode:
                self._toggle_mc_mode()
        else:
            self._tool_stacked.setCurrentIndex(1)
            if self._er_mode:
                self._toggle_er_mode()

    # ── Mark Center ───────────────────────────────────────────────────────────

    def _toggle_mc_mode(self):
        self._mc_mode = not self._mc_mode
        print(f"[MC] _toggle_mc_mode → _mc_mode={self._mc_mode}")
        if self._mc_mode:
            self._mc_button.setStyleSheet(MC_ACTIVE_BTN)
            self._mc_button.setIcon(tabler_icon(OutlineIcon.CROSSHAIR, size=15, color='#f59e0b'))
        else:
            self._mc_button.setStyleSheet(SECONDARY_BTN)
            self._mc_button.setIcon(tabler_icon(OutlineIcon.CROSSHAIR, size=15, color=Theme.TXT))
        self._mc_button.setIconSize(QSize(15, 15))

    def _on_mc_rgb_click(self, event):
        print(f"[MC] click handler fired, _mc_mode={self._mc_mode}, button={event.button()}")
        if not self._mc_mode:
            return
        if event.button() != Qt.MouseButton.LeftButton:
            return
        rgb_widget = self.images_on_layout['rgb']
        vb = rgb_widget.plot
        in_bounds = vb.sceneBoundingRect().contains(event.scenePos())
        print(f"[MC] in_bounds={in_bounds}, scenePos={event.scenePos()}, vbRect={vb.sceneBoundingRect()}")
        if not in_bounds:
            return
        pos = vb.mapSceneToView(event.scenePos())
        print(f"[MC] viewPos=({pos.x():.1f}, {pos.y():.1f}), img_w={rgb_widget.img_w}, img_h={rgb_widget.img_h}")
        self._mc_point = (pos.x(), pos.y())

        # Image center in ViewBox coords; +x → −RA, +y → +Dec (after rot90 CW)
        cx = rgb_widget.img_w / 2.0
        cy = rgb_widget.img_h / 2.0

        try:
            ra_center = float(self.main_window.df.iloc[self.current_idx][self.current_inspection.inspection_parameters['ra column name']])
            dec_center = float(self.main_window.df.iloc[self.current_idx][self.current_inspection.inspection_parameters['dec column name']])
        except (KeyError, ValueError, TypeError, AttributeError):
            return

        pixscale = self.current_inspection.pixscale  # arcsec/pixel
        delta_x = pos.x() - cx
        delta_y = pos.y() - cy

        d_ra = -delta_x * pixscale / 3600.0 / math.cos(math.radians(dec_center))
        d_dec = delta_y * pixscale / 3600.0
        self._mc_ra = ra_center + d_ra
        self._mc_dec = dec_center + d_dec

        grader = self.current_inspection.inspection_parameters['grader name']
        col_ra = f'Center_RA_{grader}_VI'
        col_dec = f'Center_Dec_{grader}_VI'
        for col in (col_ra, col_dec):
            if col not in self.main_window.df.columns:
                self.main_window.df[col] = ''
        self.main_window.df.loc[self.current_idx, col_ra] = round(self._mc_ra, 6)
        self.main_window.df.loc[self.current_idx, col_dec] = round(self._mc_dec, 6)
        self.current_inspection.df_has_been_modified = True
        self.trigger_csv_save_thread()

        self._mc_draw_overlay()
        self._toggle_mc_mode()

    def _mc_draw_overlay(self):
        import pyqtgraph as pg
        print(f"[MC] _mc_draw_overlay called, _mc_point={self._mc_point}")
        self._mc_clear_overlay()
        if self._mc_point is None:
            return
        x, y = self._mc_point
        arm = 8
        color = '#a855f7'
        pen = pg.mkPen(color=color, width=1.5)

        h_line = pg.PlotDataItem([x - arm, x + arm], [y, y], pen=pen)
        v_line = pg.PlotDataItem([x, x], [y - arm, y + arm], pen=pen)
        dot = pg.ScatterPlotItem(
            [x], [y], size=8, pen=pg.mkPen(color=color, width=1.5),
            brush=pg.mkBrush(color), symbol='o'
        )
        vb = self.images_on_layout['rgb'].plot
        print(f"[MC] adding items at ({x:.1f}, {y:.1f}), arm={arm}, vb={vb}")
        for item in (h_line, v_line, dot):
            vb.addItem(item)
            self._mc_overlay_items.append(item)
        print(f"[MC] overlay_items count={len(self._mc_overlay_items)}")

        self._mc_overlay_visible = True

        if self._mc_ra is not None and self._mc_dec is not None:
            self._mc_result_label.setText(
                f'RA {self._mc_ra:.5f}\nDec {self._mc_dec:.5f}')
            self._mc_show_btn.setEnabled(True)
            self._mc_show_btn.setText('Hide Mark')
            self._mc_show_btn.setIcon(tabler_icon(OutlineIcon.EYE_OFF, size=15, color='#f59e0b'))
            self._mc_show_btn.setIconSize(QSize(15, 15))
            self._mc_show_btn.setStyleSheet(MC_ACTIVE_BTN)

    def _mc_clear_overlay(self):
        if hasattr(self, 'images_on_layout') and 'rgb' in self.images_on_layout:
            vb = self.images_on_layout['rgb'].plot
            for item in self._mc_overlay_items:
                vb.removeItem(item)
        self._mc_overlay_items = []

    def _mc_clear(self):
        self._mc_clear_overlay()
        self._mc_point = None
        self._mc_ra = None
        self._mc_dec = None
        self._mc_overlay_visible = False
        if hasattr(self, '_mc_result_label'):
            self._mc_result_label.setText('—')
        if hasattr(self, '_mc_show_btn'):
            self._mc_show_btn.setEnabled(False)
            self._mc_show_btn.setText('Show Mark')
            self._mc_show_btn.setIcon(tabler_icon(OutlineIcon.EYE, size=15, color=Theme.TXT))
            self._mc_show_btn.setIconSize(QSize(15, 15))
            self._mc_show_btn.setStyleSheet(SECONDARY_BTN)

    def _mc_toggle_visibility(self):
        self._mc_overlay_visible = not self._mc_overlay_visible
        for item in self._mc_overlay_items:
            item.setVisible(self._mc_overlay_visible)
        if self._mc_overlay_visible:
            self._mc_show_btn.setText('Hide Mark')
            self._mc_show_btn.setIcon(tabler_icon(OutlineIcon.EYE_OFF, size=15, color='#f59e0b'))
            self._mc_show_btn.setIconSize(QSize(15, 15))
            self._mc_show_btn.setStyleSheet(MC_ACTIVE_BTN)
        else:
            self._mc_show_btn.setText('Show Mark')
            self._mc_show_btn.setIcon(tabler_icon(OutlineIcon.EYE, size=15, color=Theme.TXT))
            self._mc_show_btn.setIconSize(QSize(15, 15))
            self._mc_show_btn.setStyleSheet(SECONDARY_BTN)

    # ── Summary screen ───────────────────────────────────────────────────────

    def _setup_summary_screen(self):
        outer = QVBoxLayout(self.summary_container_widget)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"""
            QScrollArea {{ background:transparent; border:none; }}
            QScrollBar:vertical {{
                background:{Theme.BG}; width:5px; border:none; margin:0;
            }}
            QScrollBar::handle:vertical {{
                background:{Theme.BORDER}; border-radius:2px; min-height:20px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height:0; }}
        """)

        inner = QWidget()
        inner.setStyleSheet("background:transparent;")
        lay = QVBoxLayout(inner)
        lay.setContentsMargins(52, 40, 52, 48)
        lay.setSpacing(0)

        grader = self.current_inspection.inspection_parameters['grader name']

        # ── Hero ─────────────────────────────────────────────────────────────
        grader_tag = QLabel(f'INSPECTED BY  {grader.upper()}')
        grader_tag.setStyleSheet(
            f"color:{Theme.TXT_MUTE}; font-size:11px; font-weight:600;"
            f" letter-spacing:2px; background:transparent;")
        grader_tag.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._sum_pct_lbl = QLabel('—')
        self._sum_pct_lbl.setStyleSheet(
            f"color:{Theme.ACCENT}; font-size:76px; font-weight:800;"
            f" background:transparent; line-height:1;")
        self._sum_pct_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._sum_sub_lbl = QLabel('—')
        self._sum_sub_lbl.setStyleSheet(
            f"color:{Theme.TXT_MUTE}; font-size:14px; background:transparent;")
        self._sum_sub_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._sum_prog = _SummaryProgressBar()

        lay.addWidget(grader_tag)
        lay.addSpacing(2)
        lay.addWidget(self._sum_pct_lbl)
        lay.addSpacing(6)
        lay.addWidget(self._sum_sub_lbl)
        lay.addSpacing(22)
        lay.addWidget(self._sum_prog)

        # ── Divider ──────────────────────────────────────────────────────────
        def _sep():
            s = QFrame(); s.setFrameShape(QFrame.Shape.HLine)
            s.setFixedHeight(1)
            s.setStyleSheet(f"background:{Theme.BORDER}; border:none;")
            return s

        lay.addSpacing(36)
        lay.addWidget(_sep())
        lay.addSpacing(32)

        # ── Histogram ────────────────────────────────────────────────────────
        dist_hdr = QLabel('GRADE DISTRIBUTION')
        dist_hdr.setStyleSheet(
            f"color:{Theme.TXT_MUTE}; font-size:10px; font-weight:700;"
            f" letter-spacing:2px; background:transparent;")
        self._sum_histogram = _SummaryHistogram()
        self._sum_histogram.setFixedHeight(180)

        lay.addWidget(dist_hdr)
        lay.addSpacing(18)
        lay.addWidget(self._sum_histogram)

        # ── Divider ──────────────────────────────────────────────────────────
        lay.addSpacing(32)
        lay.addWidget(_sep())
        lay.addSpacing(32)

        # ── Grade breakdown ───────────────────────────────────────────────────
        breakdown_hdr = QLabel('GRADE BREAKDOWN')
        breakdown_hdr.setStyleSheet(
            f"color:{Theme.TXT_MUTE}; font-size:10px; font-weight:700;"
            f" letter-spacing:2px; background:transparent;")
        lay.addWidget(breakdown_hdr)
        lay.addSpacing(18)

        self._sum_grades_container = QWidget()
        self._sum_grades_container.setStyleSheet("background:transparent;")
        self._sum_grades_lay = QVBoxLayout(self._sum_grades_container)
        self._sum_grades_lay.setContentsMargins(0, 0, 0, 0)
        self._sum_grades_lay.setSpacing(0)
        lay.addWidget(self._sum_grades_container)

        # ── Footer ────────────────────────────────────────────────────────────
        lay.addSpacing(32)
        lay.addWidget(_sep())
        lay.addSpacing(20)

        self._sum_footer = QLabel('')
        self._sum_footer.setStyleSheet(
            f"color:{Theme.TXT_MUTE}; font-size:12px; background:transparent;")
        self._sum_footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self._sum_footer)
        lay.addStretch()

        scroll.setWidget(inner)
        outer.addWidget(scroll)
        self._refresh_summary()

    def _refresh_summary(self):
        from collections import Counter

        grader = self.current_inspection.inspection_parameters['grader name']
        df     = self.main_window.df
        total  = len(df)

        grades_col = f'{grader}_grades'
        raw   = df[grades_col].values if grades_col in df.columns else []
        valid = [str(g).strip() for g in raw
                 if g is not None and str(g).strip() != '' and g == g]
        graded = len(valid)
        pct    = graded / total * 100 if total > 0 else 0.0

        # Hero
        if graded == 0:
            self._sum_pct_lbl.setStyleSheet(
                f"color:{Theme.TXT_MUTE}; font-size:76px; font-weight:800;"
                f" background:transparent;")
            self._sum_pct_lbl.setText('0%')
        else:
            self._sum_pct_lbl.setStyleSheet(
                f"color:{Theme.ACCENT}; font-size:76px; font-weight:800;"
                f" background:transparent;")
            self._sum_pct_lbl.setText(f'{pct:.1f}%')

        remaining = total - graded
        sub = f'{graded} of {total} systems graded'
        if remaining > 0:
            sub += f'  ·  {remaining} remaining'
        self._sum_sub_lbl.setText(sub)
        self._sum_prog.set_value(pct / 100.0)

        # Histogram
        counts = Counter(valid)
        self._sum_histogram.set_data(counts)

        # Grade rows — clear and rebuild
        while self._sum_grades_lay.count():
            item = self._sum_grades_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if counts:
            sorted_counts = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)
            max_c = sorted_counts[0][1]
            for i, (grade, count) in enumerate(sorted_counts):
                row_pct = count / graded * 100 if graded > 0 else 0
                self._sum_grades_lay.addWidget(
                    _GradeRow(grade, count, row_pct, count / max_c))
                if i < len(sorted_counts) - 1:
                    sep = QFrame()
                    sep.setFrameShape(QFrame.Shape.HLine)
                    sep.setFixedHeight(1)
                    sep.setStyleSheet(f"background:{Theme.BORDER}; border:none;")
                    self._sum_grades_lay.addWidget(sep)

        # Footer (ER / center counts)
        def _count_filled(col):
            if col not in df.columns: return 0
            n = 0
            for v in df[col].values:
                try:
                    f = float(v)
                    if f == f: n += 1
                except (ValueError, TypeError): pass
            return n

        er  = _count_filled(f'ER_arcsec_{grader}_VI')
        ctr = _count_filled(f'Center_RA_{grader}_VI')
        parts = []
        if er  > 0: parts.append(f'ER measurements: {er}')
        if ctr > 0: parts.append(f'Center marks: {ctr}')
        self._sum_footer.setText('  ·  '.join(parts) if parts else '')
        self._sum_footer.setVisible(bool(parts))

    # ── ER / MC restore ───────────────────────────────────────────────────────

    def _er_restore(self):
        self._er_clear()
        grader = self.current_inspection.inspection_parameters['grader name']
        col = f'ER_arcsec_{grader}_VI'
        if col not in self.main_window.df.columns:
            return
        try:
            val = float(self.main_window.df.iloc[self.current_idx][col])
            if val != val:
                return
        except (ValueError, TypeError):
            return
        self._er_result_label.setText(f'ER ≈ {val:.2f}″')

    def _mc_restore(self):
        self._mc_clear()
        grader = self.current_inspection.inspection_parameters['grader name']
        col_ra  = f'Center_RA_{grader}_VI'
        col_dec = f'Center_Dec_{grader}_VI'
        df = self.main_window.df
        if col_ra not in df.columns or col_dec not in df.columns:
            return
        try:
            ra_val  = float(df.iloc[self.current_idx][col_ra])
            dec_val = float(df.iloc[self.current_idx][col_dec])
            if ra_val != ra_val or dec_val != dec_val:
                return
        except (ValueError, TypeError):
            return
        # Back-project saved RA/Dec to pixel coords and redraw crosshair
        ip = self.current_inspection.inspection_parameters
        try:
            ra_t  = float(df.iloc[self.current_idx][ip['ra column name']])
            dec_t = float(df.iloc[self.current_idx][ip['dec column name']])
        except (KeyError, ValueError, TypeError):
            self._mc_result_label.setText(f'RA {ra_val:.5f}\nDec {dec_val:.5f}')
            return
        rgb_widget = self.images_on_layout['rgb']
        cx = rgb_widget.img_w / 2.0
        cy = rgb_widget.img_h / 2.0
        pix = self.current_inspection.pixscale
        px = cx - (ra_val - ra_t) * math.cos(math.radians(dec_t)) * 3600.0 / pix
        py = cy + (dec_val - dec_t) * 3600.0 / pix
        self._mc_point = (px, py)
        self._mc_ra  = ra_val
        self._mc_dec = dec_val
        self._mc_draw_overlay()

    # ─────────────────────────────────────────────────────────────────────────

    def _show_tool_help(self):
        grader = self.current_inspection.inspection_parameters['grader name']
        texts = {
            'Measure ER': (
                '<b>Einstein Radius (ER) Measurement</b><br><br>'
                'Click <i>Measure ER</i> to enter measuring mode,<br>'
                'then click two points on the RGB cutout.<br>'
                'The tool computes the angular separation between<br>'
                'the two points as an Einstein radius estimate.<br>'
                '(Pixel scale: 0.262″/px)<br><br>'
                'Use <i>Show / Hide ER</i> to toggle the overlay.<br><br>'
                f'Saved to column:<br><b>ER_arcsec_{grader}_VI</b>'
            ),
            'Mark Center': (
                '<b>Mark Center</b><br><br>'
                'Sometimes a cutout is not perfectly centred on the<br>'
                'lens. Click <i>Mark Center</i> to enter marking mode,<br>'
                'then click the true centre of the lens on the RGB<br>'
                'cutout. The RA/Dec of that pixel is recorded.<br><br>'
                'The image is <i>not</i> re-fetched — only the<br>'
                'coordinates are stored.<br><br>'
                'Use <i>Show / Hide Mark</i> to toggle the crosshair.<br><br>'
                f'Saved to columns:<br>'
                f'<b>Center_RA_{grader}_VI</b><br>'
                f'<b>Center_Dec_{grader}_VI</b>'
            ),
        }
        text = texts.get(self._tool_dropdown.currentText(), '')
        QToolTip.showText(QCursor.pos(), text, self._tool_help_btn,
                          self._tool_help_btn.rect(), 10000)

    def _setup_tools_panel(self):
        self.tools_panel.layout.setContentsMargins(12, 8, 12, 12)
        self.tools_panel.layout.setSpacing(8)

        # Generate a chevron-down PNG once for the QSS ::down-arrow
        _arrow_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), '_combo_arrow.png'
        ).replace('\\', '/')
        if not os.path.exists(_arrow_path):
            tabler_pixmap(OutlineIcon.CHEVRON_DOWN, size=12, color=Theme.TXT_MUTE).save(_arrow_path)

        _combo_qss = f"""
            QComboBox {{
                background-color: #1c2a42; color: {Theme.TXT};
                border: 1px solid #33425c; border-radius: 8px;
                font-size: 13px; font-weight: 600; padding: 0 10px;
            }}
            QComboBox:hover {{ background-color: #243a5a; }}
            QComboBox::drop-down {{
                subcontrol-origin: border;
                subcontrol-position: center right;
                width: 26px;
                border-left: 1px solid #33425c;
                border-top-right-radius: 7px;
                border-bottom-right-radius: 7px;
            }}
            QComboBox::down-arrow {{
                image: url("{_arrow_path}");
                width: 12px; height: 12px;
            }}
            QComboBox QAbstractItemView {{
                background-color: #1c2a42; color: {Theme.TXT};
                selection-background-color: {Theme.ACCENT}; outline: none;
            }}
            QComboBox QAbstractItemView::item {{ color: {Theme.TXT}; padding: 4px 10px; }}
        """

        # "Select Tool:" label above the dropdown row
        tool_lbl = QLabel("Select Tool:")
        tool_lbl.setStyleSheet(
            f"color:{Theme.TXT_MUTE}; font-size:11px; font-weight:700; "
            f"letter-spacing:0.5px; background:transparent;")
        self.tools_panel.layout.addWidget(tool_lbl)

        # Dropdown + ? help button
        dropdown_row = QHBoxLayout()
        dropdown_row.setContentsMargins(0, 0, 0, 0)
        dropdown_row.setSpacing(6)

        self._tool_dropdown = QComboBox()
        self._tool_dropdown.addItems(['Measure ER', 'Mark Center'])
        self._tool_dropdown.setItemDelegate(QStyledItemDelegate(self._tool_dropdown))
        self._tool_dropdown.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._tool_dropdown.setFixedHeight(30)
        self._tool_dropdown.setStyleSheet(_combo_qss)
        self._tool_dropdown.currentTextChanged.connect(self._on_tool_changed)

        self._tool_help_btn = QPushButton('?')
        self._tool_help_btn.setFixedSize(30, 30)
        self._tool_help_btn.clicked.connect(self._show_tool_help)
        self._tool_help_btn.setStyleSheet(f"""
            QPushButton {{ background-color:transparent; border:1px solid #33425c;
                           border-radius:6px; color:{Theme.TXT_MUTE};
                           font-size:13px; font-weight:700; }}
            QPushButton:hover {{ background-color:#1c2a42; color:{Theme.TXT_SOFT}; }}
        """)

        dropdown_row.addWidget(self._tool_dropdown, 1)
        dropdown_row.addWidget(self._tool_help_btn)
        self.tools_panel.layout.addLayout(dropdown_row)

        # Stacked widget — page 0: ER tool, page 1: Mark Center tool
        self._tool_stacked = QStackedWidget()
        self._tool_stacked.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        # ── Page 0: Measure ER ────────────────────────────────────────
        er_page = QWidget()
        er_page.setStyleSheet("background: transparent;")
        er_layout = QVBoxLayout(er_page)
        er_layout.setContentsMargins(0, 0, 0, 0)
        er_layout.setSpacing(6)

        self._er_result_label = QLabel("—")
        self._er_result_label.setStyleSheet(
            f"color:{Theme.ACCENT}; font-size:15px; font-weight:700; background:transparent;")
        self._er_result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        er_layout.addWidget(self._er_result_label)

        self._er_button = QPushButton('Measure ER')
        self._er_button.setFixedHeight(30)
        self._er_button.setStyleSheet(SECONDARY_BTN)
        self._er_button.setIcon(tabler_icon(OutlineIcon.RULER_MEASURE, size=15, color=Theme.TXT))
        self._er_button.setIconSize(QSize(15, 15))
        self._er_button.clicked.connect(self._toggle_er_mode)
        er_layout.addWidget(self._er_button)

        self._er_show_btn = QPushButton('Show ER')
        self._er_show_btn.setFixedHeight(30)
        self._er_show_btn.setIcon(tabler_icon(OutlineIcon.EYE, size=15, color=Theme.TXT))
        self._er_show_btn.setIconSize(QSize(15, 15))
        self._er_show_btn.setStyleSheet(SECONDARY_BTN)
        self._er_show_btn.setEnabled(False)
        self._er_show_btn.clicked.connect(self._er_toggle_visibility)
        er_layout.addWidget(self._er_show_btn)

        self._tool_stacked.addWidget(er_page)

        # ── Page 1: Mark Center ───────────────────────────────────────
        mc_page = QWidget()
        mc_page.setStyleSheet("background: transparent;")
        mc_layout = QVBoxLayout(mc_page)
        mc_layout.setContentsMargins(0, 0, 0, 0)
        mc_layout.setSpacing(6)

        self._mc_result_label = QLabel("—")
        self._mc_result_label.setStyleSheet(
            f"color:#f59e0b; font-size:13px; font-weight:600; background:transparent;")
        self._mc_result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mc_layout.addWidget(self._mc_result_label)

        self._mc_button = QPushButton('Mark Center')
        self._mc_button.setFixedHeight(30)
        self._mc_button.setStyleSheet(SECONDARY_BTN)
        self._mc_button.setIcon(tabler_icon(OutlineIcon.CROSSHAIR, size=15, color=Theme.TXT))
        self._mc_button.setIconSize(QSize(15, 15))
        self._mc_button.clicked.connect(self._toggle_mc_mode)
        mc_layout.addWidget(self._mc_button)

        self._mc_show_btn = QPushButton('Show Mark')
        self._mc_show_btn.setFixedHeight(30)
        self._mc_show_btn.setIcon(tabler_icon(OutlineIcon.EYE, size=15, color=Theme.TXT))
        self._mc_show_btn.setIconSize(QSize(15, 15))
        self._mc_show_btn.setStyleSheet(SECONDARY_BTN)
        self._mc_show_btn.setEnabled(False)
        self._mc_show_btn.clicked.connect(self._mc_toggle_visibility)
        mc_layout.addWidget(self._mc_show_btn)

        self._tool_stacked.addWidget(mc_page)

        self.tools_panel.layout.addWidget(self._tool_stacked)
        self.tools_panel.layout.addStretch()

    # ─────────────────────────────────────────────────────────────────────────

    def _start_prefetch(self, idx):
        n = len(self.main_window.df)
        if idx < 0 or idx >= n:
            return
        if self.current_inspection.is_cached(idx):
            return
        existing = self._prefetch_threads.get(idx)
        if existing and existing.isRunning():
            return
        thread = PrefetchThread(self.current_inspection, idx)
        thread.fetched.connect(self._on_prefetch_done)
        thread.finished.connect(lambda i=idx: self._prefetch_threads.pop(i, None))
        self._prefetch_threads[idx] = thread
        thread.start()
        print(f'[Prefetch] started idx={idx}')

    def _on_prefetch_done(self, rgb, grz, idx, layer):
        if layer != self.current_inspection.layer:
            print(f'[Prefetch] discarding idx={idx} (stale layer)')
            return
        if not self.current_inspection.is_cached(idx):
            self.current_inspection.add_to_cache([rgb, grz], idx)

    def _stop_all_prefetches(self):
        for thread in list(self._prefetch_threads.values()):
            if thread.isRunning():
                thread.quit()
                thread.wait(500)
        self._prefetch_threads.clear()

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
        if event.type() == QEvent.Type.KeyPress:
            if obj not in (self.grade_input.text_edit, self.comment_input.text_edit) or obj.isReadOnly():
                if event.key() == Qt.Key.Key_Right and self.next_system_button.isEnabled():
                    self.load_next_system()
                    return True
                if event.key() == Qt.Key.Key_Left and self.previous_system_button.isEnabled():
                    self.load_previous_system()
                    return True
            if self.quick_inspection_activated:
                if event.key() in self._advance_keys():
                    self._advance_focus()
                    return True
        return super().eventFilter(obj, event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Right and self.next_system_button.isEnabled():
            self.load_next_system()
        elif event.key() == Qt.Key.Key_Left and self.previous_system_button.isEnabled():
            self.load_previous_system()
        else:
            super().keyPressEvent(event)
    
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