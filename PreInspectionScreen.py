from PyQt6.QtWidgets import (QFileDialog, QPushButton, QListWidget, QListWidgetItem,
                             QCheckBox, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QTableWidget, QTableWidgetItem, QAbstractItemView, QComboBox,
                             QLineEdit, QScrollArea, QFrame, QStackedWidget, QHeaderView,
                             QStyledItemDelegate)
from PyQt6.QtCore import Qt, QSize
import numpy as np
import re
from pathlib import Path
from Assets import SvgWidget, show_popup_window
from Icons import tabler_icon, badge_pixmap, OutlineIcon, ICON_WHITE

# ---------------------------------------------------------------------------
# Design system
# ---------------------------------------------------------------------------
BG        = "#0a1628"   # page canvas (deep dark)
SURFACE   = "#0d1a2e"   # header / action bar
CARD      = "#152238"   # card background
FIELD     = "#2e466c"   # input background (intentionally lighter than CARD so fields stand out)
BORDER    = "#27364d"   # card / divider border
FIELD_BRD = "#4a6188"   # input border (brighter than card border so fields are clearly outlined)
ACCENT    = "#4A9EFF"   # primary / focus
WARN      = "#ffb454"   # overwrite warning
TXT       = "#e8edf5"   # primary text
TXT_SOFT  = "#c3cde0"   # labels
TXT_MUTE  = "#8a99b3"   # captions

QSS = f"""
QWidget#preInspectionPage {{ background-color: {BG}; }}

QFrame#header, QFrame#actionBar {{ background-color: {SURFACE}; }}
QFrame#header     {{ border-bottom: 1px solid #1e2c44; }}
QFrame#actionBar  {{ border-top: 1px solid #1e2c44; }}

QLabel {{ color: {TXT}; background: transparent; }}
QLabel#pageTitle    {{ font-size: 21px; font-weight: 700; color: #ffffff; }}
QLabel#pageSubtitle {{ font-size: 12px; color: {TXT_MUTE}; }}
QLabel#cardTitle    {{ font-size: 15px; font-weight: 600; color: #ffffff; }}
QLabel#caption      {{ font-size: 12px; color: {TXT_MUTE}; }}
QLabel#fieldLabel   {{ font-size: 12px; font-weight: 600; color: {TXT_SOFT}; }}
QLabel#warning      {{ font-size: 12px; color: {WARN}; }}

QFrame#card {{ background-color: {CARD}; border: 1px solid {BORDER}; border-radius: 12px; }}

QScrollArea#configScroll {{ background: transparent; border: none; }}
QWidget#scrollBody {{ background: transparent; }}

QComboBox, QLineEdit {{
    background-color: {FIELD}; color: {TXT};
    border: 1px solid {FIELD_BRD}; border-radius: 8px; padding: 7px 10px;
    selection-background-color: {ACCENT}; selection-color: white;
}}
QComboBox:hover {{ border-color: #3d5278; }}
QComboBox:focus, QLineEdit:focus {{ border-color: {ACCENT}; }}
QLineEdit:disabled {{ color: #5c6b85; background-color: #111c2e; border-color: #223049; }}
QComboBox::drop-down {{ border: none; width: 22px; }}
QComboBox QAbstractItemView {{
    background-color: {FIELD}; color: {TXT};
    border: 1px solid {FIELD_BRD}; border-radius: 8px; outline: none;
    selection-background-color: {ACCENT}; selection-color: white;
}}
QComboBox QAbstractItemView::item {{ color: {TXT}; background-color: {FIELD}; padding: 5px 8px; }}
QComboBox QAbstractItemView::item:hover {{ color: {TXT}; background-color: #3a5480; }}
QComboBox QAbstractItemView::item:selected {{ color: white; background-color: {ACCENT}; }}

QPushButton#seg {{ border: 1px solid {FIELD_BRD}; background: {FIELD};
                   color: {TXT_MUTE}; padding: 7px 18px; font-weight: 600; }}
QPushButton#seg:hover[active="false"] {{ background: #17273f; color: {TXT_SOFT}; }}
QPushButton#seg[active="true"] {{ background: {ACCENT}; color: white; border-color: {ACCENT}; }}
QPushButton#segLeft  {{ border-top-left-radius: 8px; border-bottom-left-radius: 8px; }}
QPushButton#segRight {{ border-top-right-radius: 8px; border-bottom-right-radius: 8px; border-left: none; }}

QPushButton#primary {{ background: {ACCENT}; color: white; border: none; border-radius: 10px;
                       padding: 9px 26px; font-size: 14px; font-weight: 700; }}
QPushButton#primary:hover  {{ background: #5fb0ff; }}
QPushButton#primary:pressed {{ background: #3d8de0; }}
QPushButton#ghost {{ background: transparent; color: {TXT_SOFT}; border: 1px solid #33425c;
                     border-radius: 10px; padding: 9px 22px; font-size: 14px; font-weight: 600; }}
QPushButton#ghost:hover {{ background: #17273f; color: white; }}
QPushButton#browse {{ background: #1c2a42; color: {TXT}; border: 1px solid #33425c;
                      border-radius: 8px; padding: 7px 16px; font-weight: 600; }}
QPushButton#browse:hover {{ background: #243a5a; }}
QPushButton#linkBtn {{ background: transparent; color: {ACCENT}; border: none; font-weight: 600; }}
QPushButton#linkBtn:hover {{ color: #7dbaff; }}

QListWidget#cols {{ background-color: {FIELD}; border: 1px solid {FIELD_BRD}; border-radius: 8px;
                    color: {TXT}; padding: 4px; outline: none; }}
QListWidget#cols::item {{ padding: 5px 6px; border-radius: 6px; }}
QListWidget#cols::item:hover {{ background-color: #3a5480; }}
QListWidget#cols::indicator, QCheckBox::indicator {{ width: 16px; height: 16px;
                    border: 1px solid #3d5278; border-radius: 4px; background: {FIELD}; }}
QListWidget#cols::indicator:checked {{ background: {ACCENT}; border-color: {ACCENT}; }}

QCheckBox {{ color: {TXT_SOFT}; spacing: 8px; background: transparent; }}
QCheckBox::indicator:checked {{ background: {ACCENT}; border-color: {ACCENT}; }}
QCheckBox#warnCheck::indicator:checked {{ background: {WARN}; border-color: {WARN}; }}

QTableWidget#preview {{ background-color: {FIELD}; alternate-background-color: #132138;
                        color: #dce3f0; gridline-color: #223049; border: 1px solid {FIELD_BRD};
                        border-radius: 8px; }}
QTableWidget#preview QHeaderView::section {{ background-color: #1c2a42; color: #aeb9cf;
                        border: none; border-right: 1px solid #223049; padding: 7px 9px;
                        font-weight: 600; }}
QTableWidget#preview QTableCornerButton::section {{ background: #1c2a42; border: none; }}

QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: #3a4a62; min-height: 24px; border-radius: 5px; }}
QScrollBar::handle:vertical:hover {{ background: #4a5c78; }}
QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 2px; }}
QScrollBar::handle:horizontal {{ background: #3a4a62; min-width: 24px; border-radius: 5px; }}
QScrollBar::handle:horizontal:hover {{ background: #4a5c78; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: none; }}
"""

PREVIEW_ROW_CAP = 200


class PreInspectionWidget(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.df_existing_columns = self.main_window.df_existing_columns
        self.inspection_parameters = {}
        self.grader_mode = 'existing'
        self.save_directory = str(Path(self.main_window.csv_path).parent)

        self.setObjectName("preInspectionPage")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(QSS)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_header())

        body = QHBoxLayout()
        body.setContentsMargins(28, 12, 28, 16)
        body.setSpacing(20)
        body.addWidget(self._build_config_panel(), 6)
        body.addWidget(self._build_preview_panel(), 5)
        root.addLayout(body, 1)

    # ------------------------------------------------------------------ UI build
    def _build_header(self):
        bar = QFrame()
        bar.setObjectName("header")
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(28, 9, 28, 9)
        lay.setSpacing(14)
        logo = SvgWidget(self.main_window.GRAPHICS_ADDRESSES['large app icon'])
        logo.setFixedSize(32, 32)
        lay.addWidget(logo)
        titles = QVBoxLayout()
        titles.setSpacing(1)
        title = QLabel("Set up inspection")
        title.setObjectName("pageTitle")
        subtitle = QLabel("Configure how this catalog will be reviewed")
        subtitle.setObjectName("pageSubtitle")
        titles.addWidget(title)
        titles.addWidget(subtitle)
        lay.addLayout(titles)
        lay.addStretch()

        back = QPushButton("  Back")
        back.setObjectName("ghost")
        back.setIcon(tabler_icon(OutlineIcon.ARROW_LEFT, size=16, color=TXT_SOFT))
        back.setIconSize(QSize(16, 16))
        back.setCursor(Qt.CursorShape.PointingHandCursor)
        back.clicked.connect(lambda: self.main_window.switch_screens(0))
        self.return_home_button = back
        start = QPushButton("  Start inspection")
        start.setObjectName("primary")
        start.setIcon(tabler_icon(OutlineIcon.TELESCOPE, size=16, color=ICON_WHITE))
        start.setIconSize(QSize(16, 16))
        start.setCursor(Qt.CursorShape.PointingHandCursor)
        start.clicked.connect(self.validate_entries)
        self.start_inspection_button = start
        lay.addWidget(back)
        lay.addSpacing(4)
        lay.addWidget(start)
        return bar

    def _build_config_panel(self):
        scroll = QScrollArea()
        scroll.setObjectName("configScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.viewport().setStyleSheet("background: transparent;")

        container = QWidget()
        container.setObjectName("scrollBody")
        col = QVBoxLayout(container)
        col.setContentsMargins(2, 2, 12, 2)
        col.setSpacing(16)
        col.addWidget(self._card_inspector())
        col.addWidget(self._card_coordinates())
        col.addWidget(self._card_columns())
        col.addWidget(self._card_output())
        col.addStretch()
        scroll.setWidget(container)
        return scroll

    def _card(self, icon, title, subtitle=None):
        """Return (card_frame, content_layout) with an icon header already added."""
        card = QFrame()
        card.setObjectName("card")
        outer = QVBoxLayout(card)
        outer.setContentsMargins(18, 16, 18, 18)
        outer.setSpacing(12)

        head = QHBoxLayout()
        head.setSpacing(11)
        badge = QLabel()
        badge.setFixedSize(26, 26)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setPixmap(badge_pixmap(icon, diameter=26, icon_size=14))
        head.addWidget(badge, alignment=Qt.AlignmentFlag.AlignTop)

        tbox = QVBoxLayout()
        tbox.setSpacing(2)
        tl = QLabel(title)
        tl.setObjectName("cardTitle")
        tbox.addWidget(tl)
        if subtitle:
            sl = QLabel(subtitle)
            sl.setObjectName("caption")
            sl.setWordWrap(True)
            tbox.addWidget(sl)
        head.addLayout(tbox)
        head.addStretch()
        outer.addLayout(head)
        return card, outer

    def _make_combo(self, items, preset_idx=0):
        combo = QComboBox()
        combo.addItems(items)
        combo.setCurrentIndex(preset_idx)
        # Force a stylesheet-aware delegate so popup item text colours apply
        # (native macOS popups otherwise ignore the ::item colour rules).
        combo.setItemDelegate(QStyledItemDelegate(combo))
        return combo

    def _labeled(self, text, widget):
        """A field label stacked above a widget, returned as a layout."""
        box = QVBoxLayout()
        box.setSpacing(5)
        lbl = QLabel(text)
        lbl.setObjectName("fieldLabel")
        box.addWidget(lbl)
        box.addWidget(widget)
        return box

    def _labeled_layout(self, text, inner_layout):
        box = QVBoxLayout()
        box.setSpacing(5)
        lbl = QLabel(text)
        lbl.setObjectName("fieldLabel")
        box.addWidget(lbl)
        box.addLayout(inner_layout)
        return box

    # -- Card 1: Inspector --------------------------------------------------
    def _card_inspector(self):
        card, lay = self._card(OutlineIcon.USER, "Inspector", "Who is reviewing this catalog?")
        self.existing_graders_found = self.check_for_existing_grader()

        self.new_name_edit = QLineEdit()
        self.new_name_edit.setPlaceholderText("Enter a new inspector name")

        if self.existing_graders_found:
            self.existing_combo = self._make_combo(sorted(self.existing_graders))

            seg = QHBoxLayout()
            seg.setSpacing(0)
            self.seg_existing = QPushButton("Existing inspector")
            self.seg_new = QPushButton("New inspector")
            for btn in (self.seg_existing, self.seg_new):
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.seg_existing.clicked.connect(lambda: self._set_grader_mode('existing'))
            self.seg_new.clicked.connect(lambda: self._set_grader_mode('new'))
            seg.addWidget(self.seg_existing)
            seg.addWidget(self.seg_new)
            seg.addStretch()
            lay.addLayout(seg)

            self.grader_stack = QStackedWidget()
            self.grader_stack.setStyleSheet("background: transparent;")
            page_existing = QWidget()
            page_existing.setStyleSheet("background: transparent;")
            pe = QVBoxLayout(page_existing)
            pe.setContentsMargins(0, 0, 0, 0)
            pe.addLayout(self._labeled("Select inspector", self.existing_combo))
            page_new = QWidget()
            page_new.setStyleSheet("background: transparent;")
            pn = QVBoxLayout(page_new)
            pn.setContentsMargins(0, 0, 0, 0)
            pn.addLayout(self._labeled("Inspector name", self.new_name_edit))
            self.grader_stack.addWidget(page_existing)
            self.grader_stack.addWidget(page_new)
            lay.addWidget(self.grader_stack)
            self._set_grader_mode('existing')
        else:
            self.grader_mode = 'new'
            note = QLabel("No existing inspectors were found in this catalog — enter a new name below.")
            note.setObjectName("caption")
            note.setWordWrap(True)
            lay.addWidget(note)
            lay.addLayout(self._labeled("Inspector name", self.new_name_edit))
        return card

    def _set_grader_mode(self, mode):
        self.grader_mode = mode
        for btn, btn_mode, side in ((self.seg_existing, 'existing', 'left'),
                                    (self.seg_new, 'new', 'right')):
            is_active = (mode == btn_mode)
            radius = ("border-top-left-radius:8px;border-bottom-left-radius:8px;"
                      if side == 'left' else
                      "border-top-right-radius:8px;border-bottom-right-radius:8px;border-left:none;")
            if is_active:
                btn.setStyleSheet(
                    "QPushButton{{background:{a};color:white;border:1px solid {a};"
                    "padding:7px 18px;font-weight:600;{r}}}".format(a=ACCENT, r=radius))
            else:
                btn.setStyleSheet(
                    "QPushButton{{border:1px solid {b};background:{f};color:{m};"
                    "padding:7px 18px;font-weight:600;{r}}}"
                    "QPushButton:hover{{background:#17273f;color:{s};}}".format(
                        b=FIELD_BRD, f=FIELD, m=TXT_MUTE, s=TXT_SOFT, r=radius))
        self.grader_stack.setCurrentIndex(0 if mode == 'existing' else 1)

    # -- Card 2: Coordinates ------------------------------------------------
    def _card_coordinates(self):
        card, lay = self._card(OutlineIcon.MAP_PIN, "Coordinates",
                               "Which columns hold the sky position (R.A. / Dec.)?")
        ra_idx, dec_idx = self.check_for_ra_dec_columns()
        self.ra_combo = self._make_combo(self.df_existing_columns, ra_idx)
        self.dec_combo = self._make_combo(self.df_existing_columns, dec_idx)
        row = QHBoxLayout()
        row.setSpacing(16)
        row.addLayout(self._labeled("R.A. column", self.ra_combo), 1)
        row.addLayout(self._labeled("Dec. column", self.dec_combo), 1)
        lay.addLayout(row)
        return card

    # -- Card 3: Columns to display ----------------------------------------
    def _card_columns(self):
        card, lay = self._card(OutlineIcon.COLUMNS, "Columns to display",
                               "Optional — extra catalog fields to show while inspecting.")
        self.col_search = QLineEdit()
        self.col_search.setPlaceholderText("Search columns…")
        self.col_search.addAction(tabler_icon(OutlineIcon.SEARCH, size=15, color=TXT_MUTE),
                                  QLineEdit.ActionPosition.LeadingPosition)
        self.col_search.textChanged.connect(self._filter_columns)
        lay.addWidget(self.col_search)

        self.columns_list = QListWidget()
        self.columns_list.setObjectName("cols")
        self.columns_list.setMinimumHeight(170)
        for name in self.df_existing_columns:
            item = QListWidgetItem(name)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            self.columns_list.addItem(item)
        self.columns_list.itemChanged.connect(self._update_col_count)
        lay.addWidget(self.columns_list)

        foot = QHBoxLayout()
        self.col_count_label = QLabel("0 selected")
        self.col_count_label.setObjectName("caption")
        foot.addWidget(self.col_count_label)
        foot.addStretch()
        clear = QPushButton("Clear all")
        clear.setObjectName("linkBtn")
        clear.setCursor(Qt.CursorShape.PointingHandCursor)
        clear.clicked.connect(self._clear_columns)
        foot.addWidget(clear)
        lay.addLayout(foot)
        return card

    def _filter_columns(self, text):
        text = text.lower().strip()
        for i in range(self.columns_list.count()):
            item = self.columns_list.item(i)
            item.setHidden(text not in item.text().lower())

    def _update_col_count(self):
        n = sum(1 for i in range(self.columns_list.count())
                if self.columns_list.item(i).checkState() == Qt.CheckState.Checked)
        self.col_count_label.setText(f"{n} selected")

    def _clear_columns(self):
        for i in range(self.columns_list.count()):
            self.columns_list.item(i).setCheckState(Qt.CheckState.Unchecked)

    # -- Card 4: Output -----------------------------------------------------
    def _card_output(self):
        card, lay = self._card(OutlineIcon.DEVICE_FLOPPY, "Output",
                               "Where your grades and comments will be saved.")
        self.inspection_name_edit = QLineEdit()
        self.inspection_name_edit.setText(self.determine_default_name())
        lay.addLayout(self._labeled("Inspection file name", self.inspection_name_edit))

        self.folder_display = QLineEdit(self.save_directory)
        self.folder_display.setReadOnly(True)
        browse = QPushButton("  Browse…")
        browse.setObjectName("browse")
        browse.setIcon(tabler_icon(OutlineIcon.FOLDER, size=15, color=TXT))
        browse.setIconSize(QSize(15, 15))
        browse.setCursor(Qt.CursorShape.PointingHandCursor)
        browse.clicked.connect(self.open_file_browser)
        self.directory_browse_button = browse
        folder_row = QHBoxLayout()
        folder_row.setSpacing(10)
        folder_row.addWidget(self.folder_display, 1)
        folder_row.addWidget(browse)
        lay.addLayout(self._labeled_layout("Save folder", folder_row))

        self.overwrite_checkbox = QCheckBox("Edit the original CSV directly (overwrites existing data)")
        self.overwrite_checkbox.setObjectName("warnCheck")
        self.overwrite_checkbox.stateChanged.connect(self._toggle_overwrite)
        lay.addWidget(self.overwrite_checkbox)
        self.overwrite_warning = QLabel(
            "⚠  The original file will be modified — existing grades and comments may be overwritten.")
        self.overwrite_warning.setObjectName("warning")
        self.overwrite_warning.setWordWrap(True)
        self.overwrite_warning.setVisible(False)
        lay.addWidget(self.overwrite_warning)
        return card

    def _toggle_overwrite(self, state):
        checked = state == Qt.CheckState.Checked.value
        self.inspection_name_edit.setDisabled(checked)
        self.overwrite_warning.setVisible(checked)

    # -- Preview panel ------------------------------------------------------
    def _build_preview_panel(self):
        card = QFrame()
        card.setObjectName("card")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(16, 14, 16, 16)
        lay.setSpacing(10)

        header = QHBoxLayout()
        title = QLabel("Data preview")
        title.setObjectName("cardTitle")
        header.addWidget(title)
        header.addStretch()
        fname = Path(self.main_window.csv_path).name
        nrows, ncols = self.main_window.df.shape
        meta = QLabel(f"{fname}   ·   {nrows:,} rows × {ncols} cols")
        meta.setObjectName("caption")
        header.addWidget(meta)
        lay.addLayout(header)

        self._build_table()
        lay.addWidget(self.table_widget, 1)

        if nrows > PREVIEW_ROW_CAP:
            hint = QLabel(f"Showing first {PREVIEW_ROW_CAP} rows")
            hint.setObjectName("caption")
            lay.addWidget(hint)
        return card

    def _build_table(self):
        df = self.main_window.df
        n_rows = min(len(df), PREVIEW_ROW_CAP)
        self.table_widget = QTableWidget(n_rows, len(df.columns))
        self.table_widget.setObjectName("preview")
        self.table_widget.setHorizontalHeaderLabels([str(c) for c in df.columns])
        self.table_widget.verticalHeader().setVisible(False)
        self.table_widget.setAlternatingRowColors(True)
        self.table_widget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_widget.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.table_widget.setShowGrid(True)
        self.table_widget.horizontalHeader().setDefaultSectionSize(110)
        self.table_widget.horizontalHeader().setStretchLastSection(False)
        for r in range(n_rows):
            for c in range(len(df.columns)):
                self.table_widget.setItem(r, c, QTableWidgetItem(str(df.iat[r, c])))

    # ------------------------------------------------------------- behaviour
    def open_file_browser(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select a folder", self.save_directory or "")
        if folder_path:
            self.save_directory = folder_path
            self.folder_display.setText(folder_path)

    def validate_entries(self):
        self.compile_all_entries()
        errors = []
        # Confirm inspector information:
        unique_characters_in_name = list(set(self.inspection_parameters['grader name']))
        if len(self.inspection_parameters['grader name']) == 0:
            errors.append('New inspector field cannot be empty.')
        elif len(unique_characters_in_name) == 1 and unique_characters_in_name[0] == ' ':
            errors.append('New inspector name cannot contain spaces only.')
        # Confirm ra dec:
        try:
            ra_temp = self.main_window.df[self.inspection_parameters['ra column name']].values.astype(np.float64)
            del ra_temp
        except Exception:
            errors.append('R.A. column values could not be converted to decimals.')
        try:
            dec_temp = self.main_window.df[self.inspection_parameters['dec column name']].values.astype(np.float64)
            del dec_temp
        except Exception:
            errors.append('Dec. column values could not be converted to decimals.')
        # Confirm inspection name:
        unique_characters_in_name = list(set(self.inspection_parameters['new df name']))
        if len(self.inspection_parameters['new df name']) == 0:
            errors.append('New inspection name cannot be empty.')
        if len(unique_characters_in_name) == 1 and unique_characters_in_name[0] == ' ':
            errors.append('New inspection name cannot contain spaces only.')
        for forbiden_char in ['\\', '/', ':', '*', '?', '"', '<', '>', '|']:
            if forbiden_char in self.inspection_parameters['new df name']:
                errors.append('New inspection name cannot contain " {} ".'.format(forbiden_char))

        if len(errors) == 0:
            self.main_window.inspection_parameters = self.inspection_parameters
            self.prepare_df_columns()
            self.main_window.switch_screens(2)
        elif len(errors) == 1:
            show_popup_window(title="An input field contains an error:", text="\n{}".format(errors[0]), header_icon_path=None)
        elif len(errors) > 1:
            error_message = errors[0]
            for error in errors[1:]:
                error_message += '\n' + error
            show_popup_window(title="An input field contains an error:", text=error_message, header_icon_path=None)

    def prepare_df_columns(self):
        if self.inspection_parameters['grader name'] + "_grades" not in self.df_existing_columns:
            self.main_window.df[self.inspection_parameters['grader name'] + "_grades"] = ""
        if self.inspection_parameters['grader name'] + "_comments" not in self.df_existing_columns:
            self.main_window.df[self.inspection_parameters['grader name'] + "_comments"] = ""

    def compile_all_entries(self):
        # Inspector information
        if self.existing_graders_found and self.grader_mode == 'existing':
            self.inspection_parameters['grader name'] = self.existing_combo.currentText()
        else:
            self.inspection_parameters['grader name'] = self.new_name_edit.text()

        # Select columns
        self.inspection_parameters['ra column name'] = self.ra_combo.currentText()
        self.inspection_parameters['dec column name'] = self.dec_combo.currentText()
        selected_columns = [self.columns_list.item(i).text()
                            for i in range(self.columns_list.count())
                            if self.columns_list.item(i).checkState() == Qt.CheckState.Checked]
        self.inspection_parameters['additional columns'] = selected_columns if selected_columns else None

        # Saving settings
        if self.overwrite_checkbox.isChecked():
            self.inspection_parameters['new df name'] = self.main_window.csv_path.split('/')[-1].split('.')[0]
        else:
            self.inspection_parameters['new df name'] = self.inspection_name_edit.text()
        self.inspection_parameters['save directory'] = self.save_directory

    def determine_default_name(self):
        csv_name = self.main_window.csv_path.split('/')[-1].split('.')[0]
        pattern = r"_v\d+$"
        match = re.search(pattern, csv_name)
        has_version_number = bool(match)
        try:
            if has_version_number:
                previous_version_number = int(csv_name.split('_v')[-1])
                new_version_number = previous_version_number + 1
                new_csv_name = csv_name[:-len(str(previous_version_number))]
                return new_csv_name + '{}'.format(new_version_number)
            else:
                new_version_number = 1
                return csv_name + '_v{}'.format(new_version_number)
        except Exception:
            return csv_name + '_v1'

    def check_for_existing_grader(self):
        existing_graders = []
        for column_name in self.df_existing_columns:
            if "_grades" in column_name:
                existing_graders.append(column_name.split("_grades")[0])
            if "_comments" in column_name:
                existing_graders.append(column_name.split("_comments")[0])
        self.existing_graders = set(existing_graders)
        return len(existing_graders) > 0

    def check_for_ra_dec_columns(self):
        df_existing_columns_lowercase = [column_name.lower() for column_name in self.df_existing_columns]
        try:
            ra_idx = df_existing_columns_lowercase.index('ra')
        except ValueError:
            ra_idx = 0
        try:
            dec_idx = df_existing_columns_lowercase.index('dec')
        except ValueError:
            dec_idx = 1
        return (ra_idx, dec_idx)
