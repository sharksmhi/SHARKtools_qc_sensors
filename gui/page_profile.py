#!/usr/bin/env python
# -*- coding:utf-8 -*-
#
# Copyright (c) 2016-2017 SMHI, Swedish Meteorological and Hydrological Institute 
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).

import datetime
import logging
import os
import re
import tkinter as tk
from tkinter import ttk
import traceback

import matplotlib
import numpy as np
import pandas as pd
import sharkpylib.plot.contour_plot as contour_plot
import sharkpylib.plot.plot_selector as plot_selector
import sharkpylib.tklib.tkinter_widgets as tkw
import sharkpylib.tklib.tkmap as tkmap
from sharkpylib.gismo.exceptions import *

import core
import gui as main_gui
from core.exceptions import *
from plugins.SHARKtools_qc_sensors import gui

"""
================================================================================
================================================================================
================================================================================
"""
class PageProfile(tk.Frame):
    """
    """
    def __init__(self, parent, parent_app, **kwargs):
        tk.Frame.__init__(self, parent, **kwargs)

        self.parent = parent
        self.parent_app = parent_app
        self.main_app = self.parent_app.main_app
        self.user_manager = parent_app.user_manager
        self.user = self.user_manager.user
        self.session = parent_app.session

        self.logger = self.main_app.logger

        self.colormaps = core.Colormaps()

        self.gismo_sampling_type_settings = None

        self.current_file_id_list = []
        self.current_ref_file_id = ''
        self.current_file_id = ''
        self.current_sampling_type = ''
        self.current_parameter = ''

        self.toplevel_map_widget_1 = None
        self.toplevel_map_widget_2 = None

        self.info_popup = self.parent_app.info_popup

        self.current_correlation_plot = None

        self.allowed_compare_files = ['PhysicalChemical']

        self._reset_merge_data()

    #===========================================================================
    def startup(self):
        self._set_frame()

        self._add_popup_menu_to_fig()
        self.update_page()

    #===========================================================================
    def update_page(self, **kwargs):
        self.user = self.user_manager.user
        self.info_popup = self.parent_app.info_popup

        # Update filter widget
        self.select_data_widget.update_widget(**kwargs)

        # Update referens file
        self._update_frame_reference_file()

        self._update_map_1()  # To add background data

    def _update_plot_background(self, file_id=None):
        if not self.current_parameter:
            return

        gismo_objects = []
        if file_id:
            gismo_objects.append(self.session.get_gismo_object(file_id))
            clear_plot = False
        else:
            file_id_list = self.select_data_widget.get_filtered_file_id_list()
            for file_id in file_id_list:
                gismo_objects.append(self.session.get_gismo_object(file_id))
            clear_plot = True
            self.current_file_id_list = file_id_list

        gui.communicate.update_profile_plot_background(gismo_objects=gismo_objects,
                                                                        par=self.current_parameter,
                                                                        plot_object=self.plot_object,
                                                                        flag_widget=self.flag_widget,
                                                                        help_info_function=self.main_app.update_help_information,
                                                                        call_targets=True,
                                                                        clear_plot=clear_plot,
                                                                        user=self.user)

        self._sync_x_axis('plot', call_targets=False)
        self._sync_z_axis('plot')

    def _reset_merge_data(self):
        self.current_gismo_match_object = None
        self.current_merge_data = {}
        self.current_compare_selection = []

    # def _update_frame_data_file(self):
    #     loaded_file_list = self.parent_app.get_loaded_files_list()
    #     add_file_list = []
    #     for item in loaded_file_list:
    #         for data_file in self.allowed_data_files:
    #             if item.startswith(data_file):
    #                 add_file_list.append(item)
    #     #self.select_data_widget.update_items(add_file_list)

    def _update_frame_reference_file(self):
        # Update reference file combobox. Should not include selected file.
        loaded_file_list = self.parent_app.get_loaded_files_list()
        add_ref_file_list = []

        selected_file_id_dict = self.select_data_widget.get_selected()
        print('selected_file_id_dict')
        print(selected_file_id_dict)

        for item in loaded_file_list:
            if item == None:
                continue
            for data_file in self.allowed_compare_files:
                if item.startswith(data_file):
                    add_ref_file_list.append(item)
        self.select_ref_data_widget.update_items(add_ref_file_list)

    #===========================================================================
    def _set_frame(self):
        self._set_labelframes()
        self._set_frame_plot()
        self._set_frame_options()

    #===========================================================================
    def _set_labelframes(self):

        opt = {'padx': 5,
               'pady': 5,
               'sticky': 'nsew'}

        #-----------------------------------------------------------------------
        # Creating frames
        self.labelframe_plot = ttk.Labelframe(self, text='Plot')
        self.labelframe_plot.grid(row=0, column=0, **opt)

        self.labelframe_options = tk.Frame(self)
        self.labelframe_options.grid(row=0, column=1, **opt)

        tkw.grid_configure(self, nr_columns=2, c0=7, c1=1)



    #===========================================================================
    def _set_frame_plot(self):
        """
        """
        frame = self.labelframe_plot
#        self.notebook_plot = tkw.NotebookWidget(frame, ['Time plot', 'Contour plot'])
        self.notebook_plot = tkw.NotebookWidget(frame, ['Single profile plot', 'Correlation plot'])

        tkw.grid_configure(frame)

        self._set_notebook_single_profile_plot()
        self._set_notebook_compare_plot()
#        self._set_notebook_contour_plot()

    def _set_notebook_contour_plot(self):
        frame = self.notebook_plot.frame_contour_plot

        self.plot_object_contour = contour_plot.PlotContour()

        self.plot_widget_contour = tkw.PlotFrame(frame,
                                                 self.plot_object_contour,
                                                 pack=False,
                                                 include_toolbar=False)


    def _set_notebook_single_profile_plot(self):
        frame = self.notebook_plot.frame_single_profile_plot

        self.plot_object = plot_selector.Plot(sync_colors=True,
                                              allow_two_axis=False,
                                              orientation='horizontal',
                                              figsize=(2, 2),
                                              hover_target=None,
                                              callback_on_disconnect_events=self._add_popup_menu_to_fig,
                                              )
        margins = {'right': 0.03,
                   'left': 0.08,
                   'top': 0.04,
                   'bottom': 0.08}

        self.plot_object.add_first_ax(margins=margins)

        # Target to plot object is called when set range is active.
        self.plot_object.add_range_target(self._callback_plot_range)

        self.plot_widget = tkw.PlotFrame(frame,
                                         self.plot_object,
                                         pack=False,
                                         include_toolbar=False)

        # items = [{'name': 'Mark min'},
        #          {'name': 'Mark max'}]
        # self.fig_menu_popup_widget = tkw.MenuWidget(frame, bind_widget=frame, items=items)



    def _add_popup_menu_to_fig(self):
        items = [{'name': 'Mark min',
                  'command': self.zrange_selection_widget._mark_max},
                 {'name': 'Mark max',
                  'command': self.zrange_selection_widget._mark_min}]
        self.fig_menu_popup_widget = tkw.MenuWidget(self.notebook_plot.frame_single_profile_plot,
                                                    bind_command='button_press_event',
                                                    bind_fig=self.plot_object.fig,
                                                    items=items,
                                                    button=3)

    def _on_plot_hover(self):
        if 'ferrybox' not in self.current_sampling_type.lower():
            return
        time_num = self.plot_object.hover_x
        # print(time_num)
        # return
        if not time_num:
            return
        # datetime_object = datetime.datetime.fromordinal(int(time_num))
        datetime_object = pd.Timestamp.tz_localize(pd.to_datetime(matplotlib.dates.num2date(time_num)), None)
        # The time is rounded so we wont find the exakt time in data. Widen the search for data and pick closest point.
        dt = pd.Timedelta(hours=1)
        # dt = pd.to_timedelta(datetime.timedelta(days=1))
        data = self.session.get_data(self.current_file_id, 'time', 'lat', 'lon',
                                     filter_options={'time_start': datetime_object-dt,
                                                     'time_end': datetime_object+dt})
        if not len(data['time']):
            self.map_widget_1.delete_marker(marker_id='position')
            return

        index = 0
        closest_t = None
        for i, t in enumerate(data['time']):
            t = pd.to_datetime(t)
            dt = abs(t - datetime_object)
            if not closest_t:
                closest_t = dt
            else:
                if dt < closest_t:
                    closest_t = dt
                    index = i

        map_list = [self.map_widget_1, self.toplevel_map_widget_1]

        for map_widget in map_list:
            if not map_widget:
                continue
            map_widget.add_markers(lat=data['lat'][index],
                                   lon=data['lon'][index],
                                   marker_id='position',
                                   marker=self.user.map_prop.setdefault('ferrybox_pos_marker', 'o'),
                                   markersize=self.user.map_prop.setdefault('ferrybox_pos_markersize', 10),
                                   color=self.user.map_prop.setdefault('ferrybox_pos_color', 'red'))

    def _set_notebook_compare_plot(self):
        frame = self.notebook_plot.frame_correlation_plot
        try:
            self.frame_correlation.destroy()
        except:
            pass
        self.frame_correlation = tk.Frame(frame)
        self.frame_correlation.grid(row=0, column=0, sticky='nsew')
        tkw.grid_configure(self.frame_correlation)


        self.plot_object_compare = plot_selector.Plot(sync_colors=True,
                                                      allow_two_axis=False,
                                                      orientation='horizontal',
                                                      figsize=(2, 2),
                                                      hover_target=None)
        margins = {'right': 0.06,
                   'left': 0.08,
                   'top': 0.06,
                   'bottom': 0.10}

        self.plot_object_compare.add_first_ax(margins=margins)

        # Target to plot object is called when set range is active.
        # self.plot_object_compare.add_range_target(self._callback_plot_range)

        self.plot_widget_compare = tkw.PlotFrame(self.frame_correlation,
                                                 self.plot_object_compare,
                                                 pack=False,
                                                 include_toolbar=False)

    #===========================================================================
    def _set_frame_options(self):

        frame = self.labelframe_options

        opt = {'padx': 5,
               'pady': 5,
               'sticky': 'nsew'}

        self.labelframe_data = tk.LabelFrame(frame, text='Select data file')
        self.labelframe_data.grid(row=0, column=0, **opt)

        self.labelframe_parameter = tk.LabelFrame(frame, text='Parameter')
        self.labelframe_parameter.grid(row=1, column=0, **opt)

#        self.labelframe_parameter_contour = tk.LabelFrame(frame, text='Contour plot')
#        self.labelframe_parameter_contour.grid(row=2, column=1, **opt)

        self.frame_notebook = tk.Frame(frame)
        self.frame_notebook.grid(row=2, column=0, **opt)

        # tkw.grid_configure(frame, nr_rows=4, r0=4, r1=4, r3=5)
        tkw.grid_configure(frame, nr_rows=3, nr_columns=1, r0=10, r2=10)

        self.select_data_widget = gui.widgets.FilterWidgetTable(self.labelframe_data,
                                                                                 parent_app=self.parent_app,
                                                                                 main_app=self.main_app,
                                                                                 session=self.session,
                                                                                 callback_update=self._callback_filter_update,
                                                                                 callback_select=self._callback_filter_select,
                                                                                 file_id_startswith=['ctd_profile', 'nodc_ctd_profile'],
                                                                                 prop_frame={},
                                                                                 prop_treeview={'height': 3})
        tkw.grid_configure(self.labelframe_data)

#         # Data file
#         self.select_data_widget = tkw.ComboboxWidget(self.labelframe_data,
#                                                    title='',
#                                                    prop_combobox=prop_combobox,
# #                                                   callback_target=self._on_select_parameter,
#                                                    row=1,
#                                                    pady=5,
#                                                    sticky='w')
#
#         self.button_load_current = tk.Button(self.labelframe_data,
#                                              text='Update data file',
#                                              command=self._update_file)
#         self.button_load_current.grid(row=0, column=1, sticky='w', **pad)
#
#         file_frame = tk.Frame(self.labelframe_data)
#         file_frame.grid(row=1, column=0, columnspan=2, sticky='w', **pad)
#         tk.Label(file_frame, text='Active file:').grid(row=0, column=0, sticky='w', **pad)
#         self.stringvar_current_data_file = tk.StringVar()
#         tk.Label(file_frame,
#                  textvariable=self.stringvar_current_data_file,
#                  bg=None).grid(row=0, column=1, sticky='w', **pad)
#         tkw.grid_configure(file_frame, nr_columns=2)
#         tkw.grid_configure(self.labelframe_data, nr_rows=2, nr_columns=2)

        #----------------------------------------------------------------------
        # Parameter listbox
        self.parameter_widget = tkw.ComboboxWidget(self.labelframe_parameter,
                                                   title='',
                                                   prop_combobox={'width': 40},
                                                   callback_target=self._on_select_parameter,
                                                   row=0,
                                                   pady=0,
                                                   sticky='w')

        self.xrange_widget = gui.AxisSettingsFloatWidget(self.labelframe_parameter,
                                                         self.plot_object,
                                                         callback=self._callback_xaxis_widgets,
                                                         label='Set range',
                                                         axis='x',
                                                         row=0,
                                                         column=1,
                                                         pady=1,
                                                         sticky='nsew')
        tkw.grid_configure(self.labelframe_parameter, nr_columns=2)

        #                                            row=0)
        self.notebook_options = tkw.NotebookWidget(self.frame_notebook,
                                                   frames=['Depth range', 'Select data to flag', 'Flag selected data',
                                                           'Compare', 'Save data', 'Save plots', 'Map', 'Automatic QC'],
                                                   row=0)
        tkw.grid_configure(self.frame_notebook, nr_rows=1)


        self._set_notebook_frame_depth_range()
        self._set_notebook_frame_select()
        self._set_notebook_frame_flag()
        self._set_notebook_frame_compare()
        self._set_notebook_frame_save_data()
        # self._set_notebook_frame_save_plots()
        self._set_notebook_frame_map()
        self._set_notebook_frame_automatic_qc()

    def _callback_filter_update(self, **kwargs):
        file_id_list = self.select_data_widget.get_filtered_file_id_list()

        self._update_parameter_list()

        if file_id_list == self.current_file_id_list:
            if kwargs.get('update_plot_background'):
                self._update_plot_background()
            return

        self._update_notebook_frame_flag()

        self._update_plot_background()

        self.qc_routine_widget.update_widget(file_id_list)

    def _callback_filter_select(self, **kwargs):
        self._set_current_file()
        self.save_file_widget.set_file_path(self.current_file_path)
        self._on_select_parameter()

    def _set_notebook_frame_automatic_qc(self):
        frame = self.notebook_options.frame_automatic_qc
        padx = 5
        pady = 5
        self.qc_routine_widget = gui.widgets.QCroutineWidget(frame,
                                                              parent_app=self.parent_app,
                                                              main_app=self.main_app,
                                                              session=self.session,
                                                              sticky='nw')

        self.boolvar_run_all_files = tk.BooleanVar()
        self.checkbutton_run_all_files = tk.Checkbutton(frame, text='Run QC on all files',
                                                        variable=self.boolvar_run_all_files)
        self.checkbutton_run_all_files.grid(row=1, column=0, sticky='sw', padx=padx, pady=pady)

        self.button_run_automatic_qc = tk.Button(frame, text='Run QC', command=self._run_qc)
        self.button_run_automatic_qc.grid(row=2, column=0, sticky='sw', padx=padx, pady=pady)

        tkw.grid_configure(frame, nr_rows=3)

    def _run_qc(self):
        """
        Runs quality control on the given file_id_list.

        :param file_id_list: sting or list of file_ids
        :return:
        """
        if self.boolvar_run_all_files.get():
            file_id_list = self.select_data_widget.get_filtered_file_id_list()
        else:
            if not self.current_file_id:
                main_gui.show_information('No file selected', 'No file selected for Quality Control. '
                                                         'Select a file in list or check '
                                                         '"Run QC on all filtered files" to run QC on all files.')
                return
            else:
                file_id_list = [self.current_file_id]
        selected_qc_routines = self.qc_routine_widget.get_selected_qc_routines()
        for qc_routine in selected_qc_routines:
            options = self.user.qc_routine_options.get_settings(par=qc_routine)
            # Run QC with matching file_id and qc_routines
            try:
                self.session.run_automatic_qc(file_id=file_id_list, qc_routine=qc_routine, **options)
            except ImportError as e:
                main_gui.show_error('Import error', e)

            except GISMOExceptionMissingInputArgument as e:
                if 'parameter' in e.message and 'list' in e.message:
                    main_gui.show_warning('No parameter selected', 'You need to specify parameters for QC routine {} '
                                                                  'Please open option ans select parameters.'.format(qc_routine))
                    self.logger.warning(e)
                elif 'save' in e.message and 'directory' in e.message:
                    main_gui.show_warning('Invalid save directory', 'It seems like the saving directory for QC routine {} '
                                                               'is not valid. Please open option and change or update '
                                                               'directory.'.format(qc_routine))
                    self.logger.warning(e)
                else:
                    main_gui.show_error('Unknown error', 'An unknown error related to missing input variable occurred. '
                                                    f'Please contact the suupport team: shark@smhi.se\n\n{traceback.format_exc()}')
                    self.logger.error(e)
                return

        self.update_page(update_plot_background=True)
        select_str = '\n'.join(selected_qc_routines)
        main_gui.show_information('Automatic quality control',
                                  f'Successfully performed the following quality control(s) on {len(file_id_list)} files: \n{select_str}')

    def _set_notebook_frame_map(self):
        frame = self.notebook_options.frame_map
        frame_map_1 = tk.Frame(frame)
        frame_map_1.grid(row=0, column=0, sticky='nsew')
        frame_map_2 = tk.Frame(frame)
        frame_map_2.grid(row=0, column=1, sticky='nsew')
        frame_buttons = tk.Frame(frame)
        frame_buttons.grid(row=1, column=0, columnspan=2, sticky='nsew')
        tkw.grid_configure(frame, nr_columns=2, nr_rows=2, r0=10)
        tkw.grid_configure(frame_map_1)
        tkw.grid_configure(frame_map_2)
        tkw.grid_configure(frame_buttons, nr_columns=2)

        # Get map boundries
        boundaries = self._get_map_boundaries()

        self.map_widget_1 = tkmap.TkMap(frame_map_1, boundaries=boundaries, map_resolution='c')
        self.map_widget_2 = tkmap.TkMap(frame_map_2, boundaries=boundaries, map_resolution='c')

        self.button_frame_map_1 = tk.Button(frame_buttons, text='Map window', command=self._popup_map_1)
        self.button_frame_map_1.grid(row=0, column=0, sticky='nsew', pady=5)
        self.button_frame_map_2 = tk.Button(frame_buttons, text='Map window', command=self._popup_map_2)
        self.button_frame_map_2.grid(row=0, column=1, sticky='nsew', pady=5)

    def _popup_map_1(self):
        def delete_map_1():
            self.toplevel_frame_map_1.destroy()
            self.toplevel_map_widget_1 = None

        if self.toplevel_map_widget_1:
            return

        self.toplevel_frame_map_1 = tk.Toplevel(self.parent_app)

        boundaries = self._get_map_boundaries()

        self.toplevel_map_widget_1 = tkmap.TkMap(self.toplevel_frame_map_1,
                                                 boundaries=boundaries,
                                                 toolbar=True,
                                                 figsize=(5, 5))
        tkw.grid_configure(self.toplevel_frame_map_1)
        self._update_map_1(self.toplevel_map_widget_1)

        self.toplevel_frame_map_1.protocol('WM_DELETE_WINDOW', delete_map_1)

    def _popup_map_2(self):
        def delete_map_2():
            self.toplevel_frame_map_2.destroy()
            self.toplevel_map_widget_2 = None

        if self.toplevel_map_widget_2:
            return
        self.toplevel_frame_map_2 = tk.Toplevel(self.parent_app)

        boundaries = self._get_map_boundaries()

        self.toplevel_map_widget_2 = tkmap.TkMap(self.toplevel_frame_map_2,
                                                 boundaries=boundaries,
                                                 toolbar=True,
                                                 figsize=(5, 5))
        tkw.grid_configure(self.toplevel_frame_map_2)
        self._update_map_2(self.toplevel_map_widget_2)

        self.toplevel_frame_map_2.protocol('WM_DELETE_WINDOW', delete_map_2)

    def _get_map_boundaries(self):
        boundaries = [self.user.map_boundries.setdefault('lon_min', 9),
                      self.user.map_boundries.setdefault('lon_max', 31),
                      self.user.map_boundries.setdefault('lat_min', 53),
                      self.user.map_boundries.setdefault('lat_max', 66)]
        return boundaries

    #===========================================================================
    def _set_notebook_frame_depth_range(self):
        frame = self.notebook_options.frame_depth_range

        r=0

        #----------------------------------------------------------------------
        # z-axis options
        self.zrange_widget = gui.AxisSettingsFloatWidget(frame,
                                                         plot_object=self.plot_object,
                                                         callback=self._callback_zaxis_widgets,
                                                         label='depth range',
                                                         axis='z',
                                                         row=r,
                                                         pady=1,
                                                         sticky='nw')
        r+=1



        tkw.grid_configure(frame, nr_rows=2)


    #===========================================================================
    def _set_notebook_frame_select(self):
        frame = self.notebook_options.frame_select_data_to_flag

        r=0

        #----------------------------------------------------------------------
        # Range widget
        self.xrange_selection_widget = gui.RangeSelectorFloatWidget(frame,
                                                                    label='Value range',
                                                                    plot_object=self.plot_object,
                                                                    axis='x',
                                                                    row=r)
        r+=1

        self.zrange_selection_widget = gui.RangeSelectorFloatWidget(frame,
                                                                    label='Depth range',
                                                                    plot_object=self.plot_object,
                                                                    max_is_min=True,
                                                                    axis='z',
                                                                    row=r)
        tkw.grid_configure(frame, nr_rows=2)


    def _update_notebook_frame_flag(self):
        """
        Update flag widget. The apperance of flag widget will change depending on the loaded settings file
        :return:
        """
        if not self.gismo_sampling_type_settings:
            try:
                self.frame_flag_widget.destroy()
            except:
                pass
            file_id_list = self.select_data_widget.get_filtered_file_id_list()
            if not file_id_list:
                return
            gismo_object = self.session.get_gismo_object(file_id_list[0])
            self.gismo_sampling_type_settings = gismo_object.settings
            self._set_notebook_frame_flag()

    #===========================================================================
    def _set_notebook_frame_flag(self):
        self.frame_flag_widget = tk.Frame(self.notebook_options.frame_flag_selected_data)
        self.frame_flag_widget.grid(row=0, column=0, sticky='nsew')

        padx=5
        pady=5
        r=0
        c=0
        self.flag_widget = gui.get_flag_widget(parent=self.frame_flag_widget,
                                               settings_object=self.gismo_sampling_type_settings,
                                               user_object=self.parent_app.user,
                                               callback_flag_data=self._on_flag_widget_flag,
                                               callback_update=self._update_plot,
                                               callback_prop_change=self._on_flag_widget_change,
                                               include_marker_size=True,
                                               text=core.texts.flag_widget_help_text(),
                                               row=r,
                                               column=c,
                                               padx=padx,
                                               pady=pady,
                                               sticky='nw')

        tkw.grid_configure(self.frame_flag_widget)


    #===========================================================================
    def _set_notebook_frame_compare(self):
        frame = self.notebook_options.frame_compare
        grid_opt = {'padx': 5,
                    'pady': 5,
                    'sticky': 'nsew'}
        self.labelframe_reference = tk.LabelFrame(frame, text='Reference file')
        self.labelframe_reference.grid(row=0, column=0, **grid_opt)

        # ----------------------------------------------------------------------
        # Reference file
        pad = {'padx': 5,
               'pady': 5}
        prop_combobox = {'width': 60}
        self.select_ref_data_widget = tkw.ComboboxWidget(self.labelframe_reference,
                                                         title='',
                                                         prop_combobox=prop_combobox,
                                                         row=0,
                                                         pady=5,
                                                         sticky='w')

        self.button_load_current_sample = tk.Button(self.labelframe_reference,
                                                    text=u'Load/update reference file',
                                                    command=self._update_file_reference)
        self.button_load_current_sample.grid(row=0, column=1, sticky='w', **pad)

        file_frame = tk.Frame(self.labelframe_reference)
        file_frame.grid(row=1, column=0, columnspan=2, sticky='w', **pad)
        tk.Label(file_frame, text='Active file:').grid(row=0, column=0, sticky='w', **pad)
        self.stringvar_current_reference_file = tk.StringVar()
        tk.Label(file_frame,
                 textvariable=self.stringvar_current_reference_file,
                 bg=None).grid(row=0, column=1, columnspan=2, sticky='w', **pad)
        tkw.grid_configure(file_frame, nr_columns=2)
        tkw.grid_configure(self.labelframe_reference, nr_rows=2)

        self.compare_widget = gui.CompareWidget(frame,
                                                parent_app=self,
                                                session=self.parent_app.session,
                                                include_depth=False,
                                                row=1,
                                                **grid_opt)

        self.include_ref_data_widget = tkw.CheckbuttonWidgetSingle(frame,
                                                                   'Show reference data in profile plot',
                                                                   callback=self._on_toggle_ref_data,
                                                                   row=2, **grid_opt)

        tkw.grid_configure(frame, nr_rows=3)


        # button_frame = tk.Frame(frame)
        # button_frame.grid(row=2, column=0, sticky='nsew', **pad)
        #
        # # Button plot
        # self.button_compare_plot_in_timeseries = tk.Button(button_frame, text='Plot in time series',
        #                                               comman=lambda: self._compare_data_plot('in_timeseries'))
        # self.button_compare_plot_in_timeseries.grid(row=0, column=0, sticky='nsew', **pad)
        #
        # self.button_compare_plot_by_flags = tk.Button(button_frame, text='Plot correlation plot\n(color by flag)',
        #                                           comman=lambda: self._compare_data_plot('color_by_flag'))
        # self.button_compare_plot_by_flags.grid(row=0, column=1, sticky='nsew', **pad)
        #
        # self.button_compare_plot_by_depth = tk.Button(button_frame, text='Plot correlation plot\n(color by depth)',
        #                                               comman=lambda: self._compare_data_plot('color_by_depth'))
        # self.button_compare_plot_by_depth.grid(row=0, column=2, sticky='nsew', **pad)
        #
        # # Button save data
        # self.button_compare_save_data = tk.Button(button_frame, text='Save correlated dataset\n'
        #                                                              '(tab separated ascii file)',
        #                                           comman=self._compare_data_save_data)
        # self.button_compare_save_data.grid(row=0, column=3, sticky='nsew', **pad)
        #
        # self.save_correlation_directory_widget = tkw.DirectoryWidgetLabelframe(button_frame,
        #                                                                        label='Save directory',
        #                                                                        row=1, column=0, columnspan=3)
        # tkw.grid_configure(button_frame, nr_rows=2, nr_columns=4)
        #
        # default_directory = os.path.join(self.user_manager.get_app_settings('directory', 'export directory'),
        #                                  datetime.datetime.now().strftime('%Y%m%d'))
        # self.save_correlation_directory_widget.set_directory(default_directory)
        #
        #
        # tkw.grid_configure(frame, nr_rows=3)

    def _on_toggle_ref_data(self):
        add_ref_data = self.include_ref_data_widget.get_value()
        self.plot_object.delete_data('ref_data')
        if add_ref_data:
            self._add_ref_data_to_plot()

    def old_save_correlation_plot_html(self):
        if not gui.communicate.match_data(self, self.compare_widget):
            self.plot_object_compare.reset_plot()
            return
        match_object = self.session.get_match_object(self.current_file_id, self.current_ref_file_id)
        merge_df = self.session.get_merge_data(self.current_file_id, self.current_ref_file_id)
        compare_parameter = self.compare_widget.get_parameter()

        # Find parameter names in merge df
        current_par_file_id = '{}_{}'.format(self.current_parameter, self.current_file_id)
        compare_par_file_id = '{}_{}'.format(compare_parameter, self.current_ref_file_id)

        main_par = match_object.get_merge_parameter(current_par_file_id)
        comp_par = match_object.get_merge_parameter(compare_par_file_id)

        # Get list of active visit_depth_id
        visit_depth_id_par = '{}_{}'.format('visit_depth_id', self.current_file_id)
        visit_depth_id_list = merge_df[visit_depth_id_par]
        # Handle flaggs
        selection = self.flag_widget.get_selection()

        import sharkpylib.plot.html_plot as html_plot

        # Set title and labels
        data = self.current_gismo_object.get_data('time',
                                                  visit_depth_id_list=visit_depth_id_list)

        time_from = pd.to_datetime(str(min(data['time']))).strftime('%Y%m%d')
        time_to = pd.to_datetime(str(max(data['time']))).strftime('%Y%m%d')
        self.plot_object_compare.set_title('{} - {}'.format(time_from, time_to))
        self.plot_object_compare.set_x_label(current_par_file_id)
        self.plot_object_compare.set_y_label(compare_par_file_id)

        plot_object = html_plot.PlotlyPlot(title='{} - {}'.format(time_from, time_to),
                                           xaxis_title=current_par_file_id,
                                           yaxis_title=compare_par_file_id)

        all_values = []

        for flag in selection.selected_flags:
            # print('FLAG', flag)
            data = self.current_gismo_object.get_data('visit_depth_id', 'time', self.current_parameter, visit_depth_id_list=visit_depth_id_list,
                                                      mask_options=dict(include_flags=[flag]))
            print('len()', len(self.current_gismo_object.df))
            print('len(data)', data['visit_depth_id'])
            boolean = ~np.isnan(np.array(data[self.current_parameter]))
            visit_depth_id_flag = data['visit_depth_id'][boolean]

            boolean = merge_df[visit_depth_id_par].isin(visit_depth_id_flag)
            x = [float(item) if item else np.nan for item in merge_df.loc[boolean, main_par]]
            y = [float(item) if item else np.nan for item in merge_df.loc[boolean, comp_par]]

            prop = self.current_gismo_object.settings.get_flag_prop_dict(flag)
            prop.update(selection.get_prop(flag))  # Is empty if no settings file is added while loading data
            prop.update({'linestyle': '',
                         'marker': '.'})

            plot_object.add_scatter_data(x, y, name=str(flag), mode='markers')

            all_values.extend(x)
            all_values.extend(y)

            # print('LEN', len(all_values))

        min_value = np.nanmin(all_values)
        max_value = np.nanmax(all_values) * 1.05

        if min_value > 0:
            min_value = min_value * 0.95

        # Plot correlation line
        plot_object.add_scatter_data([min_value, max_value], [min_value, max_value], name='correlation_line', mode='lines')

        # Save plot
        current_par_name = current_par_file_id.replace('/', '_').replace('\\', '_')
        compare_par_name = compare_par_file_id.replace('/', '_').replace('\\', '_')
        plot_object.plot_to_file(os.path.join(self.save_plots_directory_widget.get_directory(),
                                              '{}_{}.html'.format(current_par_name, compare_par_name)))

    def old_compare_data_plot(self, *args):

        # Recreate plot object if
        self._set_notebook_compare_plot()

        selection = self.compare_widget.get_selection()
        load_match_data = False
        if selection != self.current_compare_selection:
            load_match_data = True
        try:
            self.current_merge_data = gui.communicate.get_merge_data(self,
                                                                                      self.compare_widget,
                                                                                      self.flag_widget,
                                                                                      load_match_data=load_match_data)
            self.current_gismo_match_object = self.session.get_match_object(self.current_file_id, self.current_ref_file_id)
            self.current_compare_selection = selection
        except GUIExceptionBreak:
            self._reset_merge_data()
            return


        # if selection != self.current_compare_selection:
        #     try:
        #         self.current_merge_data = gui.communicate.get_merge_data(self, self.compare_widget, self.flag_widget)
        #         self.current_gismo_match_object = self.session.get_match_object(self.current_file_id, self.current_ref_file_id)
        #         self.current_compare_selection = selection
        #     except GUIExceptionBreak:
        #         self._reset_merge_data()
        #         return

        if 'in_timeseries' in args:
            print('in_timeseries')
            gui.communicate.add_compare_to_timeseries_plot(plot_object=self.plot_object,
                                                                            session=self.session,
                                                                            file_id=self.current_file_id,
                                                                            ref_file_id=self.current_ref_file_id,
                                                                            help_info_function=self.parent_app.update_help_information,
                                                                            par=self.compare_widget.get_parameter(),
                                                                            user=self.user)
            self.plot_has_ref_data = True

        else:
            if self.plot_has_ref_data:
                self._update_plot()
                self.plot_has_ref_data = False
            # self.plot_object.delete_data(marker_id='ref_data') # Does not work...
            data = self.current_merge_data

            end_points = [data['min_value'], data['max_value']]
            # Plot correlation line
            self.plot_object_compare.set_data(end_points, end_points,
                                              line_id='correlation', marker='',
                                              color=self.user.plot_color.setdefault('correlation_line', 'red'))

            if 'color_by_depth' in args:
                xx = []
                yy = []
                cc = []
                for flag in sorted(data['flags']):
                    xx.extend(list(data['flags'][flag]['x']))
                    yy.extend(list(data['flags'][flag]['y']))
                    cc.extend(list(data['flags'][flag]['depth']))

                self.plot_object_compare.set_data(xx, yy, c=cc,
                                                  cmap='cmo.deep',
                                                  colorbar_title='Depth\n[m]')

                # self.plot_object_contour.add_legend(title='Depth [m]')

                self.current_correlation_plot = 'color_by_depth'
            elif 'color_by_flag' in args:
                for flag in sorted(data['flags']):
                    x = data['flags'][flag]['x']
                    y = data['flags'][flag]['y']
                    prop = data['flags'][flag]['prop']

                    self.plot_object_compare.set_data(x, y, line_id=flag, **prop)
                    self.current_correlation_plot = 'color_by_flag'

            self.plot_object_compare.set_x_limits(limits=end_points, call_targets=False)
            self.plot_object_compare.set_y_limits(limits=end_points, call_targets=True)

            # Set title and labels
            self.plot_object_compare.set_title('{} - {}'.format(data['time_from_str'], data['time_to_str']))
            self.plot_object_compare.set_x_label(data['main_par_file_id'])
            self.plot_object_compare.set_y_label(data['compare_par_file_id'])


    def old_compare_data_save_data(self):
        if not gui.communicate.match_data(self, self.compare_widget):
            return
        merge_df = self.session.get_merge_data(self.current_file_id, self.current_ref_file_id)
        directory = self.save_correlation_directory_widget.get_directory()
        if not directory:
            return
        if not os.path.exists(directory):
            os.makedirs(directory)

        file_path = os.path.join(directory, 'merge_data_{} - {}.txt'.format(self.current_file_id, self.current_ref_file_id))
        merge_df.to_csv(file_path, sep='\t', index=False)

    def _update_compare_widget(self):
        self.compare_widget.update_parameter_list(self.current_ref_file_id)

    def _add_ref_data_to_plot(self):
        logging.debug('page_fixed_platforms._callback_compare: Start')
        try:
            match_data = gui.add_compare_to_profile_plot(plot_object=self.plot_object,
                                                         session=self.session,
                                                         ref_file_id=self.current_ref_file_id,
                                                         file_id=self.current_file_id,
                                                         compare_widget=self.compare_widget,
                                                         help_info_function=self.parent_app.update_help_information,
                                                         user=self.user)

            self.map_widget_1.add_scatter(match_data['lat'], match_data['lat'], marker_id='match_data')
        except GISMOExceptionInvalidOption as e:
            main_gui.show_warning('Invalid option', e)

    def _set_notebook_frame_save_data(self):

        frame = self.notebook_options.frame_save_data
        # frame = self.notebook_options.frame_save

        self.save_file_widget = main_gui.SaveWidget(frame,
                                               label='Save file',
                                               callback=self._callback_save_file,
                                               user=self.user,
                                               sticky='nw')

        self.save_all_files_widget = main_gui.SaveWidget(frame,
                                                    label='Save all files (filtered)',
                                                    include_file_name=False,
                                                    callback=self._callback_save_all_files,
                                                    user=self.user,
                                                    sticky='nw',
                                                    row=1)

        tkw.grid_configure(frame, nr_rows=2)

    def old_set_notebook_frame_save_plots(self):

        def on_change_file_format():
            self.user.save.set('plot_file_format', self.combobox_widget_file_format.get_value())

        frame = self.notebook_options.frame_save_plots

        prop = {'padx': 5,
                'pady': 5,
                'sticky': 'nsew'}

        # Save directory
        self.save_plots_directory_widget = tkw.DirectoryWidgetLabelframe(frame,
                                                                       label='Save in directory',
                                                                       row=0, columnspan=2, **prop)
        default_directory = os.path.join(self.user_manager.get_app_settings('directory', 'export directory'),
                                         datetime.datetime.now().strftime('%Y%m%d'))
        self.save_plots_directory_widget.set_directory(default_directory)

        self.labelframe_save_plots_pic = ttk.LabelFrame(frame, text='Save plots')
        self.labelframe_save_plots_pic.grid(row=1, column=0, **prop)

        self.labelframe_save_plots_html = ttk.LabelFrame(frame, text='Save html')
        self.labelframe_save_plots_html.grid(row=1, column=1, **prop)

        tkw.grid_configure(frame, nr_rows=2, nr_columns=2)

        # --------------------------------------------------------------------------------------------------------------
        # Save pic
        pic_frame = self.labelframe_save_plots_pic
        self.combobox_widget_file_format = tkw.ComboboxWidget(pic_frame, title='File format', items=['png', 'pdf', 'ps', 'eps', 'svg'],
                                                              callback_target=on_change_file_format, row=0)
        self.combobox_widget_file_format.set_value(self.user.save.setdefault('plot_file_format', 'png'))

        # self.button_save_time_plot = tk.Button(pic_frame, text='Save time series plot',
        #                                        comman=self._save_time_plot)
        # self.button_save_time_plot.grid(row=1, column=0, **prop)
        #
        # self.button_save_correlation_plot = tk.Button(pic_frame, text='Save correlation plot',
        #                                               comman=self._save_correlation_plot)
        # self.button_save_correlation_plot.grid(row=2, column=0, **prop)

        tkw.grid_configure(pic_frame, nr_rows=3)

        # --------------------------------------------------------------------------------------------------------------
        # Save html
        html_frame = self.labelframe_save_plots_html
        self.button_save_correlation_plot_html = tk.Button(html_frame, text='Show and save correlation plots\nin HTML format',
                                                           comman=self._save_correlation_plot_html)
        self.button_save_correlation_plot_html.grid(row=0, column=0, **prop)

        tkw.grid_configure(html_frame, nr_rows=1)


        # Export html plot
        # self.save_widget_html = gui.SaveWidgetHTML(frame,
        #                                            label='Show and save time series plots in HTML format',
        #                                            callback=self._callback_save_html,
        #                                            default_directory=self.user_manager.get_app_settings('directory', 'export directory'),
        #                                            user=self.user,
        #                                            sticky='nw',
        #                                            row=2,
        #                                            columnspan=2)

        tkw.grid_configure(frame, nr_rows=3)

    def _callback_save_file(self, *args, **kwargs):
        gui.communicate.save_file(file_id=self.current_file_id,
                                  session=self.session,
                                  save_widget=self.save_file_widget,
                                  user=self.user.name)
        self.user.path.set('export_directory', self.save_file_widget.get_directory())

    def _callback_save_all_files(self, *args, **kwargs):
        file_id_list = self.select_data_widget.get_filtered_file_id_list()
        gui.communicate.save_files(file_id_list=file_id_list,
                                   session=self.session,
                                   save_widget=self.save_all_files_widget,
                                   user=self.user.name)

        self.user.path.set('export_directory', self.save_all_files_widget.get_directory())

    def old_callback_save_html(self):
        if self.save_widget_html.has_sufficient_selections():
            self.parent_app.run_progress(self._save_html, 'Saving plots...')
        else:
            gui.show_information('Missing selection', 'You did not provide enough information for plotting htlm plots.')

    def old_save_html(self):
        gui.communicate.save_html_plot(self, self.save_widget_html, flag_widget=self.flag_widget,
                                                        save_directory_widget=self.save_plots_directory_widget)

    def old_save_correlation_plot(self):
        file_format = self.combobox_widget_file_format.get_value()
        # self.current_correlation_plot = 'color_by_depth'
        in_file_name = 'correlation_{}_{}_{}_{}'.format(self.current_parameter, self.current_file_id,
                                                     self.current_ref_file_id, self.current_correlation_plot)
        gui.communicate.save_plot(self, self.plot_object_compare, self.save_plots_directory_widget,
                                                   file_format=file_format, in_file_name=in_file_name)

    def old_save_time_plot(self, *args, **kwargs):
        file_format = self.combobox_widget_file_format.get_value()
        in_file_name = 'time_series_{}_{}'.format(self.current_parameter, self.current_file_id)
        gui.communicate.save_plot(self, self.plot_object, self.save_plots_directory_widget,
                                                   file_format=file_format, in_file_name=in_file_name)

    def _sync_x_axis(self, source, call_targets=True):
        gui.communicate.sync_limits_in_plot_user_and_axis(plot_object=self.plot_object,
                                                                           user_object=self.user,
                                                                           axis_widget=self.xrange_widget,
                                                                           par=self.current_parameter,
                                                                           axis='x',
                                                                           call_targets=call_targets,
                                                                           source=source)

    def _sync_z_axis(self, source, call_targets=True):
        gui.communicate.sync_limits_in_plot_user_and_axis(plot_object=self.plot_object,
                                                                           user_object=self.user,
                                                                           axis_widget=self.zrange_widget,
                                                                           par='depth',
                                                                           axis='z',
                                                                           call_targets=call_targets,
                                                                           source=source)


    def _callback_zaxis_widgets(self):
        self._sync_z_axis('axis', call_targets=True)
        self._update_map_1()
        self._update_map_2()

    def _callback_xaxis_widgets(self):
        self._sync_x_axis('axis', call_targets=True)
        # self._update_map_1()
        self._update_map_2()

    def _callback_plot_range(self):
        if not self.plot_object.mark_range_orientation:
            return
        elif self.plot_object.mark_range_orientation == 'vertical':
            gui.update_range_selection_widget(plot_object=self.plot_object,
                                              range_selection_widget=self.zrange_selection_widget,
                                              time_axis=False)
        elif self.plot_object.mark_range_orientation == 'horizontal':
            gui.update_range_selection_widget(plot_object=self.plot_object,
                                              range_selection_widget=self.xrange_selection_widget,
                                              time_axis=False)

    def _update_parameter_list(self):
        exclude_parameters = ['time', 'lat', 'lon', 'depth']

        parameter_list = []
        for file_id in self.select_data_widget.get_filtered_file_id_list():
            parameter_list.extend(self.session.get_parameter_list(file_id))
        parameter_list = sorted(set(parameter_list))
        for par in exclude_parameters:
            parameter_list.pop(parameter_list.index(par))
        # Single (plot) parameter widget
        self.parameter_widget.update_items(parameter_list,
                                           default_item=self.user.parameter_priority.get_priority(parameter_list))

        self.current_parameter = self.parameter_widget.get_value()

        # self._update_export_parameter_list()

    def _update_export_parameter_list(self):
        # Parameters for exporting
        parameter_list = []
        if self.current_file_id:
            for par in self.session.get_parameter_list(self.current_file_id):
                if not par.strip():
                    continue
                parameter_list.append('{} (main)'.format(par))
        if self.current_ref_file_id:
            for par in self.session.get_parameter_list(self.current_file_id):
                if not par.strip():
                    continue
                parameter_list.append('{} (ref)'.format(par))
        self.save_widget_html.update_parameters(parameter_list)

    def _reset_widgets(self):
        # self.plot_object.reset_plot()
        # self.parameter_widget.update_items()

        self.xrange_widget.reset_widget()
        self.zrange_widget.reset_widget()
        self.xrange_selection_widget.reset_widget()
        self.zrange_selection_widget.reset_widget()

    def _on_select_parameter(self):
        # Reset plot
        # self.parent_app.update_help_information()
        # self.plot_object.reset_plot()

        self.old_parameter = self.current_parameter
        self.current_parameter = self.parameter_widget.get_value()

        if not self.current_parameter:
            return

        print('OLD', self.old_parameter)
        print('NEW', self.current_parameter)
        if self.current_parameter != self.old_parameter:
            self._update_plot_background()

            # Save parameter
            self.user.parameter_priority.set_priority(self.current_parameter)

        # First plot...
        self._update_plot(call_targets=False)
        self._on_toggle_ref_data()

        # ...then set full range in plot without updating (not calling to update the tk.canvas).
        if self.user.options.setdefault('zoom_to_data_on_parameter_update', True):
            self.plot_object.zoom_to_data(call_targets=False, x_limits=True)

        # Update limits in plot from user
        self._sync_x_axis('user', call_targets=False)
        self._sync_z_axis('plot', call_targets=True)

        self._update_map_2()

        # self.parent_app.update_help_information('Parameter updated', bg='green')

    def _check_loaded_data(self):
        """
        Checks loaded file and loded data. If both are loaded return True else show popup window and return False
        :return:
        """
        if not self.parent_app.get_loaded_files_list():
            main_gui.show_information('No data files loaded',
                                 'There are no data loaded. Start by selecting a file under "Get data file"')
            return False
        if not self.current_file_id:
            main_gui.show_information('No data file selected',
                                 'Select a file under "Select data file" and press "Update data file"')
            return False

        return True

    def _on_flag_widget_flag(self):
        if not self._check_loaded_data():
            return
        try:
            gui.flag_data_profile(flag_widget=self.flag_widget,
                                  file_id=self.current_file_id,
                                  session=self.session,
                                  plot_object=self.plot_object,
                                  par=self.current_parameter)
            self._update_plot_background(file_id=self.current_gismo_object.file_id)
            self._update_plot()
            self.xrange_selection_widget.clear_widget()
            self.zrange_selection_widget.clear_widget()
        except GUIExceptionNoRangeSelection:
            gui.show_information('Could not flag data',
                                 'You need to make a selection under tab "Select data to flag" before you can flag data')

    def _update_plot(self, **kwargs):
        """
        Called by the parameter widget to update plot.
        """
        if not self._check_loaded_data():
            return

        gui.update_profile_plot(gismo_object=self.current_gismo_object,
                                par=self.current_parameter,
                                plot_object=self.plot_object,
                                flag_widget=self.flag_widget,
                                help_info_function=self.main_app.update_help_information,
                                call_targets=kwargs.get('call_targets', True),
                                clear_plot=False)

        try:
            self.plot_object.set_title(self.current_gismo_object.get_station_name())
        except GISMOExceptionMethodNotImplemented:
            pass
        self.plot_has_ref_data = False

    def _update_contour_plot(self, **kwargs):
        contour_par = self.parameter_contour_plot_widget.get_value()
        if contour_par not in self.current_contour_parameters:
            gui.show_information('Could not plot contour for parameter "{}"'.format(contour_par))
            return
        par_list = self.current_contour_parameters[contour_par]

        z = []
        y = []
        for par in par_list:
            z.append(self.session.get_data(self.current_file_id, par)[par])
            y.append(float(re.findall('_\d*', par)[0].strip('_')))

        x = self.session.get_data(self.current_file_id, 'time')['time']
        self.plot_object_contour.set_data(x, y, z, contour_plot=True)

    def _on_flag_widget_change(self):
        logging.debug('page_fixed_platforms._on_flag_widget_change: Start')
        selection = self.flag_widget.get_selection()
        for k, flag in enumerate(selection.selected_flags):
            self.plot_object.set_prop(ax='first', line_id=flag, **selection.get_prop(flag))

        # Compare widget
        try:
            selection = self.flag_widget.get_selection()
            for k, flag in enumerate(selection.selected_flags):
                self.plot_object_compare.set_prop(ax='first', line_id=flag, **selection.get_prop(flag))
        except:
            pass
        gui.save_user_info_from_flag_widget(self.flag_widget, self.parent_app.user)
        logging.debug('page_fixed_platforms._on_flag_widget_change: End')

    def _get_file_id(self, string):
        """
        Returns file_id from a information string like Ferrybox CMEMS: <file_id>
        :param string:
        :return:
        """
        return string.split(':')[-1].strip()

    def _set_current_file(self):
        """
        Sets the current file information. file_id and file_path are set.
        Information taken from self.select_data_widget
        :return:
        """
        selected = self.select_data_widget.get_selected()
        if not selected:
            self._reset_file_id()
            return
        self.current_file_id = selected['File ID']
        self.current_sampling_type = ''
        self.current_file_path = self.session.get_file_path(self.current_file_id)
        self.current_gismo_object = self.session.get_gismo_object(self.current_file_id)

    def _set_current_reference_file(self):
        """
        Sets the current reference file information. file_id and file_path are set.
        Information taken from self.select_ref_data_widget
        :return:
        """
        ref_string = self.select_ref_data_widget.get_value().strip()
        if not ref_string:
            self._reset_ref_file_id()
            gui.show_information('No reference file selected', 'You have to select a file in the list.')
            return
        self.current_ref_sampling_type = self.select_ref_data_widget.get_value().split(':')[0].strip()
        self.current_ref_file_id = gui.get_file_id(self.select_ref_data_widget.get_value())
        self.current_ref_file_path = self.session.get_file_path(self.current_ref_file_id)
        self.current_ref_gismo_object = self.session.get_gismo_object(self.current_ref_file_id)

    def _reset_file_id(self):
        self.current_sampling_type = ''
        self.current_file_id = ''
        self.current_file_path = ''
        self.current_gismo_object = None

    def old_reset_ref_file_id(self):
        self.current_ref_sampling_type = ''
        self.current_ref_file_id = ''
        self.current_ref_file_path = ''
        self.current_ref_gismo_object = None

    def old_update_contour_parameters(self):
        """
        Creates the contour parameter list and updates the contour parameter widget.
        :return:
        """
        par_list = self.session.get_parameter_list(self.current_file_id)
        striped_pars = []
        nr_list = []
        print('='*50)
        for par in par_list:
            print(par, type(par))
            striped_pars.append(re.sub('_\d*', '', par))
            found = re.findall('_\d*', par)
            if found:
                nr_list.append(int(found[0].strip('_')))
            else:
                nr_list.append(0)

        par_list = np.array(par_list)
        striped_pars = np.array(striped_pars)
        nr_list = np.array(nr_list)

        self.current_contour_parameters = dict()
        for spar in set(striped_pars):
            if list(striped_pars).count(spar) > 1:
                boolean = striped_pars == spar
                par_dict = dict(zip(par_list[boolean], nr_list[boolean]))
                sorted_par_list = [item[0] for item in sorted(par_dict.items(), key=lambda kv: kv[1], reverse=True)]
                self.current_contour_parameters[spar] = sorted_par_list

        #     self.current_contour_parameters[par] = sorted_par_listself.current_contour_parameters = dict()
        # for par in set(striped_pars):
        #     if list(striped_pars).count(par) > 1:
        #         self.current_contour_parameters[par] = []
        #
        # for spar in self.current_contour_parameters:
        #     boolean = striped_pars == spar
        #     par_dict = dict(zip(striped_pars[boolean], nr_list[boolean]))
        #     sorted_par_list = [item[0] for item in sorted(par_dict.items(), key=lambda kv: kv[1], reverse=True)]
        #     self.current_contour_parameters[par] = sorted_par_list

        self.parameter_contour_plot_widget.update_items(sorted(self.current_contour_parameters))


    def _update_valid_time_range_in_time_axis(self):
        data_file_string = self.select_data_widget.get_selected_file_id()
        data_file_id = self._get_file_id(data_file_string)
        gui.set_valid_time_in_time_axis(gismo_object=self.current_gismo_object,
                                        time_axis_widget=self.xrange_widget)
        gui.set_valid_time_in_time_axis(gismo_object=self.current_gismo_object,
                                        time_axis_widget=self.xrange_selection_widget)

    def _update_frame_save_widgets(self):
        if not self.current_file_path:
            self.save_file_widget.set_file_path()
            self.save_plot_widget.set_file_path()
            return

        # Set file paths
        # TODO: Set directory
        self.save_file_widget.set_file_path(self.current_file_path)

    def _update_map_1(self, *args, **kwargs):
        title_position = [0.5, 1.1]
        if args:
            map_list = args
        else:
            map_list = [self.map_widget_1, self.toplevel_map_widget_1]

        for map_widget in map_list:
            if not map_widget:
                # print('NOT MAP_WIDGET 1')
                continue
            # print('RUNNING')
            map_widget.delete_all_markers()
            map_widget.delete_all_map_items()
            map_widget.set_title('', position=title_position)



            gui.plot_map_background_data(map_widget=map_widget,
                                         session=self.session,
                                         user=self.user,
                                         current_file_id=self.current_file_id)
            if not self.current_file_id:
                continue

            if 'fixed platforms' in self.current_sampling_type.lower():
                title = 'All loaded data\n(current platform data highlighted)'
                # Plot current file
                data = self.session.get_data(self.current_file_id, 'lat', 'lon', self.current_parameter)

                map_widget.add_markers(np.nanmean(data['lat']),
                                       np.nanmean(data['lon']),
                                       marker_id='all_pos',
                                       linestyle='None',
                                       marker='s',
                                       color=self.user.map_prop.setdefault('fixed_platform_color', 'green'),
                                       markersize=10,
                                       zorder=20)

                map_widget.set_title(title, position=title_position)
            elif 'ctd' in self.current_sampling_type.lower():
                title = 'All loaded data\n(current platform data highlighted)'
                # Plot current file
                data = self.session.get_data(self.current_file_id, 'lat', 'lon', self.current_parameter)

                map_widget.add_markers(np.nanmean(data['lat']),
                                       np.nanmean(data['lon']),
                                       marker_id='all_pos',
                                       linestyle='None',
                                       marker='d',
                                       color=self.user.map_prop.setdefault('ferrybox_ctd_color', 'blue'),
                                       markersize=10,
                                       zorder=21)

                map_widget.set_title(title, position=title_position)
            elif 'ferrybox' in self.current_sampling_type.lower():
                title = 'All loaded data\n(current ferrybox data highlighted)'
                # Whole track as base
                data = self.session.get_data(self.current_file_id, 'lat', 'lon')
                map_widget.add_markers(data['lat'], data['lon'],
                                    marker_id='track_base',
                                    color=self.user.map_prop.setdefault('ferrybox_track_color', 'blue'),
                                    marker='.',
                                    linestyle='')

                # Highlighted track
                time_limits = self.xrange_widget.get_limits()
                time_start, time_end = time_limits
                data = self.session.get_data(self.current_file_id, 'lat', 'lon',
                                             filter_options={'time_start': time_start,
                                                             'time_end': time_end})
                map_widget.add_markers(data['lat'], data['lon'],
                                    marker_id='track_highlighted',
                                    color=self.user.map_prop.setdefault('ferrybox_track_color_highlighted', 'red'),
                                    marker='.',
                                    linestyle='')

                map_widget.set_title(title, position=title_position)



    def _update_map_2(self, *args, **kwargs):
        title_position = [0.5, 1.05]
        if args:
            map_list = args
        else:
            map_list = [self.map_widget_2, self.toplevel_map_widget_2]

        for map_widget in map_list:
            if not map_widget:
                # print('NOT MAP_WIDGET 2')
                continue

            map_widget.delete_all_markers()
            map_widget.delete_all_map_items()
            map_widget.set_title('', position=title_position)

            if 'fixed platforms' in self.current_sampling_type.lower():
                pass
            elif 'ferrybox' in self.current_sampling_type.lower():
                selected_flags = self.flag_widget.get_selection().selected_flags

                time_limits = self.xrange_widget.get_limits()
                time_start, time_end = time_limits
                data = self.session.get_data(self.current_file_id, 'lat', 'lon', self.current_parameter,
                                             filter_options={'time_start': time_start,
                                                             'time_end': time_end},
                                             mask_options={'include_flags': selected_flags})

                cmap_string = self.user.parameter_colormap.get(self.current_parameter)
                cmap = self.colormaps.get(cmap_string)

                vmin, vmax = self.yrange_widget.get_limits()

                marker_name = map_widget.add_scatter(lat=data['lat'], lon=data['lon'],
                                                            values=data[self.current_parameter],
                                                            marker_size=self.user.map_prop.setdefault('ferrybox_track_width', 10),
                                                            color_map=cmap,
                                                            marker_type='o',
                                                            marker_id='track',
                                                            edge_color=None,
                                                            zorder=10, vmin=vmin, vmax=vmax)
                map_widget.add_colorbar(marker_name,
                                      title=self.session.get_unit(self.current_file_id, self.current_parameter),
                                      orientation='vertical',
                                      position=[0.93, 0.02, 0.05, 0.3],
                                      tick_side='left',
                                      format='%.1f')

                map_widget.set_title(self.current_parameter, position=title_position)



    #===========================================================================
    def _update_file_reference(self):
        logging.debug('page_fixed_platforms._update_file_reference: Start')

        self._set_current_reference_file()

        if not self.current_ref_file_id:
            self.stringvar_current_reference_file.set('')
            return

        if not self.current_ref_file_path:
            self.stringvar_current_reference_file.set('')
            return
        self.stringvar_current_reference_file.set(self.current_ref_file_path)

        self._update_compare_widget()

        logging.debug('page_fixed_platforms._update_file_reference: End')
        self.main_app.update_help_information('Reference file updated: {}'.format(self.current_ref_file_id), bg='green')

