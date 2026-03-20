from PyQt6.QtWidgets import QFileDialog,QPushButton,QListWidgetItem,QListWidget,QCheckBox, QWidget,QVBoxLayout,QHBoxLayout,QLabel,QTableWidget,QTableWidgetItem,QAbstractItemView, QGroupBox, QSpacerItem
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtCore import Qt
import numpy as np
import csv
import re
from Assets import InputField, DropdownMenu, ScrollableList, ClickEffectButton, CheckBox, SvgWidget, show_popup_window
from pathlib import Path

class PreInspectionWidget(QWidget):
    def __init__(self,main_window):
        super().__init__()
        self.main_window=main_window
        self.df_existing_columns=self.main_window.df_existing_columns
        self.inspection_parameters={}

        self.window_layout = QVBoxLayout()
        self.page_layout = QHBoxLayout()
        self.setting_outline = QVBoxLayout()
        self.preview_outline = QVBoxLayout()
        self.window_layout.addLayout(self.page_layout)
        self.page_layout.addLayout(self.preview_outline, 1)
        self.page_layout.addLayout(self.setting_outline, 1)

        # Build settings column:

        # Grader name
        self.add_text('Set up inspection settings', size=20,host_layout=self.setting_outline,bold=True)
        self.grader_info_layout = QVBoxLayout()
        #Existing graders
        self.existing_graders_found = self.check_for_existing_grader()
        if self.existing_graders_found:
            self.dropdown_existing_graders=DropdownMenu(label_text="Choose from existing inspector:",drop_down_items=self.existing_graders,main_window=self.main_window)
            self.dropdown_checkbox = self.create_checkbox(True)
            self.dropdown_existing_graders.insertWidget(0,self.dropdown_checkbox)
            self.grader_info_layout.addLayout(self.dropdown_existing_graders)
            grader_name_input_box_label = "Type new inspector name:"
            add_checkmark=True
        else:
            self.add_text("No existing graders were found in this CSV. Enter an new inspector name below.",size=int(0.9*self.main_window.FONT_SIZES["input box labels"]),host_layout=self.grader_info_layout,bold=False)
            grader_name_input_box_label = "New inspector name:"
            add_checkmark=False
        # self.grader_info_layout.addSpacerItem(QSpacerItem(0, 10))
        #Grader name
        self.grader_name_layout = InputField(label_text=grader_name_input_box_label,main_window=self.main_window)
        if add_checkmark:
            self.input_new_grader_checkbox = self.create_checkbox(False)
            self.input_new_grader_checkbox.stateChanged.connect(lambda state: self.define_grader_name(state, self.dropdown_checkbox))
            self.dropdown_checkbox.stateChanged.connect(lambda state: self.define_grader_name(state, self.input_new_grader_checkbox))
            self.grader_name_layout.insertWidget(0,self.input_new_grader_checkbox)
        self.grader_info_layout.addLayout(self.grader_name_layout)

        #Column selection

        #RA and Dec:
        self.column_info_layout = QVBoxLayout()
        self.ra_dec_layout = QHBoxLayout()
        ra_dec_idxs = self.check_for_ra_dec_columns()
        self.ra_dropdown, self.dec_dropdown = DropdownMenu(label_text='R.A. column:',drop_down_items=self.df_existing_columns,main_window=self.main_window,preset_idx=ra_dec_idxs[0]), DropdownMenu(label_text='Dec. column:',drop_down_items=self.df_existing_columns,main_window=self.main_window,preset_idx=ra_dec_idxs[1])
        self.ra_dec_layout.addLayout(self.ra_dropdown), self.ra_dec_layout.addLayout(self.dec_dropdown)
        self.column_info_layout.addLayout(self.ra_dec_layout)
        #Custom column selection:
        self.all_columns_list = ScrollableList(items=self.df_existing_columns,connected_function=self.update_selected_columns_checkbox_list)
        self.selected_columns_checkbox_list = QListWidget()
        self.selected_columns_checkbox_list.setStyleSheet(self.all_columns_list.style)
        self.two_lists_titles = QHBoxLayout()
        self.add_text('All available columns', size=self.main_window.FONT_SIZES["input box labels"],host_layout=self.two_lists_titles,bold=False)
        self.add_text('Selected columns', size=self.main_window.FONT_SIZES["input box labels"],host_layout=self.two_lists_titles,bold=False)
        self.two_lists_layout = QHBoxLayout()
        self.two_lists_layout.addWidget(self.all_columns_list), self.two_lists_layout.addWidget(self.selected_columns_checkbox_list)
        self.add_text('Select additional columns to display during inspection:', size=self.main_window.FONT_SIZES["input box labels"],host_layout=self.column_info_layout,bold=False)
        self.column_info_layout.addLayout(self.two_lists_titles)
        self.column_info_layout.addLayout(self.two_lists_layout)

        #Saving settings
        # New directory:
        self.saving_settings_layout = QVBoxLayout()
        self.inspection_name_layout = InputField(label_text="Inspection name:",main_window=self.main_window)
        self.inspection_name_layout.input_field.setText(self.determine_default_name())
        self.new_inspection_file_checkbox = self.create_checkbox(True)
        self.new_inspection_file_checkbox.stateChanged.connect(self.turn_off_overwritte)
        self.inspection_name_layout.insertWidget(0,self.new_inspection_file_checkbox)
        self.add_text('Select directory:', size=self.main_window.FONT_SIZES["input box labels"],host_layout=self.inspection_name_layout,bold=False)
        self.directory_browse_button = self.create_directory_browse_button()
        self.inspection_name_layout.addWidget(self.directory_browse_button)
        self.saving_settings_layout.addLayout(self.inspection_name_layout)
        # Overwrite:
        self.overwritte_checkbox = CheckBox('Edit selected CSV directly',main_window=self.main_window).checkbox
        self.overwritte_checkbox.stateChanged.connect(self.display_overwritte_warning)
        self.saving_settings_layout.addWidget(self.overwritte_checkbox)
        self.overwritte_warning_label = self.add_text("WARNING: Original CSV content may be overwritten.",size=self.main_window.FONT_SIZES["input box labels"],host_layout=None,bold=True,warning=True)
        self.overwritte_warning_label.setVisible(False)
        self.saving_settings_layout.addWidget(self.overwritte_warning_label)

        self.grader_info_box = self.create_group_box(box_title="Inspector Information",box_content_layout=self.grader_info_layout)
        self.setting_outline.addWidget(self.grader_info_box)

        self.column_selection_box = self.create_group_box(box_title="Select Columns",box_content_layout=self.column_info_layout)
        self.setting_outline.addWidget(self.column_selection_box)

        self.saving_settings_box = self.create_group_box(box_title="Saving Settings",box_content_layout=self.saving_settings_layout)
        self.setting_outline.addWidget(self.saving_settings_box)

        self.setting_outline.addStretch()

        # Build CSV preview column
        self.add_text('CSV preview', size=20,host_layout=self.preview_outline,bold=True)
        self.display_table(host_layout=self.preview_outline)

        #Bottom buttons
        self.bottom_buttons_layout=QHBoxLayout()
        self.bottom_buttons_layout.setContentsMargins(0, 0, 0, 0)
        self.return_home_button = ClickEffectButton(self.main_window.GRAPHICS_ADDRESSES['return home unclicked'],self.main_window.GRAPHICS_ADDRESSES['return home clicked'],size1=200, size2=200)
        self.return_home_button.clicked.connect(lambda: self.main_window.switch_screens(0))       
        self.start_inspection_button = ClickEffectButton(self.main_window.GRAPHICS_ADDRESSES['start inspection unclicked'],self.main_window.GRAPHICS_ADDRESSES['start inspection clicked'],size1=200, size2=200)
        self.start_inspection_button.clicked.connect(self.validate_entries)       
        self.bottom_buttons_layout.addStretch()
        self.bottom_buttons_layout.addWidget(self.return_home_button)
        self.add_logo_to_layout()
        self.bottom_buttons_layout.addWidget(self.start_inspection_button)
        self.bottom_buttons_layout.addStretch()
        self.window_layout.addLayout(self.bottom_buttons_layout)

        self.setLayout(self.window_layout)

    def validate_entries(self):
        self.compile_all_entries()
        errors = []
        #Confirm inspector information:
        unique_characters_in_name = list(set(self.inspection_parameters['grader name']))
        if len(self.inspection_parameters['grader name'])==0:
            errors.append('New inspector field cannot be empty.')
        elif len(unique_characters_in_name)==1 and unique_characters_in_name[0]==' ':
            errors.append('New inspector name cannot contain spaces only.')
        #Confirm ra dec:
        try:
            ra_temp = self.main_window.df[self.inspection_parameters['ra column name']].values.astype(np.float64)
            del ra_temp
        except:
            errors.append('R.A. column values could not be converted to decimals.')
        try:
            dec_temp = self.main_window.df[self.inspection_parameters['dec column name']].values.astype(np.float64)
            del dec_temp
        except:
            errors.append('Dec. column values could not be converted to decimals.')
        #Confirm inspection name:
        unique_characters_in_name = list(set(self.inspection_parameters['new df name']))
        if len(self.inspection_parameters['new df name'])==0:
            errors.append('New inspection name cannot be empty.')
        if len(unique_characters_in_name)==1 and unique_characters_in_name[0]==' ':
            errors.append('New inspection name cannot contain spaces only.')
        for forbiden_char in [ '\\', '/', ':', '*', '?', '"', '<', '>', '|']:
            if forbiden_char in self.inspection_parameters['new df name']:
                errors.append('New inspection name cannot contain " {} ".'.format(forbiden_char))
        
        if len(errors)==0:
            #IF there are no errors:
            self.main_window.inspection_parameters = self.inspection_parameters
            #Add missing grade and comment columns to df
            self.prepare_df_columns()
            self.main_window.switch_screens(2)
            
        elif len(errors)==1:
            show_popup_window(title="An input field contains an error:",text="\n{}".format(errors[0]), header_icon_path=None)
        elif len(errors)>1:
            error_message = errors[0]
            for error in errors[1:]:
                error_message+='\n'+error
            show_popup_window(title="An input field contains an error:",text=error_message, header_icon_path=None)
            
    def prepare_df_columns(self):
        #Add grade col
        if self.inspection_parameters['grader name']+"_grades" not in self.df_existing_columns:
            self.main_window.df[self.inspection_parameters['grader name']+"_grades"]=""
        #Add column col
        if self.inspection_parameters['grader name']+"_comments" not in self.df_existing_columns:
            self.main_window.df[self.inspection_parameters['grader name']+"_comments"]=""

    def compile_all_entries(self):
        # Inspector information
        if self.existing_graders_found:
            if self.dropdown_checkbox.isChecked():
                self.inspection_parameters['grader name'] = self.dropdown_existing_graders.dropdown.currentText() #Update grader name
            elif self.input_new_grader_checkbox.isChecked():
                self.inspection_parameters['grader name'] = self.grader_name_layout.input_field.text() #Update grader name
        else:
            self.inspection_parameters['grader name'] = self.grader_name_layout.input_field.text() #Update grader name

        # Select columns
        self.inspection_parameters['ra column name'] = self.ra_dropdown.dropdown.currentText() #Update RA column name
        self.inspection_parameters['dec column name'] = self.dec_dropdown.dropdown.currentText() #Update RA column name
        selected_columns = [item.text() for item in self.all_columns_list.selectedItems()]
        self.inspection_parameters['additional columns'] = selected_columns if len(selected_columns)>0 else None

        # Saving settings
        if self.overwritte_checkbox.isChecked():
            self.inspection_parameters['new df name'] = self.main_window.csv_path.split('/')[-1].split('.')[0]
        elif self.new_inspection_file_checkbox.isChecked():
            self.inspection_parameters['new df name'] = self.inspection_name_layout.input_field.text()
        self.inspection_parameters['save directory'] = self.save_directory

    def turn_off_overwritte(self,state):
        if state == Qt.CheckState.Checked.value:
            self.overwritte_checkbox.setChecked(False)
        elif state == Qt.CheckState.Unchecked.value:
            self.overwritte_checkbox.setChecked(True)

    def display_overwritte_warning(self,state):
        if state == Qt.CheckState.Checked.value:
            self.overwritte_warning_label.setVisible(True)
            self.new_inspection_file_checkbox.setChecked(False)
        elif state == Qt.CheckState.Unchecked.value:
            self.overwritte_warning_label.setVisible(False)
            self.new_inspection_file_checkbox.setChecked(True)

    def create_directory_browse_button(self):
        self.save_directory = str(Path(self.main_window.csv_path).parent)
        button = QPushButton(Path(self.main_window.csv_path).parent.name)
        button.clicked.connect(lambda:self.open_file_browser(button))
        button.setStyleSheet("""
                                    QPushButton {
                                        border: 2px solid white;
                                        background-color: #2e2e2e; /* dark gray */
                                        color: white;
                                        padding: 5px;
                                        border-radius: 5px;
                                    }
                                    QPushButton:hover {
                                        background-color: #3c3c3c; /* slightly lighter on hover */
                                    }
                                    QPushButton:pressed {
                                        background-color: #1e1e1e; /* darker when pressed */
                                    }
                                """)
        return button

    def open_file_browser(self,button):
        folder_path = QFileDialog.getExistingDirectory(self, "Select a folder", "")
        if folder_path:
            self.save_directory = folder_path
            button.setText(Path(folder_path).name)  # Change button label to file name

    def add_logo_to_layout(self):
        logo = SvgWidget(self.main_window.GRAPHICS_ADDRESSES['large app icon'])
        logo.setFixedSize(50,50)

        layout = QHBoxLayout()
        layout.addStretch(), layout.addWidget(logo), layout.addStretch()
        self.bottom_buttons_layout.addLayout(layout)

    def determine_default_name(self):
        csv_name = self.main_window.csv_path.split('/')[-1].split('.')[0]
        #Try to obtain version number:
        pattern = r"_v\d+$" #v followed by version number
        match = re.search(pattern,csv_name)
        has_version_number = bool(match)
        try:
            if has_version_number:
                previous_version_number = int(csv_name.split('_v')[-1])
                new_version_number = previous_version_number+1
                new_csv_name = csv_name[:-len(str(previous_version_number))]
                return new_csv_name+'{}'.format(new_version_number)
            else:
                new_version_number = 1
                return csv_name+'_v{}'.format(new_version_number)
        except:
            return csv_name+'_v1'

    def update_selected_columns_checkbox_list(self):
        self.selected_columns_checkbox_list.clear()
        for item in self.all_columns_list.selectedItems():
            checkbox_item = QListWidgetItem(self.selected_columns_checkbox_list)
            checkbox = QCheckBox(item.text())
            checkbox.setChecked(True)

            # Remove from left list selection if unchecked
            # checkbox.stateChanged.connect(
            #     lambda state, it=item: self.unselect_item(it) if state == Qt.CheckState.Unchecked else None
            # )

            self.selected_columns_checkbox_list.setItemWidget(checkbox_item, checkbox)

    def define_grader_name(self,state,other_checkbox):
        if state == Qt.CheckState.Checked.value:
            other_checkbox.setChecked(False)
        elif state == Qt.CheckState.Unchecked.value:
            other_checkbox.setChecked(True)

    def add_text(self,text,size,host_layout=None,bold=False,warning=False):
        label = QLabel(text)
        font = QFont()
        if bold:
            font.setWeight(QFont.Weight.Bold)
        else:
            font.setWeight(QFont.Weight.Normal)
        font.setPointSize(size)
        label.setFont(font)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if warning:
            label.setStyleSheet("color: red;")
        else:
            label.setStyleSheet("color: white;")
        if host_layout==None:
            return label
        else:
            host_layout.addWidget(label)

    def create_checkbox(self, checked=False):
        checkbox = QCheckBox()
        checkbox.setChecked(checked)
        return checkbox

    def check_for_existing_grader(self):
        existing_graders = []
        for column_name in self.df_existing_columns:
            if "_grades" in column_name: 
                grader_name = column_name.split("_grades")[0]
                existing_graders.append(grader_name)
            if "_comments" in column_name:
                grader_name = column_name.split("_comments")[0]
                existing_graders.append(grader_name)
        self.existing_graders=set(existing_graders)
        return True if len(existing_graders)>0 else False
    
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
        return (ra_idx,dec_idx)

    def create_group_box(self,box_title,box_content_layout):
        group_box = QGroupBox(box_title)
        group_box.setLayout(box_content_layout)
        group_box.setStyleSheet("""
                                QGroupBox {
                                    border: 1px solid lightgray;
                                    border-radius: 5px;
                                    margin-top: 10px;
                                }

                                QGroupBox::title {
                                subcontrol-origin: margin;
                                subcontrol-position: top center;
                                background-color: black;
                                color: lightgray;
                                padding-left: 5px;
                                padding-right: 5px;
                                top: -1px; /* manually raise the title to overlap */
                                }
                                """)
        return group_box

    def display_table(self,host_layout):
        self.table_widget = QTableWidget()
        self.table_widget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers) 

        with open(self.main_window.csv_path, newline='', encoding='utf-8') as file:
            reader = csv.reader(file)
            data = list(reader)

            self.table_widget.setRowCount(len(data) - 1)
            self.table_widget.setColumnCount(len(data[0]))
            self.table_widget.setHorizontalHeaderLabels(data[0])  # Set headers

            for row_index, row_data in enumerate(data[1:]):  # Skip header
                for col_index, cell in enumerate(row_data):
                    item = QTableWidgetItem(cell)
                    
                    self.table_widget.setItem(row_index, col_index, item)

        self.table_widget.setStyleSheet("""
                                        QTableWidget {
                                            background-color: #2e2e2e;  /* dark gray */
                                            color: white;               /* optional: white text */
                                            gridline-color: #555555;    /* optional: gray gridlines */
                                        }
                                        QHeaderView::section {
                                            background-color: #444444;  /* optional: darker header */
                                            color: white;
                                        }
                                        QScrollBar:vertical {
                                            background: #333;
                                            width: 12px;
                                            margin: 0px 0px 0px 0px;
                                        }

                                        QScrollBar::handle:vertical {
                                            background: #888;
                                            min-height: 20px;
                                            border-radius: 5px;
                                        }
                                        QScrollBar::add-line:vertical,
                                        QScrollBar::sub-line:vertical {
                                            height: 0px;
                                        }
                                        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                                            background: none;
                                        }
                                        QScrollBar:horizontal {
                                            background: #333;
                                            height: 12px;
                                            margin: 0px 0px 0px 0px;
                                        }

                                        QScrollBar::handle:horizontal {
                                            background: #888;
                                            min-width: 20px;
                                            border-radius: 5px;
                                        }

                                        QScrollBar::add-line:horizontal,
                                        QScrollBar::sub-line:horizontal {
                                            width: 0px;
                                        }

                                        QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                                            background: none;
                                        }
                                        """)
        
        host_layout.addWidget(self.table_widget)