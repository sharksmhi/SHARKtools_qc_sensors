# -*- coding: utf-8 -*-
# Copyright (c) 2018 SMHI, Swedish Meteorological and Hydrological Institute
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
import os
import shutil
import tkinter as tk
from tkinter import filedialog
import sharkpylib as spl
import gui as main_gui
import sharkpylib.tklib.tkinter_widgets as tkw
from sharkpylib.gismo.sampling_types import SamplingTypeSettings
from core.exceptions import *
from sharkpylib.gismo.exceptions import *

SETTINGS_FILES_DIRECTORY = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'settings_files')
MAPPING_FILES_DIRECTORY = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'mapping_files')


class PageSamplingTypeSettings(tk.Frame):
    """
    """
    def __init__(self, parent, parent_app, **kwargs):
        tk.Frame.__init__(self, parent, **kwargs)
        # parent is the frame "container" in App. contoller is the App class
        self.parent = parent
        self.parent_app = parent_app
        self.main_app = self.parent_app.main_app
        self.user_manager = parent_app.user_manager
        self.user = self.user_manager.user
        self.session = parent_app.session
        self.settings = parent_app.settings
        self.settings_files = parent_app.settings_files
        self.mapping_files = parent_app.mapping_files

        self.mapping_files.add_directory(MAPPING_FILES_DIRECTORY)

    #===========================================================================
    def startup(self):
        self._add_settings_file_directory()
        self._set_frame()
        self._set_labelframe_files()
        self._set_labelframe_dependent_parameters()
        self._set_labelframe_flags()
        self._set_labelframe_mandatory_columns()
        self._set_labelframe_parameter_mapping()
        self._set_labelframe_station_mapping()
        self._set_labelframe_properties()
        self._on_select_file()
    
    #===========================================================================
    def update_page(self):
        self.user = self.user_manager.user

        # self.listbox_parameters.update_items(self.user.sampling_type_settings.setdefault('parameter_list', []))

        if not self.settings_object:
            return

        # Update dependencies
        self._update_labelframe_dependent_parameters()

        # Update flags
        self._update_labelframe_flags()

        # Update mandatory columns
        self._update_labelframe_mandatory_columns()
        
        # Update parameter mapping
        self._update_labelframe_parameter_mapping()

        # Update station mapping
        self._update_labelframe_station_mapping()

        # Update properties
        self._update_labelframe_poperties()

    def _get_dependent_parameters_from_settings(self, par=None):
        return list(self.settings_object.get_data('dependent_parameters', par))

    def _update_labelframe_dependent_parameters(self):
        try:
            pars = self._get_dependent_parameters_from_settings()
            self.combobox_widget_dependent_parameters.update_items(pars)
            self._on_select_dependent_parameter()
        except:
            pass

    def _update_labelframe_flags(self):
        flag_info = self.settings_object.get_data('flags')
        self.flag_grid_widget.reset_all_entries()
        for r, [flag, description] in enumerate(flag_info.items()):
            self.flag_grid_widget.set_value(r, 0, flag)
            self.flag_grid_widget.set_value(r, 1, description)

    def _update_labelframe_mandatory_columns(self):
        man_col_info = self.settings_object.get_data('mandatory_columns')
        self.man_col_grid_widget.reset_all_entries()
        for r, [item, col] in enumerate(man_col_info.items()):
            if type(col) == list:
                col = '; '.join(col)
            self.man_col_grid_widget.set_value(r, 0, item)
            self.man_col_grid_widget.set_value(r, 1, col)

    def _update_labelframe_parameter_mapping(self):
        map_data = self.settings_object.get_data('parameter_mapping')
        file_base = map_data.get('file_name', None)

        if file_base not in self.par_map_combobox_file.items:
            raise GISMOExceptionInvalidFileId(file_base)
        self.par_map_combobox_file.set_value(file_base)
        self._on_select_parameter_mapping_file()

        self.par_map_combobox_int_col.set_value(map_data.get('internal_column'))
        self.par_map_combobox_ext_col.set_value(map_data.get('external_column'))
        self.par_map_combobox_unit_col.set_value(map_data.get('unit_column'))
        self.par_map_entry_encoding.set_value(map_data.get('encoding'))
        self.par_map_entry_qf_prefix.set_value(map_data.get('qf_prefix'))
        self.par_map_entry_qf_suffix.set_value(map_data.get('qf_suffix'))
        self.par_map_entry_unit_start.set_value(map_data.get('unit_starts_with'))

    def _update_labelframe_station_mapping(self):
        map_data = self.settings_object.get_data('station_mapping')
        file_base = map_data.get('file_name', None)

        if file_base not in self.sta_map_combobox_file.items:
            raise GISMOExceptionInvalidFileId(file_base)
        self.sta_map_combobox_file.set_value(file_base)
        self._on_select_station_mapping_file()

        self.sta_map_combobox_int_col.set_value(map_data.get('internal_column'))
        self.sta_map_combobox_ext_col.set_value(map_data.get('external_column'))
        self.sta_map_entry_encoding.set_value(map_data.get('encoding'))
        self.sta_map_entry_header_start.set_value(map_data.get('header_starts_with'))

    def _update_labelframe_poperties(self):
        prop_info = self.settings_object.get_data('properties')
        self.prop_grid_widget.reset_all_entries()
        for r, [prop, value] in enumerate(prop_info.items()):
            self.prop_grid_widget.set_value(r, 0, prop)
            self.prop_grid_widget.set_value(r, 1, value)

    def _add_settings_file_directory(self):
        if not os.path.exists(SETTINGS_FILES_DIRECTORY):
            os.makedirs(SETTINGS_FILES_DIRECTORY)
        self.settings_files.add_directory(SETTINGS_FILES_DIRECTORY)
        
    #===========================================================================
    def _set_frame(self):

        opt = {'padx': 5,
               'pady': 5,
               'sticky': 'nsew'}

        self.frame_files = tk.LabelFrame(self, text='Settings file')
        self.frame_files.grid(row=0, column=0, columnspan=2, **opt)

        r = 1
        self.frame_dependent_parameters = tk.LabelFrame(self, text='Dependent parameters', bg='pink')
        self.frame_dependent_parameters.grid(row=r, column=0, **opt)

        self.frame_flags = tk.LabelFrame(self, text='Flags', bg='lightyellow')
        self.frame_flags.grid(row=r, column=1, **opt)

        r += 1
        self.frame_mandatory_columns = tk.LabelFrame(self, text='Mandatory columns', bg='lightgreen')
        self.frame_mandatory_columns.grid(row=r, column=0, **opt)

        self.frame_parameter_mapping = tk.LabelFrame(self, text='Parameter mapping', bg='lightblue')
        self.frame_parameter_mapping.grid(row=r, column=1, **opt)

        r += 1
        self.frame_station_mapping = tk.LabelFrame(self, text='Station mapping', bg='lightseagreen')
        self.frame_station_mapping.grid(row=r, column=0, **opt)

        self.frame_properties = tk.LabelFrame(self, text='Properties', bg='sandybrown')
        self.frame_properties.grid(row=r, column=1, **opt)

        tkw.grid_configure(self, nr_rows=4, nr_columns=2, r1=10, r2=10)

    def _set_labelframe_files(self):
        frame = self.frame_files
        opt = {'padx': 5,
               'pady': 5,
               'sticky': 'nw'}
        self.combobox_files = tkw.ComboboxWidget(frame,
                                                 align='horizontal',
                                                 title='Show file',
                                                 items=self.settings_files.get_list(),
                                                 callback_target=self._on_select_file,
                                                 **opt)

        frame_save = tk.Frame(frame)
        frame_save.grid(row=0, column=1, **opt)

        tkw.grid_configure(frame, nr_rows=1, nr_columns=2)

        self.button_save = tk.Button(frame_save, text='Save', command=self._save_file)
        self.button_save.grid(row=0, column=0, **opt)

        self.button_save_as = tk.Button(frame_save, text='Save as', command=self._save_file_as)
        self.button_save_as.grid(row=0, column=1, **opt)

        tkw.grid_configure(frame_save, nr_rows=0, nr_columns=2)

    def _set_labelframe_dependent_parameters(self):
        frame = self.frame_dependent_parameters
        opt = {'padx': 5,
               'pady': 5,
               'sticky': 'nw'}

        frame_left = tk.Frame(frame)
        frame_left.grid(row=0, column=0, **opt)

        frame_right = tk.Frame(frame)
        frame_right.grid(row=0, column=1, **opt)

        tkw.grid_configure(frame, nr_columns=2)

        # Frame left
        tk.Label(frame_left, text='If this parameter is flagged:').grid(row=0, column=0, columnspan=2, **opt)
        self.combobox_widget_dependent_parameters = tkw.ComboboxWidget(frame_left,
                                                                       callback_target=self._on_select_dependent_parameter,
                                                                       columnspan=2,
                                                                       row=1)
        self.button_add_dependent_parameter = tk.Button(frame_left, text='Add', command=self._add_dependent_parameter)
        self.button_add_dependent_parameter.grid(row=2, column=0, **opt)
        self.button_remove_dependent_parameter = tk.Button(frame_left, text='Remove', command=self._remove_dependent_parameter)
        self.button_remove_dependent_parameter.grid(row=2, column=1, **opt)

        self.button_parameter_file = tk.Button(frame_left, text='Load parameter file', command=self._load_parameter_file)
        self.button_parameter_file.grid(row=3, column=0, columnspan=2, **opt)

        tkw.grid_configure(frame_left, nr_columns=2, nr_rows=4)

        # Frame right
        prop = {'height': 6}
        tk.Label(frame_right, text='The selected parameters below are also flagged:').grid(row=0, column=0, **opt)
        self.listbox_selection_widget_dependent_parameters = tkw.ListboxSelectionWidget(frame_right,
                                                                                        prop_items=prop,
                                                                                        prop_selected=prop,
                                                                                        sort_selected=True,
                                                                                        target=self._on_select_listbox_selection_widget_dependent_parameters,
                                                                                        row=1, sticky='w')

        tkw.grid_configure(frame_right, nr_rows=2, nr_columns=1)

    def _set_labelframe_flags(self):
        frame = self.frame_flags
        opt = {'padx': 5,
               'pady': 5,
               'sticky': 'nw'}
        self.flag_grid_widget = tkw.EntryGridWidget(frame, nr_rows=10, nr_columns=2, disabled_columns=[0, 1],
                                                    in_slides=False, **opt)
        self.flag_grid_widget.set_width_for_columns({0: 5,
                                                     1: 100})

    def _set_labelframe_mandatory_columns(self):
        frame = self.frame_mandatory_columns
        opt = {'padx': 5,
               'pady': 5,
               'sticky': 'nw'}
        self.man_col_grid_widget = tkw.EntryGridWidget(frame, nr_rows=10, nr_columns=2, disabled_columns=[0, 1],
                                                       callback_on_focus_in=self._on_focus_man_col,
                                                       in_slides=False, **opt)
        self.man_col_grid_widget.set_width_for_columns({0: 10,
                                                        1: 90})

    def _set_labelframe_parameter_mapping(self):
        frame = self.frame_parameter_mapping
        opt = {'padx': 5,
               'pady': 5,
               'sticky': 'nw'}

        combobox_width = 40
        r = 0
        # File name
        mapping_files = self.mapping_files.get_list()
        tk.Label(frame, text='File name').grid(row=r, column=0, **opt)
        self.par_map_combobox_file = tkw.ComboboxWidget(frame, row=r, column=1,
                                                        prop_combobox={'width': combobox_width},
                                                        items=mapping_files,
                                                        callback_target=self._on_select_parameter_mapping_file,
                                                        **opt)
        r += 1
        # External column
        tk.Label(frame, text='External column').grid(row=r, column=0, **opt)
        self.par_map_combobox_ext_col = tkw.ComboboxWidget(frame, row=r, column=1,
                                                         callback_target=self._on_change_parameter_mapping,
                                                         prop_combobox={'width': combobox_width},
                                                         **opt)
        r += 1
        # Internal column
        tk.Label(frame, text='Internal column').grid(row=r, column=0, **opt)
        self.par_map_combobox_int_col = tkw.ComboboxWidget(frame, row=r, column=1,
                                                           callback_target=self._on_change_parameter_mapping,
                                                           prop_combobox={'width': combobox_width},
                                                           **opt)
        r += 1
        # Unit column
        tk.Label(frame, text='Unit column').grid(row=r, column=0, **opt)
        self.par_map_combobox_unit_col = tkw.ComboboxWidget(frame, row=r, column=1,
                                                            callback_target=self._on_change_parameter_mapping,
                                                            prop_combobox={'width': combobox_width},
                                                            **opt)
        r = 0
        # File encoding
        tk.Label(frame, text='File encoding').grid(row=r, column=2, **opt)
        self.par_map_entry_encoding = tkw.EntryWidget(frame, row=r, column=3,
                                                      prop_entry={'width': 10},
                                                      **opt)
        self.par_map_entry_encoding.disable_widget()
        r += 1

        # qf_prefix
        tk.Label(frame, text='QF prefix').grid(row=r, column=2, **opt)
        self.par_map_entry_qf_prefix = tkw.EntryWidget(frame, row=r, column=3,
                                                       prop_entry={'width': 10},
                                                       **opt)
        self.par_map_entry_qf_prefix.disable_widget()
        r += 1

        # qf_suffix
        tk.Label(frame, text='QF suffix').grid(row=r, column=2, **opt)
        self.par_map_entry_qf_suffix = tkw.EntryWidget(frame, row=r, column=3,
                                                       prop_entry={'width': 10},
                                                       **opt)
        self.par_map_entry_qf_suffix.disable_widget()
        r += 1

        # Unit starts with
        tk.Label(frame, text='Unit starts with (if in external column)').grid(row=r, column=2, **opt)
        self.par_map_entry_unit_start = tkw.EntryWidget(frame, row=r, column=3,
                                                        prop_entry={'width': 10},
                                                        **opt)
        self.par_map_entry_unit_start.disable_widget()

    def _set_labelframe_station_mapping(self):
        frame = self.frame_station_mapping
        opt = {'padx': 5,
               'pady': 5,
               'sticky': 'nw'}

        combobox_width = 40
        r = 0
        # File name
        mapping_files = self.mapping_files.get_list()
        tk.Label(frame, text='File name').grid(row=r, column=0, **opt)
        self.sta_map_combobox_file = tkw.ComboboxWidget(frame, row=r, column=1,
                                                        prop_combobox={'width': combobox_width},
                                                        items=mapping_files,
                                                        callback_target=self._on_select_station_mapping_file,
                                                        **opt)
        r += 1
        # External column
        tk.Label(frame, text='External column').grid(row=r, column=0, **opt)
        self.sta_map_combobox_ext_col = tkw.ComboboxWidget(frame, row=r, column=1,
                                                           callback_target=self._on_change_station_mapping,
                                                           prop_combobox={'width': combobox_width},
                                                           **opt)
        r += 1
        # Internal column
        tk.Label(frame, text='Internal column').grid(row=r, column=0, **opt)
        self.sta_map_combobox_int_col = tkw.ComboboxWidget(frame, row=r, column=1,
                                                           callback_target=self._on_change_station_mapping,
                                                           prop_combobox={'width': combobox_width},
                                                           **opt)
        r = 0
        # File encoding
        tk.Label(frame, text='File encoding').grid(row=r, column=2, **opt)
        self.sta_map_entry_encoding = tkw.EntryWidget(frame, row=r, column=3,
                                                      prop_entry={'width': 20},
                                                      **opt)
        self.sta_map_entry_encoding.disable_widget()
        r += 1

        # qf_prefix
        tk.Label(frame, text='Header starts with').grid(row=r, column=2, **opt)
        self.sta_map_entry_header_start = tkw.EntryWidget(frame, row=r, column=3,
                                                          prop_entry={'width': 20},
                                                          **opt)
        self.sta_map_entry_header_start.disable_widget()
        r += 1

        # qf_suffix
        tk.Label(frame, text='QF suffix').grid(row=r, column=2, **opt)
        self.par_map_entry_qf_suffix = tkw.EntryWidget(frame, row=r, column=3,
                                                       prop_entry={'width': 20},
                                                       **opt)
        self.par_map_entry_qf_suffix.disable_widget()
        r += 1

        # Unit starts with
        tk.Label(frame, text='Unit starts with (if in external column)').grid(row=r, column=2, **opt)
        self.par_map_entry_unit_start = tkw.EntryWidget(frame, row=r, column=3,
                                                        prop_entry={'width': 20},
                                                        **opt)
        self.par_map_entry_unit_start.disable_widget()

    def _set_labelframe_properties(self):
        frame = self.frame_properties
        opt = {'padx': 5,
               'pady': 5,
               'sticky': 'nw'}

        self.prop_grid_widget = tkw.EntryGridWidget(frame, nr_rows=10, nr_columns=2, disabled_columns=[0, 1],
                                                    in_slides=False, **opt)
        self.prop_grid_widget.set_width_for_columns({0: 20,
                                                     1: 10})

        # r = 0
        # # File encoding
        # tk.Label(frame, text='File encoding').grid(row=r, column=2, **opt)
        # self.prop_entry_encoding = tkw.EntryWidget(frame, row=r, column=3,
        #                                               prop_entry={'width': 20},
        #                                               **opt)
        # self.prop_entry_encoding.disable_widget()
        # r += 1
        #
        # # Column separator
        # tk.Label(frame, text='Column separator').grid(row=r, column=2, **opt)
        # self.prop_entry_col_sep = tkw.EntryWidget(frame, row=r, column=3,
        #                                               prop_entry={'width': 20},
        #                                               **opt)
        # self.prop_entry_col_sep.disable_widget()
        # r += 1
        #
        # # Comment ID
        # tk.Label(frame, text='Comment ID').grid(row=r, column=2, **opt)
        # self.prop_entry_comment_id = tkw.EntryWidget(frame, row=r, column=3,
        #                                                prop_entry={'width': 20},
        #                                                **opt)
        # self.prop_entry_comment_id.disable_widget()
        # r += 1
        #
        # # Missing value
        # tk.Label(frame, text='Missing value').grid(row=r, column=2, **opt)
        # self.par_map_entry_unit_start = tkw.EntryWidget(frame, row=r, column=3,
        #                                                prop_entry={'width': 20},
        #                                                **opt)
        # self.par_map_entry_unit_start.disable_widget()

    def _on_change_parameter_mapping(self):
        """
        Called from all widgets in parameter_mapping.
        :return:
        """
        self.settings_object.set_data('parameter_mapping', 'file_name', self.par_map_combobox_file.get_value())
        self.settings_object.set_data('parameter_mapping', 'internal_column', self.par_map_combobox_int_col.get_value())
        self.settings_object.set_data('parameter_mapping', 'external_column', self.par_map_combobox_ext_col.get_value())
        self.settings_object.set_data('parameter_mapping', 'unit_column', self.par_map_combobox_unit_col.get_value())
        # self.settings_object.set_data('parameter_mapping', 'encoding', self.par_map_entry_encoding.get_value())
        # self.settings_object.set_data('parameter_mapping', 'qf_prefix', self.par_map_entry_qf_prefix.get_value())
        # self.settings_object.set_data('parameter_mapping', 'qf_suffix', self.par_map_entry_qf_suffix.get_value())
        # self.settings_object.set_data('parameter_mapping', 'unit_starts_with', self.par_map_entry_unit_start.get_value())
        
    def _on_change_station_mapping(self):
        """
        Called from all widgets in station_mapping.
        :return:
        """
        self.settings_object.set_data('station_mapping', 'file_name', self.sta_map_combobox_file.get_value())
        self.settings_object.set_data('station_mapping', 'internal_column', self.sta_map_combobox_int_col.get_value())
        self.settings_object.set_data('station_mapping', 'external_column', self.sta_map_combobox_ext_col.get_value())

    def _on_select_parameter_mapping_file(self):
        mapping_file = self.par_map_combobox_file.get_value()
        col_name_list = self.mapping_files.get_columns_names_in_file(mapping_file)
        col_name_list = [''] + col_name_list
        self.par_map_combobox_ext_col.update_items(col_name_list[:])
        self.par_map_combobox_int_col.update_items(col_name_list[:])
        self.par_map_combobox_unit_col.update_items(col_name_list[:])
        
    def _on_select_station_mapping_file(self):
        station_file = self.sta_map_combobox_file.get_value()
        col_name_list = self.mapping_files.get_columns_names_in_file(station_file)
        col_name_list = [''] + col_name_list
        self.sta_map_combobox_ext_col.update_items(col_name_list[:])
        self.sta_map_combobox_int_col.update_items(col_name_list[:])

    def _on_select_listbox_selection_widget_dependent_parameters(self):
        par = self.combobox_widget_dependent_parameters.get_value()
        dependent_pars = self.listbox_selection_widget_dependent_parameters.get_selected()
        if len(dependent_pars) == 0:
            self.settings_object.remove_data('dependent_parameters', par)
        else:
            self.settings_object.set_data('dependent_parameters', par, dependent_pars)

    def _on_select_dependent_parameter(self):
        self._update_listbox_selection_widget_dependent_parameters()

    def _on_select_file(self):
        print('Select file')
        self._update_settings_object()
        self.update_page()

    def _on_focus_man_col(self, grid_widget):
        def _ok():
            value = widget.get_value()
            values_string = '; '.join(value)
            grid_widget.set_value(values_string)
            self.settings_object.set_data('mandatory_columns', item, value)

            popup_frame.destroy()
            grid_widget.unfocus()

        def _cancel():
            popup_frame.destroy()
            grid_widget.unfocus()

        col = grid_widget.col_in_grid
        row = grid_widget.row_in_grid
        if col == 0:
            return

        popup_frame = tk.Toplevel(self)
        popup_frame.protocol('WM_DELETE_WINDOW', _cancel)
        current_parameter_list = self._get_parameter_list_from_user()

        grid = dict(sticky='w',
                    padx=5,
                    pady=5)

        item = self.man_col_grid_widget.get_value(row, 0)
        value = self.man_col_grid_widget.get_value(row, col)
        settings_value = self.settings_object.get_data('mandatory_columns', item)
        settings_type = type(settings_value)
        r = 0
        if settings_type == list:
            value_list = [v.strip() for v in value.split(';')]
            self._save_parameter_list_to_user(value_list)
            current_parameter_list = self._get_parameter_list_from_user()
            tk.Label(popup_frame,
                     text=f'Select parameters to build mandatory column "{item}"').grid(row=r, column=0, **grid)
            r += 1
            widget = tkw.ListboxSelectionWidget(popup_frame,
                                                items=current_parameter_list,
                                                selected_items=value_list,
                                                row=1,
                                                **grid)
            r += 1
        else:
            widget = tkw.ComboboxWidget(popup_frame,
                                        title=f'Set parameter for mandatory column "{item}"',
                                        items=current_parameter_list,
                                        default_item=value,
                                        **grid)
            r += 1

        widget_button_done = tk.Button(popup_frame, text='Ok', command=_ok)
        widget_button_done.grid(row=r, column=0, **grid)
        widget_button_done = tk.Button(popup_frame, text='Cancel', command=_cancel)
        widget_button_done.grid(row=r, column=1, **grid)
        tkw.grid_configure(popup_frame, nr_rows=3, nr_columns=2)

    def _update_combobox_files(self):
        self.combobox_files.update_items(sorted(self.settings_files.get_list()))

    def _update_settings_object(self):
        file_name = self.combobox_files.get_value()
        file_path = self.settings_files.get_path(file_name)
        directory = os.path.dirname(file_path)
        self.settings_object = SamplingTypeSettings(file_name, directory=directory)

    def _update_listbox_selection_widget_dependent_parameters(self):
        """
        Updates self.listbox_selection_widget_dependent_parameters based on selected item in
        elf.combobox_widget_dependent_parameters
        :return:
        """
        par = self.combobox_widget_dependent_parameters.get_value()
        selected_pars = self.settings_object.get_data('dependent_parameters', par)
        available_parameters = self._get_parameter_list_from_user()
        all_pars = sorted(set(selected_pars + available_parameters))
        if par in all_pars:
            all_pars.pop(all_pars.index(par))
        self.listbox_selection_widget_dependent_parameters.update_items(all_pars)
        self.listbox_selection_widget_dependent_parameters.move_items_to_selected(selected_pars)
        self._save_parameter_list_to_user(all_pars, include_current=True)

    def _get_parameter_list_from_user(self):
        return self.user.sampling_type_settings.setdefault('parameter_list', [])
    
    def _save_parameter_list_to_user(self, parameter_list, include_current=True):
        all_pars = []
        if include_current:
            all_pars = self._get_parameter_list_from_user()
        all_pars = sorted(set(all_pars + parameter_list))
        self.user.sampling_type_settings.set('parameter_list', all_pars)
    
    def _load_parameter_file(self):
        open_directory = self.parent_app.get_open_directory()
        file_path = filedialog.askopenfilename(initialdir=open_directory,
                                               filetypes=[('Parameter file', '*.txt')])
        if not file_path:
            return
        file_par_list = spl.file_io.get_list_from_file(file_path=file_path)
        self._save_parameter_list_to_user(file_par_list, include_current=True)
        # self._update_listbox_parameters()
        self.parent_app.set_open_directory(file_path)
        self._on_select_dependent_parameter()

    def _remove_dependent_parameter(self):
        parameter = self.combobox_widget_dependent_parameters.get_value()
        self.combobox_widget_dependent_parameters.delete_item(parameter)
        # Delete in settings
        self.settings_object.delete_data('dependent_parameters', parameter)

    def _add_dependent_parameter(self):
        def _add_parameter():
            parameter = widget_parameter.get_value()
            if not parameter:
                main_gui.show_information('Create dependencies', 'No parameter selected')
                return
            try:
                current_par = self.combobox_widget_dependent_parameters.get_value()
                # Add parameter to settings
                self.settings_object.add_data('dependent_parameters', parameter, [])
                print(self.settings_object.get_data('dependent_parameters'))
                # Set parameter list
                self.combobox_widget_dependent_parameters.update_items(self._get_dependent_parameters_from_settings())
                if intvar_show_parameter.get():
                    self.combobox_widget_dependent_parameters.set_value(parameter)
                else:
                    self.combobox_widget_dependent_parameters.set_value(current_par)
                self._update_listbox_selection_widget_dependent_parameters()
            except GUIException as e:
                main_gui.show_error('Creating dependencies', '{}\nSomething went wrong Try again!'.format(e.message))
            popup_frame.destroy()

        def _cancel():
            popup_frame.destroy()

        popup_frame = tk.Toplevel(self)
        current_parameter_list = self._get_parameter_list_from_user()

        grid = dict(sticky='w',
                    padx=5,
                    pady=5)

        widget_parameter = tkw.ComboboxWidget(popup_frame, title='Add dependent parameters for parameter', items=current_parameter_list,
                                                **grid)

        intvar_show_parameter = tk.IntVar()
        widget_checkbutton_show_parameter = tk.Checkbutton(popup_frame, text="Show dependencies", variable=intvar_show_parameter)
        widget_checkbutton_show_parameter.grid(row=1, column=1, **grid)
        intvar_show_parameter.set(1)

        widget_button_done = tk.Button(popup_frame, text='Add parameter', command=_add_parameter)
        widget_button_done.grid(row=2, column=0, **grid)
        widget_button_done = tk.Button(popup_frame, text='Cancel', command=_cancel)
        widget_button_done.grid(row=2, column=1, **grid)
        tkw.grid_configure(popup_frame, nr_rows=3, nr_columns=2)

    def _save_file(self):
        try:
            self.settings_object.save()
        except GISMOExceptionSaveNotAllowed as e:
            main_gui.show_warning('Saving Sampling type settings',
                                  f'Not allowed to overwrite file {self.settings_object.file_name}. '
                                  f'Please save with a different name.')

    def _save_file_as(self):
        def _save_file():
            file_name = stringvar_entry.get()
            if not file_name:
                main_gui.show_information('Save file', 'No file name selected')
                return
            if file_name in self.settings_files.get_list():
                from tkinter import messagebox
                overwrite = messagebox.askyesno('Save file', f'File name "{file_name}" exist. Would you like to overwrite this file?')
                if not overwrite:
                    return
            try:
                self.settings_object.file_name = (file_name, SETTINGS_FILES_DIRECTORY)  # Setter method
                self.settings_object.save()
                # Update Settings files object
                self.settings_files.add_directory(SETTINGS_FILES_DIRECTORY)  # This will update files
                # Update combobox
                self._update_combobox_files()
                self.combobox_files.set_value(file_name)
            except GISMOExceptionSaveNotAllowed:
                main_gui.show_warning('Saving Sampling type settings',
                                      f'Not allowed to overwrite file {self.settings_object.file_name}. '
                                      f'Please save with a different name.')
            except GUIException as e:
                main_gui.show_error('Save file', '{}\nSomething went wrong Try again!'.format(e.message))
            popup_frame.destroy()

        def _cancel():
            popup_frame.destroy()

        popup_frame = tk.Toplevel(self)

        grid = dict(sticky='w',
                    padx=5,
                    pady=5)

        tk.Label(popup_frame, text='File name:').grid(row=0, column=0, **grid)
        stringvar_entry = tk.StringVar()
        entry = tk.Entry(popup_frame, textvariable=stringvar_entry, width=40)
        entry.grid(row=1, column=0, columnspan=2, **grid)

        widget_button_done = tk.Button(popup_frame, text='Save file', command=_save_file)
        widget_button_done.grid(row=2, column=0, **grid)
        widget_button_done = tk.Button(popup_frame, text='Cancel', command=_cancel)
        widget_button_done.grid(row=2, column=1, **grid)
        tkw.grid_configure(popup_frame, nr_rows=3, nr_columns=2)