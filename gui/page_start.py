#!/usr/bin/env python
# -*- coding:utf-8 -*-
#
# Copyright (c) 2018 SMHI, Swedish Meteorological and Hydrological Institute
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).

import tkinter as tk

from plugins.SHARKtools_qc_sensors import gui


"""
================================================================================
================================================================================
================================================================================
"""
class PageStart(tk.Frame):

    def __init__(self, parent, controller, **kwargs):
        tk.Frame.__init__(self, parent, **kwargs)
        # parent is the frame "container" in App. contoller is the App class
        self.parent = parent
        self.controller = controller

    def startup(self):
        padx = 10
        pady = 10
        font = 12
        #----------------------------------------------------------------------
        # Create frame grid 
        nr_rows = 4 
        nr_columns = 8
        self.frames = {} 
        self.texts = {}
        for r in range(nr_rows):
            for c in range(nr_columns): 
#                print('=', r, c)
                if r not in self.frames: 
                    self.frames[r] = {}
                    self.texts[r] = {}

                self.frames[r][c] = tk.Frame(self) 
                self.frames[r][c].grid(row=r, column=c, padx=padx, pady=pady, sticky='nsew')
                
        
        for r in range(nr_rows):
            for c in range(nr_columns):
                self.grid_rowconfigure(r, weight=1)
                self.grid_columnconfigure(c, weight=1)
        #----------------------------------------------------------------------
        
        # Buttons 
        self.button = {}

        self.button_texts = {'Ferrybox\nand\nfixed platforms': 'PageTimeSeries',
                             'CTD Profiles': 'PageProfile',
                             'Sampling Type Settings': 'PageSamplingTypeSettings'}
        self.button_colors = {'PageTimeSeries': 'sandybrown',
                              'PageProfile': 'lightblue',
                              'PageSamplingTypeSettings': 'green'}


        r=0
        c=0
        for text in sorted(self.button_texts):
            page = self.button_texts[text]

            # text = self.button_texts[page]
            color = self.button_colors[page]
            self.button[page] = tk.Button(self.frames[r][c],
                                 text=text,
                                 command=lambda x=page: self.controller.show_frame(x),
                                 font=font,
                                 bg=color)

            self.button[page].grid(row=0, column=0, padx=padx, pady=pady, sticky='nsew')
            self.frames[r][c].grid_rowconfigure(0, weight=1)
            self.frames[r][c].grid_columnconfigure(0, weight=1)
            c+=1
            if c >= nr_columns:
                c = 0
                r += 1


    #===========================================================================
    def update_page(self):
        pass