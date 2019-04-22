from __future__ import print_function
import wave
import struct
import math
import pyaudio, time
import numpy as np
import sys, threading
from scipy import signal, stats
import ConfigParser
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject
        
class PreferencesWindow(Gtk.Dialog):
    def __init__(self, parent, config_file = "Config/vad.cfg"):
        Gtk.Dialog.__init__(self, "My Preferences", parent, 0,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_OK, Gtk.ResponseType.OK))

        self.vad_out_file = "temp/vad_out" 
        self.config = ConfigParser.RawConfigParser()
        self.config_file = config_file
        self.vad_config = {}
        self.read_config()
        self.vad_pass = False
        self.set_keep_above(True)
        self.set_border_width(10)
        
        self.set_default_size(150, 100)
        self.box = self.get_content_area()
        #Setting up the self.grid in which the elements are to be positionned
        self.grid = Gtk.Grid()
        self.grid.set_column_homogeneous(True)
        self.grid.set_row_homogeneous(True)
        self.box.add(self.grid)
        
        # add Energy Threshold
        self.energy_hbox = Gtk.HBox(homogeneous=True, spacing=10)
        self.energy_label = Gtk.Label("Energy Threshhold")
        self.energy_adj = Gtk.Adjustment(self.vad_config['Energy_PrimThresh'], 0.0, 999999.0, 0.1, 0.1, 0.0)
        self.energy_entry = Gtk.SpinButton.new(self.energy_adj, 0.001, 1);
        self.energy_hbox.add(self.energy_label)
        self.energy_hbox.add(self.energy_entry)
        
        # add Spectal Flatness Threshold
        self.SF_hbox = Gtk.HBox(homogeneous=True, spacing=10)
        self.SF_label = Gtk.Label("Spectral Flatness Threshhold")
        self.SF_adj = Gtk.Adjustment(self.vad_config['SF_PrimThresh'], 0.0, 999999.0, 0.1, 0.1, 0.0)
        self.SF_entry = Gtk.SpinButton.new(self.SF_adj, 0.001, 1);
        self.SF_hbox.add(self.SF_label)
        self.SF_hbox.add(self.SF_entry)
        
         # add Frequency Threshold
        self.F_hbox = Gtk.HBox(homogeneous=True, spacing=10)
        self.F_label = Gtk.Label("Frequency Threshhold")
        self.F_adj = Gtk.Adjustment(self.vad_config['F_PrimThresh'], 0.0, 999999.0, 0.1, 0.1, 0.0)
        self.F_entry = Gtk.SpinButton.new(self.F_adj, 0.001, 1);
        self.F_hbox.add(self.F_label)
        self.F_hbox.add(self.F_entry)
        
        # adds buttons
        self.reset_button = Gtk.Button("Reset Default")
        self.reset_button.connect("clicked", self.on_reset_clicked)
        
        self.ok_button = self.get_widget_for_response (Gtk.ResponseType.OK)
        self.ok_button.connect("clicked", self.on_ok_clicked)
        
        # indicator for VAD
        self.vad_indicator = Gtk.DrawingArea()
        self.vad_indicator.connect("draw", self.expose) #queue_draw()
        #self.connect("redraw-signal", self.redraw)
        
        self.grid.attach(self.energy_hbox, 0, 0, 6, 1)
        self.grid.attach(self.SF_hbox, 0, 1, 6, 1)
        self.grid.attach(self.F_hbox, 0, 2, 6, 1)
        self.grid.attach(self.vad_indicator, 7, 0, 1, 2)
        
        action_area = self.get_action_area()
        action_area.add(self.reset_button)
        action_area.reorder_child(self.reset_button, Gtk.PackType.START)
        
        self.source_id = GObject.timeout_add(1000, self.redraw)
        self.show_all()
        
    def on_ok_clicked(self, widget):
        self.set_config()
    
    def on_reset_clicked(self, widget):
        self.energy_adj.set_value(self.config.getfloat('DEFAULTPARMS', 'Energy_PrimThresh'))
        self.F_adj.set_value(self.config.getfloat('DEFAULTPARMS', 'F_PrimThresh'))
        self.SF_adj.set_value(self.config.getfloat('DEFAULTPARMS', 'SF_PrimThresh'))
        print ("reset clicked")
        
    def read_config(self):
        self.config.read(self.config_file)
        self.vad_config['Energy_PrimThresh'] = self.config.getfloat('VAD', 'Energy_PrimThresh')
        self.vad_config['F_PrimThresh'] = self.config.getfloat('VAD', 'F_PrimThresh')
        self.vad_config['SF_PrimThresh'] = self.config.getfloat('VAD', 'SF_PrimThresh')
        self.vad_config['Min_Silence'] = self.config.getfloat('VAD', 'Min_Silence')
        self.vad_config['Min_Speech'] = self.config.getfloat('VAD', 'Min_Speech')
    
    def set_config(self):
        E_thres = self.energy_adj.get_value()
        self.config.set('VAD', 'Energy_PrimThresh', str(E_thres))
        F_thres = self.F_adj.get_value()
        self.config.set('VAD', 'F_PrimThresh', str(F_thres))
        SF_thres = self.SF_adj.get_value()
        self.config.set('VAD', 'SF_PrimThresh', str(SF_thres))
        with open(self.config_file, 'wb') as configfile:
            self.config.write(configfile)
        
    
    def expose(self, widget, cr):
        width = widget.get_allocated_width()
        height = widget.get_allocated_height()
        radius = min(height, width) / 2
        cr.arc(width / 2, height / 2, radius, 0, 2*math.pi)
        if self.vad_pass:
            cr.set_source_rgb(0,1,0)
        else:
            cr.set_source_rgb(1,0,0)
        cr.fill()
    def redraw(self, wid = None):
        with open(self.vad_out_file, 'r') as fp:
            if fp.read().strip() == '1':
                self.vad_pass = True
            else:
                self.vad_pass = False
        self.vad_indicator.queue_draw()
        return True

if __name__ == '__main__':       
    #main_win = MainWindow()
    child_win = PreferencesWindow()
    #main_win.show_all()
    child_win.connect("delete-event", Gtk.main_quit)
    child_win.show_all()
    Gtk.main()
