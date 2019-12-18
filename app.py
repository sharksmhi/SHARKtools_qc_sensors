# Copyright (c) 2018 SMHI, Swedish Meteorological and Hydrological Institute 
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).

# To use basemap you might need to install Microsoft Visual C++: https://visualstudio.microsoft.com/visual-cpp-build-tools/


import tkinter as tk 
from tkinter import ttk
from tkinter import filedialog


import os
import sys
import socket

import matplotlib.pyplot as plt

import gui as main_gui
from plugins.SHARKtools_qc_sensors import gui
import core
import sys

import sharkpylib as spl

from sharkpylib.gismo import GISMOsession


from sharkpylib import gismo
from sharkpylib import loglib
import sharkpylib.tklib.tkinter_widgets as tkw

from plugins.plugin_app import PluginApp

from sharkpylib.gismo.exceptions import *
from sharkpylib.file.file_handlers import SamplingTypeSettingsDirectory, MappingDirectory

import threading

ALL_PAGES = dict()
ALL_PAGES['PageStart'] = gui.PageStart
ALL_PAGES['PageTimeSeries'] = gui.PageTimeSeries
ALL_PAGES['PageMetadata'] = gui.PageMetadata
ALL_PAGES['PageProfile'] = gui.PageProfile
ALL_PAGES['PageSamplingTypeSettings'] = gui.PageSamplingTypeSettings
ALL_PAGES['PageUser'] = gui.PageUser

APP_TO_PAGE = dict()
for page_name, page in ALL_PAGES.items():
    APP_TO_PAGE[page] = page_name


class App(PluginApp):
    """
    This class contains the main window (page), "container", for 
    the GISMOtoolbox application.
    Additional pages in the application are stored under self.frames. 
    The container is the parent frame that is passed to other pages.
    self is also passed to the other pages objects and should there be given the name
    "self.main_app". 
    Toolboxsettings and logfile can be reached in all page objects by calling
    "self.main_app.settings" and "self.main_app.logfile" respectivly. 
    """
    
    #===========================================================================
    def __init__(self, parent, main_app, **kwargs):
        PluginApp.__init__(self, parent, main_app, **kwargs)
        # parent is the frame "container" in App. contoller is the App class
        self.parent = parent
        self.main_app = main_app
        self.version = '2019.01.1'
        # TODO: Move version to __version__
        self.info_popup = self.main_app.info_popup

        self.plugin_directory = os.path.dirname(os.path.abspath(__file__))
        self.root_directory = self.main_app.root_directory
        self.users_directory = self.main_app.users_directory
        self.log_directory = self.main_app.log_directory
        # self.mapping_files_directory = self.main_app.mapping_files_directory

    # def get_user_settings(self):
    #     return [('basic', 'test_setting')]

    def startup(self):
        """
        Updated 20181002
        """

        # TODO: Dynamically load the factories so that you can select another one at start up (or in a directory)
        self.sampling_types_factory = gismo.sampling_types.PluginFactory()
        self.qc_routines_factory = gismo.qc_routines.PluginFactory()

        # Setting upp GUI logger
        if not os.path.exists(self.log_directory):
            os.makedirs(self.log_directory)


        self.logger = loglib.get_logger(name='gismo_qc',
                                        logfiles=[dict(level='DEBUG',
                                                       file_path=os.path.join(self.log_directory,
                                                                              'gismo_qc_debug.log')),
                                                  dict(level='WARNING',
                                                       file_path=os.path.join(self.log_directory,
                                                                              'gismo_qc_warning.log')),
                                                  dict(level='ERROR',
                                                       file_path=os.path.join(self.log_directory,
                                                                              'gismo_qc_error.log'))
                                                  ])


        # Load paths
        # self.paths = core.Paths(self.plugin_directory)

        # Load settings files object
        # self.settings_files = core.SamplingTypeSettingsFiles(self.paths.directory_settings_files)
        self.settings_files = SamplingTypeSettingsDirectory()
        self.mapping_files = MappingDirectory()

        self.settings = self.main_app.settings

        self.user_manager = self.main_app.user_manager
        self.user = self.main_app.user

        self.session = spl.gismo.GISMOsession(root_directory=self.root_directory,
                                                users_directory=self.users_directory,
                                                log_directory=self.log_directory,
                                                # mapping_files_directory=self.paths.directory_mapping_files,
                                                # settings_files_directory=self.paths.directory_settings_files,
                                                user=self.user.name,
                                                sampling_types_factory=self.sampling_types_factory,
                                                qc_routines_factory=self.qc_routines_factory,
                                                save_pkl=False)

        # TODO: Add mapping directory?
        # TODO: Add settings directory?

        self.default_platform_settings = None

        self._create_titles()

        self.all_ok = True
        
        self.active_page = None
        self.previous_page = None
        self.admin_mode = False
        self.progress_running = False
        self.progress_running_toplevel = False

        self.latest_loaded_sampling_type = ''

        self._set_frame()


        self.startup_pages()
        
        
        # Show start page given in settings.ini
        self.page_history = ['PageUser']
        self.show_frame('PageStart')

    def update_page(self):
        self.user = self.user_manager.user
        plt.style.use(self.user.layout.setdefault('plotstyle', self.user.layout.setdefault('plotstyle',
                                                                                           self.settings['default'][
                                                                                               'plotstyle'])))
        self.update_all()

    #==========================================================================
    def _set_frame(self):
        self.frame_top = tk.Frame(self)
        self.frame_mid = tk.Frame(self)
        self.frame_bot = tk.Frame(self)

        
        # Grid
        self.frame_top.grid(row=0, column=0, sticky="nsew")
        self.frame_mid.grid(row=1, column=0, sticky="nsew")
        self.frame_bot.grid(row=2, column=0, sticky="nsew")
        
        # Gridconfigure 
        tkw.grid_configure(self, nr_rows=3, r0=100, r1=5, r2=1)
        
        #----------------------------------------------------------------------
        # Frame top
        # Create container in that will hold (show) all frames
        self.container = tk.Frame(self.frame_top)
        self.container = tk.Frame(self.frame_top)
        self.container.grid(row=0, column=0, sticky="nsew")
        tkw.grid_configure(self.frame_top)

        
        #----------------------------------------------------------------------
        # Frame mid
        self.frame_add = tk.LabelFrame(self.frame_mid)
        self.frame_loaded = tk.LabelFrame(self.frame_mid, text='Loaded files')
        
        # Grid
        self.frame_add.grid(row=0, column=0, sticky="nsew")
        self.frame_loaded.grid(row=0, column=1, sticky="nsew")
        
        # Gridconfigure 
        tkw.grid_configure(self.frame_mid, nr_columns=2)
        
        #----------------------------------------------------------------------
        # Frame bot
        self._set_frame_bot()
        
        self._set_frame_add_file()
        self._set_frame_loaded_files()

    def _set_frame_bot(self):
        self.frame_info = tk.Frame(self.frame_bot)
        self.frame_info.grid(row=0, column=0, sticky="nsew")

        # ttk.Separator(self.frame_bot, orient=tk.VERTICAL).grid(row=0, column=1, sticky='ns')

        self.frame_progress = tk.Frame(self.frame_bot)
        # self.frame_progress.grid(row=0, column=2, sticky="nsew")
        self.progress_widget = tkw.ProgressbarWidget(self.frame_progress, sticky='nsew')

        self.info_widget = tkw.LabelFrameLabel(self.frame_info, pack=False)

        tkw.grid_configure(self.frame_info)

        tkw.grid_configure(self.frame_bot)

    def run_progress(self, run_function, message=''):

        def run_thread():
            self.progress_widget.run_progress(run_function, message=message)

        if self.progress_running:
            gui.show_information('Progress is running', 'A progress is running, please wait until it is finished!')
            return
        self.progress_running = True
        # run_thread = lambda: self.progress_widget.run_progress(run_function, message=message)
        threading.Thread(target=run_thread).start()
        self.progress_running = False

    def run_progress_in_toplevel(self, run_function, message=''):
        """
        Rins progress in a toplevel window.
        :param run_function:
        :param message:
        :return:
        """
        def run_thread():
            self.frame_toplevel_progress = tk.Toplevel(self)
            self.progress_widget_toplevel = tkw.ProgressbarWidget(self.frame_toplevel_progress, sticky='nsew', in_rows=True)
            self.frame_toplevel_progress.update_idletasks()
            self.progress_widget_toplevel.update_idletasks()
            print('running')
            self.progress_widget.run_progress(run_function, message=message)
            self.frame_toplevel_progress.destroy()

        if self.progress_running_toplevel:
            gui.show_information('Progress is running', 'A progress is running, please wait until it is finished!')
            return
        self.progress_running = True
        # run_thread = lambda: self.progress_widget.run_progress(run_function, message=message)
        threading.Thread(target=run_thread).start()
        self.progress_running = False

    #===========================================================================
    def startup_pages(self):
        # Tuple that store all pages
        
        self.pages_started = dict()
        
        
        # Dictionary to store all frame classes
        self.frames = {}
        
        # Looping all pages to make them active. 
        for page_name, Page in ALL_PAGES.items():  # Capital P to emphasize class
            # Destroy old page if called as an update
            try:
                self.frames[page_name].destroy()
                print(Page, u'Destroyed')
            except:
                pass
            frame = Page(self.container, self)
            frame.grid(row=0, column=0, sticky="nsew")

            self.container.rowconfigure(0, weight=1)
            self.container.columnconfigure(0, weight=1) 
            
            self.frames[page_name] = frame
            
        self.activate_binding_keys()

    
    #===========================================================================
    def _set_load_frame(self):
        self._set_frame_add_file() 
        self._set_frame_loaded_files()
        
        
    #===========================================================================
    def _set_frame_add_file(self):
        """
        Created     20180821    by Magnus 
        """
        #----------------------------------------------------------------------
        # Three main frames 
        frame = self.frame_add
        frame_data = tk.LabelFrame(frame, text='Get data file')
        frame_settings = tk.LabelFrame(frame, text='Settings file')
        frame_sampling_type = tk.LabelFrame(frame, text='Sampling type')
        frame_platform_depth = tk.LabelFrame(frame, text='Platform depth')
        frame_load = tk.Frame(frame)
        
        # Grid 
        padx=5 
        pady=5
        frame_data.grid(row=0, column=0, columnspan=4, sticky='nsew', padx=padx, pady=pady)
        frame_settings.grid(row=1, column=0, sticky='nsew', padx=padx, pady=pady)
        frame_sampling_type.grid(row=1, column=1, sticky='nsew', padx=padx, pady=pady)
        frame_platform_depth.grid(row=1, column=2, sticky='nsew', padx=padx, pady=pady)
        frame_load.grid(row=1, column=3, sticky='nsew', padx=padx, pady=pady)

        # Gridconfigure 
        tkw.grid_configure(frame, nr_rows=2, nr_columns=4, r0=50)
        
        #----------------------------------------------------------------------
        # Data frame

        self.button_get_ferrybox_data_file = tk.Button(frame_data, text='Ferrybox CMEMS',
                                                       command=lambda: self._get_data_file_path('Ferrybox CMEMS'))
        self.button_get_fixed_platform_data_file = tk.Button(frame_data, text='Fixed platform CMEMS',
                                                             command=lambda: self._get_data_file_path('Fixed platforms CMEMS'))
        self.button_get_ctd_data_file = tk.Button(frame_data, text='DV CTD standard format',
                                                  command=lambda: self._get_data_file_paths('CTD DV'))
        self.button_get_ctd_nodc_data_file = tk.Button(frame_data, text='NODC CTD standard format',
                                                  command=lambda: self._get_data_file_paths('CTD NODC'))
        self.button_get_sampling_file = tk.Button(frame_data, text='SHARKweb bottle data',
                                                  command=lambda: self._get_data_file_path('PhysicalChemical SHARK'))

        # tkw.disable_widgets(self.button_get_ctd_data_file)
        
        self.stringvar_data_file = tk.StringVar()
        self.entry_data_file = tk.Entry(frame_data, textvariable=self.stringvar_data_file, state='disabled')

        # Grid 
        padx=5
        pady=5
        self.button_get_ferrybox_data_file.grid(row=0, column=0, padx=padx, pady=pady, sticky='nsew')
        self.button_get_fixed_platform_data_file.grid(row=0, column=1, padx=padx, pady=pady, sticky='nsew')
        self.button_get_ctd_data_file.grid(row=0, column=2, padx=padx, pady=pady, sticky='nsew')
        self.button_get_ctd_nodc_data_file.grid(row=0, column=3, padx=padx, pady=pady, sticky='nsew')
        self.button_get_sampling_file.grid(row=0, column=4, padx=padx, pady=pady, sticky='nsew')
        
        self.entry_data_file.grid(row=1, column=0, columnspan=5, padx=padx, pady=pady, sticky='nsew')

        # Grid configure
        tkw.grid_configure(frame_data, nr_rows=2, nr_columns=5)

        # Settings frame
        self.combobox_widget_settings_file = tkw.ComboboxWidget(frame_settings,
                                                                items=[],
                                                                title='',
                                                                callback_target=self._save_type_and_file,
                                                                prop_combobox={'width': 40},
                                                                column=0,
                                                                columnspan=1,
                                                                row=0,
                                                                sticky='nsew')
        self._update_settings_combobox_widget()

        self.button_import_settings_file = ttk.Button(frame_settings, text='Import settings file', command=self._import_settings_file)
        self.button_import_settings_file.grid(row=0, column=1, padx=padx, pady=pady, sticky='nsew')
        tkw.grid_configure(frame_settings, nr_rows=1, nr_columns=2)

        #----------------------------------------------------------------------
        # Sampling type frame
        self.combobox_widget_sampling_type = tkw.ComboboxWidget(frame_sampling_type, 
                                                                items=sorted(self.session.get_sampling_types()),
                                                                title='',
                                                                callback_target=self._save_type_and_file,
                                                                prop_combobox={'width': 30},
                                                                column=0, 
                                                                columnspan=1, 
                                                                row=0, 
                                                                sticky='nsew')

        # Platform depth frame
        self.entry_widget_platform_depth = tkw.EntryWidget(frame_platform_depth, entry_type='int',
                                                           prop_entry=dict(width=5), row=0, column=0,
                                                           padx=padx, pady=pady, sticky='nsew')
        self.entry_widget_platform_depth.disable_widget()
        tk.Label(frame_platform_depth, text='meters').grid(row=0, column=1, padx=padx, pady=pady, sticky='nsew')
        tkw.grid_configure(frame_platform_depth)

        # Gridconfigure
        tkw.grid_configure(frame_sampling_type)

        # Load file button
        self.button_load_file = tk.Button(frame_load, text='Load file', command=self._load_file, bg='lightgreen', font=(30))
        self.button_load_file.grid(row=0, column=0, padx=padx, pady=pady, sticky='nsew')
        self.button_load_file.configure(state='disabled')
        tkw.grid_configure(frame_load)

    def _update_settings_combobox_widget(self):
        self.combobox_widget_settings_file.update_items(self.settings_files.get_list())

    #===========================================================================
    def _set_frame_loaded_files(self):
        """
        Created     20180821
        """
        frame = self.frame_loaded

        prop_listbox = {'height': 4}
        self.listbox_widget_loaded_files = tkw.ListboxWidget(frame,
                                                             include_delete_button=False,
                                                             # include_delete_button='Remove source',
                                                             prop_listbox=prop_listbox,
                                                             callback_delete_button=self._delete_source,
                                                             padx=1,
                                                             pady=1)

        tkw.grid_configure(frame)


    def _delete_source(self, file_id, *args, **kwargs):
        file_id = file_id.split(':')[-1].strip()
        print('_delete_source'.upper(), file_id)
        self.session.remove_file(file_id)
        self.update_all()

    def _get_data_file_paths(self, sampling_type):

        open_directory = self.get_open_directory(sampling_type)
        file_paths = filedialog.askopenfilenames(initialdir=open_directory,
                                                 filetypes=[('GISMO-file ({})'.format(sampling_type), '*.txt')])

        if file_paths:
            self.set_open_directory(file_paths[0], sampling_type)
            old_sampling_type = self.combobox_widget_sampling_type.get_value()
            self.combobox_widget_sampling_type.set_value(sampling_type)
            file_path_list = []
            for file_path in file_paths:
                file_name = os.path.basename(file_path)
                if sampling_type == 'CTD DV' and not file_name.startswith('ctd_profile_'):
                    continue
                if sampling_type == 'CTD NODC' and not file_name.startswith('nodc_ctd_profile_'):
                    continue
                if not file_path_list:
                    file_path_list.append(file_path)
                else:
                    file_path_list.append(file_name)

            self.stringvar_data_file.set('; '.join(file_path_list))

            self._set_settings(sampling_type, file_paths[0])

    def _get_data_file_path(self, sampling_type):
        """
        Created     20180821
        """
        open_directory = self.get_open_directory(sampling_type)
        file_path = filedialog.askopenfilename(initialdir=open_directory,
                                               filetypes=[('GISMO-file ({})'.format(sampling_type), '*.txt')])

        if file_path:
            self.set_open_directory(file_path, sampling_type)
            old_sampling_type = self.combobox_widget_sampling_type.get_value() 
            self.combobox_widget_sampling_type.set_value(sampling_type)
            self.stringvar_data_file.set(file_path)

        self._set_settings(sampling_type, file_path)

    def _save_type_and_file(self):
        if not self.latest_loaded_sampling_type:
            return
        s_type = self.combobox_widget_sampling_type.get_value()
        if s_type:
            self.user.file_type.set(self.latest_loaded_sampling_type, 'sampling_type', s_type)

        s_file = self.combobox_widget_settings_file.get_value()
        if s_file:
            self.user.file_type.set(self.latest_loaded_sampling_type, 'settings_file', s_file)

    def _set_settings(self, sampling_type, file_path):
        if file_path:
            # Check settings file path
            # settings_file_path = self.combobox_widget_settings_file.get_value()
            # try:
            #     self.combobox_widget_settings_file.set_value(self.settings['directory']['Default {} settings'.format(sampling_type)])
            # except:
            #      pass

            # User settings
            # Sampling type
            self.latest_loaded_sampling_type = sampling_type
            s_type = self.user.file_type.setdefault(sampling_type, 'sampling_type', '')
            if s_type:
                self.combobox_widget_sampling_type.set_value(s_type)

            # Settings file
            s_file = self.user.file_type.setdefault(sampling_type, 'settings_file', '')
            if s_file:
                self.combobox_widget_settings_file.set_value(s_file)

            self.info_popup.show_information(core.texts.data_file_selected(username=self.user.name))

            if 'fixed platform' in sampling_type.lower():
                self.entry_widget_platform_depth.enable_widget()
                temp_file_id = os.path.basename(file_path)[:10]
                depth = self.user.sampling_depth.setdefault(temp_file_id, 1)
                self.entry_widget_platform_depth.set_value(depth)
            else:
                self.entry_widget_platform_depth.set_value('')
                self.entry_widget_platform_depth.disable_widget()

            self.button_load_file.configure(state='normal')
        else:
            self.button_load_file.configure(state='disabled')
            self.entry_widget_platform_depth.set_value('')
            self.entry_widget_platform_depth.disable_widget()
            
    #===========================================================================
    def _import_settings_file(self):

        open_directory = self.get_open_directory()
            
        file_path = filedialog.askopenfilename(initialdir=open_directory, 
                                                filetypes=[('GISMO Settings file','*.ini')])
        if not file_path:
            return
        self.set_open_directory(file_path)

        self.settings_files.import_file(file_path)
        self._update_settings_combobox_widget()

    def get_open_directory(self, suffix=None):
        if suffix:
            string = f'open_directory_{suffix.replace(" ", "_")}'
        else:
            string = 'open_directory'
        return self.user.path.setdefault(string, self.settings['directory']['Input directory'])

    def set_open_directory(self, directory, suffix=None):
        if os.path.isfile(directory):
            directory = os.path.dirname(directory)
        if suffix:
            string = f'open_directory_{suffix.replace(" ", "_")}'
        else:
            string = 'open_directory'
        self.user.path.set(string, directory)

    def _load_file(self):

        def load_file(data_file_path, **kwargs):
            self.update_help_information('')
            self.button_load_file.configure(state='disabled')

            settings_file = self.combobox_widget_settings_file.get_value()
            sampling_type = self.combobox_widget_sampling_type.get_value()

            self.session.load_file(sampling_type=sampling_type,
                                   data_file_path=data_file_path,
                                   settings_file=settings_file,
                                   # settings_file_path=settings_file_path,
                                   reload=False,
                                   root_directory=self.root_directory,
                                   **kwargs)

        self.reset_help_information()
        data_file_path = self.stringvar_data_file.get()
        settings_file = self.combobox_widget_settings_file.get_value()
        settings_file_path = self.settings_files.get_path(settings_file)

        # sampling_type = self.combobox_widget_sampling_type.get_value()
        
        if not all([data_file_path, settings_file_path]): 
            self.update_help_information('No file selected!', fg='red')
            return

        data_file_path = self.stringvar_data_file.get()
        if ';' in data_file_path:
            data_file_list = []
            for k, file_name in enumerate(data_file_path.split(';')):
                file_name = file_name.strip()
                if k == 0:
                    directory = os.path.dirname(file_name)
                    data_file_list.append(file_name)
                else:
                    data_file_list.append(os.path.join(directory, file_name))
        else:
            data_file_list = [data_file_path]

        for file_path in data_file_list:
            # Load file
            try:
                load_file(file_path)
                # self.run_progress(load_file, message='Loading file...please wait...')
            except GISMOExceptionMissingPath as e:
                main_gui.show_information('Invalid path',
                                     'The path "{}" given in i settings file "{} can not be found'.format(e.message,
                                                                                                          settings_file_path))
                self.update_help_information('Please try again with a different settings file.')

            except GISMOExceptionMissingInputArgument as e:
                # print(e.message, '#{}#'.format(e.message), type(e.message))
                if 'depth' in e.message:
                    platform_depth = self.entry_widget_platform_depth.get_value()
                    if not platform_depth:
                        main_gui.show_information('No depth found!',
                                                  'You need to provide platform depth for this sampling type!')
                        return
                    load_file(file_path, depth=platform_depth)
            except GISMOExceptionInvalidParameter as e:
                main_gui.show_information('Invalid parameter',
                                          f'Could not find parameter {e}. Settings file might have wrong information.')
                return
            except GISMOExceptionQCfieldError:
                main_gui.show_error('QC field error',
                                          f'Something is wrong with the qf columns in file: {file_path}')
                return
            except Exception as e:
                main_gui.show_internal_error(e)
                return


        # Remove data file text
        self.stringvar_data_file.set('')

        self._update_loaded_files_widget()
        self.update_all()
        self.button_load_file.configure(state='normal')

        self.update_help_information('File loaded! Please continue.', bg='green')

    def _update_loaded_files_widget(self):
        loaded_files = [] 
        for sampling_type in self.session.get_sampling_types():
            for file_id in self.session.get_file_id_list(sampling_type):
                loaded_files.append('{}: {}'.format(sampling_type, file_id))
        self.listbox_widget_loaded_files.update_items(loaded_files)


    def get_loaded_files_list(self):
        """
        Returns a list with the items in self.listbox_widget_loaded_files
        :return:
        """
        return self.listbox_widget_loaded_files.items[:]

    #===========================================================================
    def _quick_run_F1(self, event):
        try:
            self.show_frame(gui.PageCTD)
        except:
            pass
            
    #===========================================================================
    def _quick_run_F2(self, event):
        pass
            
    #===========================================================================
    def _quick_run_F3(self, event):
        pass
    
    #===========================================================================
    def activate_binding_keys(self):
        """
        Load binding keys
        """
        self.bind("<Home>", lambda event: self.show_frame(gui.PageStart))
        self.bind("<Escape>", lambda event: self.show_frame(gui.PageStart))
        
        self.bind("<F1>", self._quick_run_F1)
        self.bind("<F2>", self._quick_run_F2)
        self.bind("<F3>", self._quick_run_F3)
        
        # Pages
        self.bind("<Control-f>", lambda event: self.show_frame(gui.PageFerrybox))
        self.bind("<Control-b>", lambda event: self.show_frame(gui.PageFixedPlatforms))

    def add_working_indicator(self):
        pass
#         self.update_help_information(u'Loading...')
#         self.working_indicator = tk.Label(self, text=u'Loading...', 
#                                           fg=u'red', 
#                                           font=("Helvetica", 16, u'italic'))
#         self.working_indicator.grid(row=0, column=0)

    def delete_working_indicator(self): 
        pass
#         self.update_help_information(None)
#         self.working_indicator.destroy()

    def update_files_information(self):
        """
        Updates the file information window (at the bottom left of the screen). 
        """
        self.loaded_files_combobox_widget.update_items(sorted(core.Boxen().loaded_ferrybox_files))
        self.loaded_files_combobox_widget_sample.update_items(sorted(core.Boxen().loaded_sample_files))

    def update_help_information(self, text='', **kwargs):
        """
        Created     20180822
        """
        kw = dict(bg=self.cget('bg'),
                  fg='black')
        kw.update(kwargs)
        self.info_widget.set_text(text, **kw)
        self.logger.debug(text)

    def reset_help_information(self):
        """
        Created     20180822
        """ 
        self.info_widget.reset()

    def update_all(self):
        
        for page_name, frame in self.frames.items():
            if self.pages_started.get(page_name):
                # print('page_name', page_name)
                frame.update_page()

    #===========================================================================
    def show_frame(self, page_name):
        """
        This method brings the given Page to the top of the GUI. 
        Before "raise" call frame startup method. 
        This is so that the Page only loads ones.
        """

        load_page = True
        frame = self.frames[page_name]

        if not self.pages_started.get(page_name, None):
            frame.startup()
            self.pages_started[page_name] = True

        #-----------------------------------------------------------------------
        if load_page:
            frame.tkraise()
            self.previous_page = self.active_page
            self.active_page = page
            # Check page history
            if page in self.page_history:
                self.page_history.pop()
                self.page_history.append(page)

        self.update_page()


    def _show_frame(self, page):
        self.withdraw()
        # self._show_frame(page)
        self.run_progress_in_toplevel(lambda x=page: self._show_frame(x), 'Opening page, please wait...')
        self.deiconify()

#     def show_frame(self, page):
#         """
#         This method brings the given Page to the top of the GUI.
#         Before "raise" call frame startup method.
#         This is so that the Page only loads ones.
#         """
# #         if page == PageAdmin and not self.admin_mode:
# #             page = PagePassword
#
#         load_page = True
#         frame = self.frames[page]
#
#         self.withdraw()
#         title = self._get_title(page)
#         if not self.pages_started[page]:
#             frame.startup()
#             self.pages_started[page] = True
#
#
#         frame.update_page()
# #             try:
# #                 frame.update()
# #             except:
# #                 Log().information(u'%s: Could not update page.' % title)
#
#         #-----------------------------------------------------------------------
#         if load_page:
#             frame.tkraise()
#             tk.Tk.wm_title(self, u'GISMO Toolbox: %s' % title)
#             self.previous_page = self.active_page
#             self.active_page = page
#
#             # Check page history
#             if page in self.page_history:
#                 self.page_history.pop()
#                 self.page_history.append(page)
#
#
#         try:
#             if self.active_page == gui.PageCTD:
#                 self.notebook_load.select_frame('CTD files')
#
#         except:
#             pass
#
#         self.update()
#         self.deiconify()

    #===========================================================================
    def goto_previous_page(self, event):
        self.page_history
        if self.previous_page:
            self.show_frame(self.previous_page) 
        
    #===========================================================================
    def previous_page(self, event):
        
        self.page_history.index(self.active_page)
        
    
    #===========================================================================
    def update_app(self):
        """
        Updates all information about loaded series. 
        """
        
        self.update_all()
    

        
        
    #===========================================================================
    def quit_toolbox(self):
        
        if self.settings.settings_are_modified:
            save_settings = tkMessageBox.askyesnocancel(u'Save core.Settings?', 
                                  u"""
                                  You have made one or more changes to the 
                                  toolbox settings during this session.
                                  Do you want to change these changes permanent?
                                  """)
            if save_settings==True:
                self.settings.save_settings()
                self.settings.settings_are_modified = False
            else:
                return
        
        self.destroy()  # Closes window
        self.quit()     # Terminates program
        
    #===========================================================================
    def _get_title(self, page):
        if page in self.titles:
            return self.titles[page]
        else:
            return ''
    
    #===========================================================================
    def _create_titles(self):
        self.titles = {}
        
        try:
            self.titles[gui.PageFerrybox] = 'Ferrybox'
        except:
            pass
        
        try:
            self.titles[gui.PageFixedPlatforms] = 'Buoy'
        except:
            pass
        
        try:
            self.titles[gui.PageProfile] = 'Profiles'
        except:
            pass

        try:
            self.titles[gui.PageTimeSeries] = 'Time Series'
        except:
            pass













