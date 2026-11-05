from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSpacerItem, QSizePolicy,QGridLayout,QApplication, QStackedWidget,QLabel,QMessageBox,QFrame,QGraphicsDropShadowEffect,QComboBox,QStyledItemDelegate,QDialog,QPushButton,QSlider,QToolTip,QProgressBar,QScrollArea,QTableWidget,QTableWidgetItem,QHeaderView
from PyQt6.QtCore import Qt, QUrl,QThread, pyqtSignal, QEvent, QPropertyAnimation, QParallelAnimationGroup, QEasingCurve, QPoint, QSize, QTimer
from PyQt6.QtGui import QPainter, QDesktopServices, QColor, QCursor, QBrush, QPen, QFont, QImage, QPixmap
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtCore import QRectF

import os
import math
import numpy as np
import time
# from Assets import SvgWidget, ImageWidget, InputField, ClickEffectButton
from Assets import Panel,SvgWidget, ImageWidget, StyledTextBox, MetadataField, ClickEffectStyleButton, StyledText, StyledInputBox,StatusWidget,CheckBox,StyledTabBar,InspectionSettings,ScrollPanel,StyledGroupBox,VoiceOverIndicator,SystemJumpWidget,SCROLLBAR_SS,save_recent
from InspectionEngine import Inspection, PrefetchThread
import Theme
from Icons import tabler_icon, tabler_pixmap, badge_pixmap, OutlineIcon, ICON_WHITE, ICON_SOFT
try:
    from VoiceOverEngine import VoiceOverThread
    _VOICEOVER_AVAILABLE = True
except Exception as _vo_import_err:
    _VOICEOVER_AVAILABLE = False
    print(f"[VoiceOver] import failed: {_vo_import_err}")

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

# ─── Pace bar ─────────────────────────────────────────────────────────────────

class PaceBar(QWidget):
    """
    A razor-thin full-width bar that drains left-to-right as time elapses.

    Color interpolates smoothly:
      full → 33% left : accent blue → amber
      33% → 0%        : amber → red

    Non-intrusive by design — no labels, no alarms. Call set_fraction(1.0)
    when a new system loads, then drive it with set_fraction() from a QTimer.
    """
    _C_FULL = QColor(74, 158, 255)   # accent blue
    _C_WARN = QColor(245, 158, 11)   # amber
    _C_CRIT = QColor(239, 68, 68)    # red

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(4)
        self._frac = 1.0

    def set_fraction(self, frac: float):
        self._frac = max(0.0, min(1.0, frac))
        self.update()

    @staticmethod
    def _lerp(c1, c2, t):
        t = max(0.0, min(1.0, t))
        return QColor(
            int(c1.red()   + (c2.red()   - c1.red())   * t),
            int(c1.green() + (c2.green() - c1.green()) * t),
            int(c1.blue()  + (c2.blue()  - c1.blue())  * t),
        )

    def _bar_color(self):
        f = self._frac
        if f >= 0.33:
            return self._lerp(self._C_FULL, self._C_WARN, (1.0 - f) / 0.67)
        else:
            return self._lerp(self._C_WARN, self._C_CRIT, (0.33 - f) / 0.33)

    def paintEvent(self, event):
        p = QPainter(self)
        r = self.rect()
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(Theme.FIELD)))
        p.drawRect(r)
        fw = max(0, int(r.width() * self._frac))
        if fw > 0:
            p.setBrush(QBrush(self._bar_color()))
            p.drawRect(0, 0, fw, r.height())
        p.end()


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


class ReviewFetchThread(QThread):
    """Fetches a single RGB thumbnail for the Review grid."""
    thumbnail_ready = pyqtSignal(int, object)  # (idx, ndarray | None)

    def __init__(self, inspection, idx, ra, dec, cutout_size=80):
        super().__init__()
        self._inspection = inspection
        self._idx = idx
        self._ra = ra
        self._dec = dec
        self._cutout_size = cutout_size

    def run(self):
        if self._inspection.is_cached(self._idx):
            ok, rgb, _, _ = self._inspection.pull_from_cache(self._idx)
            if ok and rgb is not None:
                self.thumbnail_ready.emit(self._idx, rgb)
                return
        ok, arr = self._inspection.get_rgb_cutout(
            self._ra, self._dec, cutout_size=self._cutout_size)
        self.thumbnail_ready.emit(self._idx, arr if ok else None)


class _ReviewCard(QWidget):
    """A thumbnail card in the Review grid."""
    clicked = pyqtSignal(int)
    THUMB = 80

    def __init__(self, idx, grade, parent=None):
        super().__init__(parent)
        self._idx = idx
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setObjectName("reviewCard")
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFixedWidth(self.THUMB + 12)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(6, 6, 6, 6)
        lay.setSpacing(4)

        self._img_label = QLabel()
        self._img_label.setFixedSize(self.THUMB, self.THUMB)
        self._img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._img_label.setStyleSheet(
            "background:#1a2d48; border-radius:5px; border:1px solid #2a3d5a;")

        info = QHBoxLayout()
        info.setContentsMargins(0, 0, 0, 0)
        info.setSpacing(2)
        sys_lbl = QLabel(f'#{idx + 1}')
        sys_lbl.setStyleSheet(
            f"color:{Theme.TXT_MUTE}; font-size:10px; background:transparent;")
        grade_lbl = QLabel(grade)
        grade_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        grade_lbl.setStyleSheet(
            f"color:{Theme.ACCENT}; font-size:12px; font-weight:700; background:transparent;")
        info.addWidget(sys_lbl)
        info.addStretch()
        info.addWidget(grade_lbl)

        lay.addWidget(self._img_label)
        lay.addLayout(info)

        self._apply_style(hover=False)

    def _apply_style(self, hover):
        if hover:
            self.setStyleSheet(
                f"QWidget#reviewCard {{ background:#1a2d48; border:1px solid {Theme.ACCENT}; "
                f"border-radius:8px; }}")
        else:
            self.setStyleSheet(
                f"QWidget#reviewCard {{ background:#152238; border:1px solid {Theme.BORDER}; "
                f"border-radius:8px; }}")

    def set_image(self, arr):
        if arr is None:
            return
        arr = np.ascontiguousarray(arr)
        h, w = arr.shape[:2]
        img = QImage(arr.data, w, h, w * 3, QImage.Format.Format_RGB888)
        pix = QPixmap.fromImage(img).scaled(
            self.THUMB, self.THUMB,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation)
        self._img_label.setPixmap(pix)
        self._img_label.setStyleSheet("background:transparent; border-radius:5px;")

    def enterEvent(self, event):
        self._apply_style(hover=True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._apply_style(hover=False)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._idx)
        super().mousePressEvent(event)


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
        self.voiceover_checkbox.checkbox.setToolTip(
            'Voice commands: "Grade A" · "Comment [text]" · "Next" · "Previous"'
        )
        # self.lock_inspection_toggle = StyledToggleSwitch("Lock Grades & Comments")

        # Labels:
        self.system_N_tracker = SystemJumpWidget()
        self.system_N_tracker.jump_requested.connect(self._jump_to_system)
        self.save_status_widget = StatusWidget(text='Autosaving on', color='green', dot_size=12)

        #Add items to bottom panel — built below after PaceBar is created

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

        # Pace bar — sandwiched between Previous and Next buttons
        self._pace_bar = PaceBar()
        self._pace_bar.hide()
        self._pace_start = 0.0
        self._pace_elapsed_paused = 0.0
        self._pace_timer = QTimer(self)
        self._pace_timer.setInterval(100)
        self._pace_timer.timeout.connect(self._pace_tick)

        # Build bottom panel: [prev] [4 px bar, vertically centred] [next]
        _pace_wrap = QWidget()
        _pace_wrap.setStyleSheet("background: transparent;")
        _pace_wrap_lay = QVBoxLayout(_pace_wrap)
        _pace_wrap_lay.setContentsMargins(12, 0, 12, 0)
        _pace_wrap_lay.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        _pace_wrap_lay.addWidget(self._pace_bar)
        self.bottom_panel.layout.setContentsMargins(14, 8, 14, 8)
        self.bottom_panel.layout.addWidget(self.previous_system_button)
        self.bottom_panel.layout.addWidget(_pace_wrap, 1)
        self.bottom_panel.layout.addWidget(self.next_system_button)

        self.window_layout.addWidget(self.bottom_panel, 2)

        # Settings window:
        self._create_settings_window()

        #Inspection (non-GUI)
        self.current_inspection = Inspection(self.main_window)
        self.current_inspection.simulation_mode = False
        self.CSV_save_path = self.current_inspection.inspection_parameters['save directory']+f'/{self.current_inspection.inspection_parameters['new df name']}.csv'
        save_recent(self.CSV_save_path)

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

        # New Inspection button — far left of the top bar
        _new_insp_btn = QPushButton(' New Inspection')
        _new_insp_btn.setIcon(tabler_icon(OutlineIcon.HOME, size=14, color='white'))
        _new_insp_btn.setIconSize(QSize(14, 14))
        _new_insp_btn.setFixedHeight(30)
        _new_insp_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        _new_insp_btn.setStyleSheet(f"""
            QPushButton {{ background-color:{Theme.ACCENT}; color:white; border:none;
                           border-radius:8px; font-size:13px; font-weight:700; padding:0 12px; }}
            QPushButton:hover {{ background-color:{Theme.ACCENT_HI}; }}
            QPushButton:pressed {{ background-color:{Theme.ACCENT_LO}; }}
        """)
        _new_insp_btn.clicked.connect(self._new_inspection)
        _sep = QFrame()
        _sep.setFrameShape(QFrame.Shape.VLine)
        _sep.setFixedSize(1, 22)
        _sep.setStyleSheet(f"background:{Theme.BORDER}; border:none;")
        self.top_panel.layout.insertWidget(0, _new_insp_btn)
        self.top_panel.layout.insertWidget(1, _sep)
        
    def _new_inspection(self):
        from Assets import show_branded_dialog
        confirmed = show_branded_dialog(
            self, 'New Inspection',
            'Your grades have been autosaved.\nReturn to the welcome screen?',
            icon=OutlineIcon.HOME, icon_bg=Theme.ACCENT,
            confirm=True, yes_label='New Inspection', no_label='Cancel',
        )
        if confirmed:
            self._stop_all_prefetches()
            self.main_window.switch_screens(0)

    def _switch_screens(self,to_screen='settings'):
        if self.animating:
            return
        if self.current_screen == 'inspection' and to_screen != 'inspection':
            self._pace_pause()
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
            self._pace_resume()
            if self.vo_thread is not None and self.voiceover_checkbox.checkbox.isChecked():
                self.vo_thread.start_listening()
                self._vo_idle_timer.start()
        elif self.to_screen == 'summary':
            if self.vo_thread is not None:
                self.vo_thread.stop_listening()
                self._vo_idle_timer.stop()
                self.voiceover_status_widget.hide()
            if hasattr(self, '_sum_histogram'):
                self._refresh_summary()
            if hasattr(self, '_review_cards'):
                self._refresh_review_grid()
        elif self.to_screen == 'settings':
            if self.vo_thread is not None:
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
        _settings_tab_icons = {
            'Grades and Comments': OutlineIcon.WRITING,
            'Quick Inspection':    OutlineIcon.BOLT,
            'Navigation':          OutlineIcon.ROUTE,
            'Appearance':          OutlineIcon.PALETTE,
            'Info':                OutlineIcon.INFO_CIRCLE,
        }
        self.settings_menu_tabs = StyledTabBar(self.dict_of_settings_menus,
                                               orientation='vertical',
                                               add_stretches=True,
                                               icons=_settings_tab_icons)
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
        # Apply default survey before fetching first images
        _default_survey = str(self.Settings.get_setting('default_survey') or 'DR10')
        self.current_inspection.set_survey(_default_survey.lower())

        # Generate chevron-down PNG once for QSS ::down-arrow (used by both combo boxes)
        self._arrow_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), '_combo_arrow.png'
        ).replace('\\', '/')
        if not os.path.exists(self._arrow_path):
            tabler_pixmap(OutlineIcon.CHEVRON_DOWN, size=12, color=Theme.TXT_MUTE).save(self._arrow_path)

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
        small_cutout_panel_size = max(120, min(int(self.main_window.height() * 0.17), 240))
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
        self._add_scalebar_compass(rgb_image)
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
        self.dr_dropdown.setCurrentText(_default_survey)
        self.dr_dropdown.setItemDelegate(QStyledItemDelegate(self.dr_dropdown))
        self.dr_dropdown.setFixedSize(110, 30)
        self.dr_dropdown.setStyleSheet(f"""
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
                image: url("{self._arrow_path}");
                width: 12px; height: 12px;
            }}
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
        self.ra_box=MetadataField('R.A. [deg]', str(metadata['ra']), mono=True)
        self.dec_box=MetadataField('Dec. [deg]', str(metadata['dec']), mono=True)
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
        if _VOICEOVER_AVAILABLE:
            self.vo_thread = VoiceOverThread(model_size='base', parent=self)
            self.vo_thread.listening.connect(self._on_vo_listening)
            self.vo_thread.processing.connect(self._on_vo_processing)
            self.vo_thread.transcript_ready.connect(self._on_vo_transcript)
            self.vo_thread.status_update.connect(self._on_vo_status)
            self.vo_thread.command_parsed.connect(self._handle_voice_command)
            self.vo_thread.error.connect(self._on_vo_error)
        else:
            self.vo_thread = None
            self.voiceover_checkbox.checkbox.setEnabled(False)
            self.voiceover_checkbox.checkbox.setToolTip("VoiceOver requires pyaudio and webrtcvad")

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
        self._pace_reset()

    # ── Navigation helpers ────────────────────────────────────────────

    def _update_nav_buttons(self):
        loop = bool(self.Settings.get_setting('loop_at_end'))
        self.previous_system_button.setEnabled(loop or self.current_idx > 0)
        self.next_system_button.setEnabled(loop or self.current_idx < self.N_total_systems - 1)

    def _warn_if_regrading(self, target_idx) -> bool:
        if not bool(self.Settings.get_setting('warn_regrading')):
            return True
        grader = self.current_inspection.inspection_parameters['grader name']
        grades_col = f'{grader}_grades'
        df = self.main_window.df
        if grades_col not in df.columns:
            return True
        existing = str(df.iloc[target_idx][grades_col]).strip()
        if existing and existing != 'nan':
            reply = self._warn(
                'System Already Graded',
                f'System #{target_idx + 1} already has grade "{existing}". Navigate to it?',
                confirm=True)
            return reply
        return True

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
        from Assets import show_branded_dialog
        from Icons import OutlineIcon
        return show_branded_dialog(
            self, title, text,
            icon=OutlineIcon.ALERT_TRIANGLE,
            icon_bg='#f59e0b',
            confirm=confirm,
            yes_label='Continue', no_label='Cancel',
        )

    def _rebuild_focus_order(self):
        field_map = {'Grade': self.grade_input, 'Comment': self.comment_input}
        field_order = self.Settings.get_setting('quick_inspection_field_order') or []
        ordered = [field_map[f] for f in field_order if f in field_map]
        self.focus_order = (ordered if ordered else list(field_map.values())) + [self.next_system_button]
        self.focus_i = 0

    def _apply_caps_lock_settings(self):
        self.grade_input.set_caps_lock(bool(self.Settings.get_setting('caplock_grades')))
        self.comment_input.set_caps_lock(bool(self.Settings.get_setting('caplock_comments')))

    # ── Pace timer ────────────────────────────────────────────────────

    def _pace_reset(self):
        """Start (or restart) the per-system countdown from full."""
        pace = int(self.Settings.get_setting('pace_seconds') or 0)
        if pace > 0:
            self._pace_elapsed_paused = 0.0
            self._pace_start = time.monotonic()
            self._pace_bar.set_fraction(1.0)
            self._pace_bar.show()
            if not self._pace_timer.isActive():
                self._pace_timer.start()
        else:
            self._pace_timer.stop()
            self._pace_bar.hide()

    def _pace_pause(self):
        """Freeze the timer (e.g. user switched to settings/summary)."""
        if self._pace_timer.isActive():
            self._pace_elapsed_paused += time.monotonic() - self._pace_start
            self._pace_timer.stop()
        self._pace_bar.hide()

    def _pace_resume(self):
        """Unfreeze the timer when returning to the inspection screen."""
        pace = int(self.Settings.get_setting('pace_seconds') or 0)
        if pace <= 0:
            return
        elapsed = self._pace_elapsed_paused
        if elapsed < pace:
            self._pace_bar.set_fraction(max(0.0, 1.0 - elapsed / pace))
            self._pace_bar.show()
            self._pace_start = time.monotonic()
            self._pace_timer.start()
        else:
            self._pace_bar.set_fraction(0.0)
            self._pace_bar.show()

    def _pace_tick(self):
        pace = int(self.Settings.get_setting('pace_seconds') or 0)
        if pace <= 0:
            self._pace_timer.stop()
            self._pace_bar.hide()
            return
        elapsed = self._pace_elapsed_paused + (time.monotonic() - self._pace_start)
        frac = max(0.0, 1.0 - elapsed / pace)
        self._pace_bar.set_fraction(frac)
        if frac <= 0.0:
            self._pace_timer.stop()

    # ── VoiceOver ─────────────────────────────────────────────────────

    def _toggle_voiceover(self, state):
        if self.vo_thread is None:
            return
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
        badge_lbl = QLabel()
        badge_lbl.setPixmap(badge_pixmap(OutlineIcon.MICROPHONE, diameter=56, icon_size=26,
                                         icon_color=ICON_WHITE, bg_color=Theme.ACCENT))
        badge_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge_lbl.setStyleSheet("background: transparent;")
        badge_wrapper = QHBoxLayout()
        badge_wrapper.addStretch()
        badge_wrapper.addWidget(badge_lbl)
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
            self._show_voiceover_tutorial()
            return True
        return False

    def _show_voiceover_tutorial(self):
        dlg = QDialog(self)
        dlg.setWindowTitle('VoiceOver')
        dlg.setModal(True)
        dlg.setFixedWidth(420)
        dlg.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        dlg.setStyleSheet(f"""
            QDialog {{
                background-color: {Theme.SURFACE};
                border: 1px solid {Theme.BORDER};
                border-radius: 14px;
            }}
            QLabel {{ background: transparent; }}
        """)

        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(28, 28, 28, 22)
        layout.setSpacing(0)

        # Header
        title_lbl = QLabel("You're all set!")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_lbl.setStyleSheet(
            f"color:{Theme.TXT}; font-size:17px; font-weight:700;")
        layout.addWidget(title_lbl)
        layout.addSpacing(6)

        sub_lbl = QLabel("Speak any of these commands while VoiceOver is active:")
        sub_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub_lbl.setWordWrap(True)
        sub_lbl.setStyleSheet(f"color:{Theme.TXT_MUTE}; font-size:13px;")
        layout.addWidget(sub_lbl)
        layout.addSpacing(22)

        # Command rows
        _commands = [
            (OutlineIcon.STAR,         Theme.ACCENT,  'Grade A, B, C …',
             'Sets the grade for the current system'),
            (OutlineIcon.WRITING,      '#a855f7',     'Comment [your text]',
             'Adds or replaces the comment field'),
            (OutlineIcon.ARROW_RIGHT,  '#22c55e',     'Next',
             'Advances to the next system'),
            (OutlineIcon.ARROW_LEFT,   '#f59e0b',     'Previous',
             'Goes back to the previous system'),
        ]

        for icon, color, cmd, desc in _commands:
            row_w = QWidget()
            row_w.setStyleSheet(
                f"background:{Theme.CARD}; border-radius:10px;")
            row_w.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
            row_h = QHBoxLayout(row_w)
            row_h.setContentsMargins(14, 12, 14, 12)
            row_h.setSpacing(14)

            icon_lbl = QLabel()
            icon_lbl.setPixmap(
                badge_pixmap(icon, diameter=34, icon_size=17,
                             icon_color=ICON_WHITE, bg_color=color))
            icon_lbl.setFixedSize(34, 34)
            row_h.addWidget(icon_lbl)

            text_col = QVBoxLayout()
            text_col.setSpacing(2)
            cmd_lbl = QLabel(f'"{cmd}"')
            cmd_lbl.setStyleSheet(
                f"color:{Theme.TXT}; font-size:13px; font-weight:700;")
            desc_lbl = QLabel(desc)
            desc_lbl.setStyleSheet(
                f"color:{Theme.TXT_MUTE}; font-size:12px;")
            text_col.addWidget(cmd_lbl)
            text_col.addWidget(desc_lbl)
            row_h.addLayout(text_col)
            row_h.addStretch()

            layout.addWidget(row_w)
            layout.addSpacing(8)

        layout.addSpacing(14)

        # Divider
        div = QFrame()
        div.setFixedHeight(1)
        div.setStyleSheet(f"background:{Theme.BORDER}; border:none;")
        layout.addWidget(div)
        layout.addSpacing(16)

        # Got it button
        got_it = QPushButton("Got it")
        got_it.setFixedHeight(38)
        got_it.setStyleSheet(f"""
            QPushButton {{
                background:{Theme.ACCENT}; color:white; border:none;
                border-radius:8px; font-size:14px; font-weight:700;
            }}
            QPushButton:hover {{ background:{Theme.ACCENT_HI}; }}
            QPushButton:pressed {{ background:{Theme.ACCENT_LO}; }}
        """)
        got_it.clicked.connect(dlg.accept)
        layout.addWidget(got_it)

        dlg.exec()

    def _vo_idle_timeout(self):
        if self.vo_thread is None:
            return
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
            if not reply:
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
            if not reply:
                return False

        return True

    def load_next_system(self):
        if not self._validate_navigation():
            return
        loop = bool(self.Settings.get_setting('loop_at_end'))
        if self.current_idx == self.N_total_systems - 1:
            target = 0 if loop else None
        else:
            target = self.current_idx + 1
        if target is None:
            return
        if not self._warn_if_regrading(target):
            return
        self.current_inspection.update_df({'grade': self.grade_input.get_content(), 'comment': self.comment_input.get_content()})
        self.current_inspection.df_has_been_modified = True
        self.trigger_csv_save_thread()
        self.current_idx = target
        self._update_nav_buttons()
        self.update_onscreen_data()
        if self.quick_inspection_activated:
            self.focus_order[0].setFocus()
            self.focus_i = 0

    def load_previous_system(self):
        if not self._validate_navigation():
            return
        loop = bool(self.Settings.get_setting('loop_at_end'))
        if self.current_idx == 0:
            target = self.N_total_systems - 1 if loop else None
        else:
            target = self.current_idx - 1
        if target is None:
            return
        if not self._warn_if_regrading(target):
            return
        self.current_inspection.update_df({'grade': self.grade_input.get_content(), 'comment': self.comment_input.get_content()})
        self.current_idx = target
        self._update_nav_buttons()
        self.update_onscreen_data()
        if self.quick_inspection_activated:
            self.focus_order[0].setFocus()
            self.focus_i = 0

    def _jump_to_system(self, idx, warn_regrading=True):
        if idx == self.current_idx:
            return
        if not self._validate_navigation():
            return
        if warn_regrading and not self._warn_if_regrading(idx):
            return
        self.current_inspection.update_df({'grade': self.grade_input.get_content(), 'comment': self.comment_input.get_content()})
        self.current_inspection.df_has_been_modified = True
        self.trigger_csv_save_thread()
        self.current_idx = idx
        self._update_nav_buttons()
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

        # Reset contrast sliders if setting is on
        if bool(self.Settings.get_setting('reset_contrast_on_nav')) and hasattr(self, 'contrast_sliders'):
            for slider in self.contrast_sliders.values():
                slider.setValue(50)

        self._start_prefetch(self.current_idx + 1)
        self._pace_reset()

        # Keep summary stats in sync with current inspection state
        if hasattr(self, '_sum_histogram'):
            self._refresh_summary()

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

    def _add_scalebar_compass(self, rgb_widget):
        import pyqtgraph as pg
        vb  = rgb_widget.plot
        pix = self.current_inspection.pixscale   # 0.262 arcsec/px
        img_w = rgb_widget.img_w                 # 101
        img_h = rgb_widget.img_h                 # 101

        pen = pg.mkPen(color=(255, 255, 255, 200), width=1.5)
        font = QFont()
        font.setPointSize(9)

        # ── Scale bar (bottom-left, 5 arcsec) ────────────────────────
        bar_arcsec = 5.0
        bar_px = bar_arcsec / pix   # ≈ 19.1 px
        pad = 5
        x0, y0 = float(pad), float(pad)
        x1 = x0 + bar_px
        tick_h = 3.0

        bar_line = pg.PlotDataItem([x0, x1],   [y0, y0],              pen=pen)
        tick_l   = pg.PlotDataItem([x0, x0],   [y0, y0 + tick_h],     pen=pen)
        tick_r   = pg.PlotDataItem([x1, x1],   [y0, y0 + tick_h],     pen=pen)
        bar_lbl  = pg.TextItem('5ʺ', color=(255, 255, 255), anchor=(0.5, 1.0))
        bar_lbl.setFont(font)
        bar_lbl.setPos((x0 + x1) / 2, y0 + tick_h + 1)

        for item in (bar_line, tick_l, tick_r, bar_lbl):
            vb.addItem(item)

        # ── Compass (bottom-right) ────────────────────────────────────
        # ViewBox orientation: +x → −RA (West), +y → +Dec (North)
        # Therefore: North = +y, East = −x
        arm = 7.0
        cx  = float(img_w) - 12.0
        cy  = 10.0

        n_line = pg.PlotDataItem([cx, cx],       [cy, cy + arm],             pen=pen)
        n_head = pg.PlotDataItem([cx-2, cx, cx+2], [cy+arm-3, cy+arm, cy+arm-3], pen=pen)
        e_line = pg.PlotDataItem([cx, cx - arm], [cy, cy],                   pen=pen)
        e_head = pg.PlotDataItem([cx-arm+3, cx-arm, cx-arm+3], [cy-2, cy, cy+2], pen=pen)

        n_lbl = pg.TextItem('N', color=(255, 255, 255), anchor=(0.5, 1.0))
        n_lbl.setFont(font)
        n_lbl.setPos(cx, cy + arm + 1)

        e_lbl = pg.TextItem('E', color=(255, 255, 255), anchor=(1.0, 0.5))
        e_lbl.setFont(font)
        e_lbl.setPos(cx - arm - 1, cy)

        for item in (n_line, n_head, e_line, e_head, n_lbl, e_lbl):
            vb.addItem(item)

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
        if self._mc_mode:
            self._mc_button.setStyleSheet(MC_ACTIVE_BTN)
            self._mc_button.setIcon(tabler_icon(OutlineIcon.CROSSHAIR, size=15, color='#f59e0b'))
        else:
            self._mc_button.setStyleSheet(SECONDARY_BTN)
            self._mc_button.setIcon(tabler_icon(OutlineIcon.CROSSHAIR, size=15, color=Theme.TXT))
        self._mc_button.setIconSize(QSize(15, 15))

    def _on_mc_rgb_click(self, event):
        if not self._mc_mode:
            return
        if event.button() != Qt.MouseButton.LeftButton:
            return
        rgb_widget = self.images_on_layout['rgb']
        vb = rgb_widget.plot
        in_bounds = vb.sceneBoundingRect().contains(event.scenePos())
        if not in_bounds:
            return
        pos = vb.mapSceneToView(event.scenePos())
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
        for item in (h_line, v_line, dot):
            vb.addItem(item)
            self._mc_overlay_items.append(item)

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
        scroll.setStyleSheet(f"QScrollArea {{ background:transparent; border:none; }}" + SCROLLBAR_SS)

        inner = QWidget()
        inner.setStyleSheet("background:transparent;")
        lay = QVBoxLayout(inner)
        lay.setContentsMargins(52, 40, 52, 48)
        lay.setSpacing(0)

        grader = self.current_inspection.inspection_parameters['grader name']

        # ── Section header helper (white text + blue accent bar) ──────────────
        def _section_header(title):
            w = QWidget()
            w.setStyleSheet("background:transparent;")
            h = QHBoxLayout(w)
            h.setContentsMargins(0, 0, 0, 0)
            h.setSpacing(10)
            bar = QFrame()
            bar.setFixedSize(3, 22)
            bar.setStyleSheet(f"background:{Theme.ACCENT}; border-radius:1px; border:none;")
            lbl = QLabel(title)
            lbl.setStyleSheet(
                f"color:{Theme.TXT}; font-size:17px; font-weight:700; background:transparent;")
            h.addWidget(bar)
            h.addWidget(lbl)
            h.addStretch()
            return w

        def _sep():
            s = QFrame()
            s.setFrameShape(QFrame.Shape.HLine)
            s.setFixedHeight(1)
            s.setStyleSheet(f"background:{Theme.BORDER}; border:none;")
            return s

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

        lay.addSpacing(36)
        lay.addWidget(_sep())
        lay.addSpacing(32)

        # ── Grade Distribution (histogram) ────────────────────────────────────
        lay.addWidget(_section_header('Grade Distribution'))
        lay.addSpacing(20)
        self._sum_histogram = _SummaryHistogram()
        self._sum_histogram.setFixedHeight(180)
        lay.addWidget(self._sum_histogram)

        # ── Grade Breakdown (rows) ────────────────────────────────────────────
        lay.addSpacing(28)
        lay.addWidget(_section_header('Grade Breakdown'))
        lay.addSpacing(16)

        self._sum_grades_container = QWidget()
        self._sum_grades_container.setStyleSheet("background:transparent;")
        self._sum_grades_lay = QVBoxLayout(self._sum_grades_container)
        self._sum_grades_lay.setContentsMargins(0, 0, 0, 0)
        self._sum_grades_lay.setSpacing(0)
        lay.addWidget(self._sum_grades_container)

        # ── Measurements ──────────────────────────────────────────────────────
        lay.addSpacing(32)
        lay.addWidget(_sep())
        lay.addSpacing(24)
        lay.addWidget(_section_header('Measurements'))
        lay.addSpacing(14)

        badges_row = QHBoxLayout()
        badges_row.setSpacing(12)
        badges_row.setContentsMargins(0, 0, 0, 0)

        self._sum_er_badge, self._sum_er_val_lbl = self._make_measurement_badge(
            'ER Measurements', '0', OutlineIcon.RULER_MEASURE)
        self._sum_ctr_badge, self._sum_ctr_val_lbl = self._make_measurement_badge(
            'Center Marks', '0', OutlineIcon.CROSSHAIR)

        badges_row.addWidget(self._sum_er_badge)
        badges_row.addWidget(self._sum_ctr_badge)
        badges_row.addStretch()
        lay.addLayout(badges_row)

        # ── Review ────────────────────────────────────────────────────────────
        lay.addSpacing(32)
        lay.addWidget(_sep())
        lay.addSpacing(24)
        lay.addWidget(_section_header('Review'))
        lay.addSpacing(14)

        # Grade chips
        self._review_chips_row = QHBoxLayout()
        self._review_chips_row.setSpacing(8)
        self._review_chips_row.setContentsMargins(0, 0, 0, 0)
        _chips_container = QWidget()
        _chips_container.setStyleSheet("background:transparent;")
        _chips_container.setLayout(self._review_chips_row)
        lay.addWidget(_chips_container)

        lay.addSpacing(10)

        self._review_count_lbl = QLabel('')
        self._review_count_lbl.setStyleSheet(
            f"color:{Theme.TXT_MUTE}; font-size:12px; background:transparent;")
        lay.addWidget(self._review_count_lbl)

        lay.addSpacing(16)

        self._review_grid_widget = QWidget()
        self._review_grid_widget.setStyleSheet("background:transparent;")
        self._review_grid_layout = QGridLayout(self._review_grid_widget)
        self._review_grid_layout.setContentsMargins(0, 0, 0, 0)
        self._review_grid_layout.setSpacing(8)
        lay.addWidget(self._review_grid_widget)

        self._review_empty_lbl = QLabel('Grade some systems to see thumbnails here.')
        self._review_empty_lbl.setStyleSheet(
            f"color:{Theme.TXT_MUTE}; font-size:14px; background:transparent;")
        self._review_empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self._review_empty_lbl)

        lay.addStretch()

        scroll.setWidget(inner)
        outer.addWidget(scroll)

        # Review state
        self._review_selected_grades = set()
        self._review_threads = {}
        self._review_cards = {}
        self._review_queue = []
        self._review_chips = {}
        self._review_chip_grades = []
        self._review_gen = 0

        self._refresh_summary()

    def _make_measurement_badge(self, label, value, icon_type):
        badge = QFrame()
        badge.setObjectName("measureBadge")
        badge.setStyleSheet(f"""
            QFrame#measureBadge {{
                background:{Theme.CARD};
                border:1px solid {Theme.BORDER};
                border-radius:10px;
            }}
        """)
        badge.setFixedHeight(68)
        badge.setMinimumWidth(150)
        lay = QHBoxLayout(badge)
        lay.setContentsMargins(16, 10, 16, 10)
        lay.setSpacing(12)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(tabler_pixmap(icon_type, size=20, color=Theme.ACCENT))
        icon_lbl.setFixedSize(24, 24)
        icon_lbl.setScaledContents(True)
        icon_lbl.setStyleSheet("background:transparent;")

        text_col = QVBoxLayout()
        text_col.setContentsMargins(0, 0, 0, 0)
        text_col.setSpacing(1)

        val_lbl = QLabel(value)
        val_lbl.setStyleSheet(
            f"color:{Theme.TXT}; font-size:22px; font-weight:700; background:transparent;")

        cap_lbl = QLabel(label)
        cap_lbl.setStyleSheet(
            f"color:{Theme.TXT_MUTE}; font-size:11px; background:transparent;")

        text_col.addWidget(val_lbl)
        text_col.addWidget(cap_lbl)

        lay.addWidget(icon_lbl)
        lay.addLayout(text_col)

        return badge, val_lbl

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

        # Measurement badges
        def _count_filled(col):
            if col not in df.columns:
                return 0
            n = 0
            for v in df[col].values:
                try:
                    f = float(v)
                    if f == f:
                        n += 1
                except (ValueError, TypeError):
                    pass
            return n

        er  = _count_filled(f'ER_arcsec_{grader}_VI')
        ctr = _count_filled(f'Center_RA_{grader}_VI')
        self._sum_er_val_lbl.setText(str(er))
        self._sum_ctr_val_lbl.setText(str(ctr))

        # Rebuild review chips if grade distribution changed
        new_grades = sorted(counts.keys())
        if new_grades != self._review_chip_grades:
            self._review_chip_grades = new_grades
            self._rebuild_review_chips(new_grades)

    # ── Review section ────────────────────────────────────────────────────────

    def _rebuild_review_chips(self, grades):
        while self._review_chips_row.count():
            item = self._review_chips_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._review_chips.clear()
        for grade in grades:
            btn = QPushButton(grade)
            btn.setFixedHeight(28)
            btn.clicked.connect(lambda checked, g=grade: self._toggle_review_chip(g))
            self._review_chips[grade] = btn
            self._review_chips_row.addWidget(btn)
        self._review_chips_row.addStretch()
        self._review_selected_grades = set()
        self._update_review_chip_styles()

    def _update_review_chip_styles(self):
        all_selected = len(self._review_selected_grades) == 0
        for grade, btn in self._review_chips.items():
            active = all_selected or grade in self._review_selected_grades
            if active:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background:{Theme.ACCENT}; color:white; border:none;
                        border-radius:12px; font-size:13px; font-weight:700;
                        padding:2px 14px;
                    }}
                    QPushButton:hover {{ background:{Theme.ACCENT_HI}; }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background:transparent; color:{Theme.TXT_MUTE};
                        border:1px solid {Theme.BORDER}; border-radius:12px;
                        font-size:13px; font-weight:600; padding:2px 14px;
                    }}
                    QPushButton:hover {{
                        background:#17273f; color:{Theme.TXT_SOFT};
                        border-color:{Theme.FIELD_BRD};
                    }}
                """)

    def _toggle_review_chip(self, grade):
        if grade in self._review_selected_grades:
            self._review_selected_grades.discard(grade)
        else:
            self._review_selected_grades.add(grade)
        if len(self._review_selected_grades) == len(self._review_chips):
            self._review_selected_grades = set()
        self._update_review_chip_styles()
        self._refresh_review_grid()

    def _refresh_review_grid(self):
        self._review_gen += 1
        for t in list(self._review_threads.values()):
            if t.isRunning():
                t.quit()
        self._review_threads.clear()

        for card in list(self._review_cards.values()):
            card.deleteLater()
        self._review_cards.clear()

        while self._review_grid_layout.count():
            item = self._review_grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        grader = self.current_inspection.inspection_parameters['grader name']
        grades_col = f'{grader}_grades'
        df = self.main_window.df
        matched = []
        if grades_col in df.columns:
            for i in range(len(df)):
                g = str(df.iloc[i][grades_col]).strip()
                if not g or g == 'nan':
                    continue
                if not self._review_selected_grades or g in self._review_selected_grades:
                    matched.append((i, g))

        count = len(matched)
        if count == 0:
            self._review_count_lbl.setText('')
            self._review_empty_lbl.show()
            self._review_grid_widget.hide()
            return

        plural = 'system' if count == 1 else 'systems'
        self._review_count_lbl.setText(f'{count} {plural}')
        self._review_empty_lbl.hide()
        self._review_grid_widget.show()

        COLS = 5
        for grid_i, (idx, grade) in enumerate(matched):
            card = _ReviewCard(idx, grade)
            card.clicked.connect(self._on_review_card_click)
            self._review_cards[idx] = card
            row, col = divmod(grid_i, COLS)
            self._review_grid_layout.addWidget(card, row, col)

        self._review_queue = list(matched)
        self._start_pending_review_fetches()

    def _start_pending_review_fetches(self):
        gen = self._review_gen
        active = sum(1 for t in self._review_threads.values() if t.isRunning())
        while active < 4 and self._review_queue:
            idx, _ = self._review_queue.pop(0)
            if idx in self._review_threads:
                continue
            ip = self.current_inspection.inspection_parameters
            try:
                ra  = float(self.main_window.df.iloc[idx][ip['ra column name']])
                dec = float(self.main_window.df.iloc[idx][ip['dec column name']])
            except (KeyError, ValueError, TypeError):
                continue
            t = ReviewFetchThread(self.current_inspection, idx, ra, dec, cutout_size=80)
            t.thumbnail_ready.connect(self._on_review_thumbnail_ready)
            t.finished.connect(lambda i=idx, g=gen: self._on_review_fetch_done(i, g))
            self._review_threads[idx] = t
            t.start()
            active += 1

    def _on_review_thumbnail_ready(self, idx, arr):
        if idx in self._review_cards:
            self._review_cards[idx].set_image(arr)

    def _on_review_fetch_done(self, idx, gen):
        if gen != self._review_gen:
            return
        self._review_threads.pop(idx, None)
        self._start_pending_review_fetches()

    def _on_review_card_click(self, idx):
        self.screen_switch_tab_bar.set_active_tab('Studio')
        self._switch_screens('inspection')
        QTimer.singleShot(450, lambda: self._jump_to_system(idx, warn_regrading=False))

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
                image: url("{self._arrow_path}");
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

    def _on_prefetch_done(self, rgb, grz, idx, layer):
        if layer != self.current_inspection.layer:
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
        # Sync focus_i with actual keyboard focus before advancing, so that
        # a manual click on a field doesn't leave the counter stale.
        focused = QApplication.focusWidget()
        for i, w in enumerate(self.focus_order):
            # focusProxy() is set on StyledInputBox → resolves to text_edit
            effective = w.focusProxy() if w.focusProxy() else w
            if effective is focused or w is focused:
                self.focus_i = i
                break

        if self.focus_i == len(self.focus_order) - 1:
            if self.next_system_button.isEnabled():
                self.next_system_button.click()
        else:
            self.focus_i += 1
            self.focus_order[self.focus_i].setFocus()

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