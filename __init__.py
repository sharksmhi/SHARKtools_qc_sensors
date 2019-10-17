# Copyright (c) 2018 SMHI, Swedish Meteorological and Hydrological Institute
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).

from . import gui
from .app import App


INFO = dict(title='Sensor data QC',
            sub_pages=[dict(name='PageStart',
                            title='Start'),
                       dict(name='PageTimeSeries',
                            title='Time series'),
                       dict(name='PageProfile',
                            title='Profile'),
                       dict(name='PageMetadata',
                            title='Metadata')
                       ],
            user_page_class='PageUser')  # Must match name in ALL_PAGES in main app


USER_SETTINGS = [('basic', 'filter'),
                 ('basic', 'flag_color'),
                 ('basic', 'flag_markersize'),
                 ('basic', 'focus'),
                 ('basic', 'layout'),
                 ('basic', 'match'),
                 ('basic', 'map_boundries'),
                 ('basic', 'map_prop'),
                 ('basic', 'options'),
                 ('basic', 'parameter_colormap'),
                 ('prioritylist', 'parameter_priority'),
                 ('basic', 'path'),
                 ('basic', 'plot_color'),
                 ('basic', 'plot_time_series_ref'),
                 ('basic', 'process'),
                 ('parameter', 'qc_routine_options'),
                 ('parameter', 'range'),
                 ('basic', 'sampling_depth'),
                 ('basic', 'save'),
                 ('basic', 'settingsfile')]

