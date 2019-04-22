from __future__ import print_function
import os
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from SpeakerRecognition import SpeakerTrainer
from record_sound import RecordAudio

class UserTrainingWindow(Gtk.Dialog):
    def __init__(self, parent, training_path = "SpeakerRecognition/trainingData"):
        Gtk.Dialog.__init__(self, "New User ", parent, 0,
                    (Gtk.STOCK_CLOSE, Gtk.ResponseType.CLOSE))

        self.count = 0 
        
        self.training_path = training_path
        self.output_file_prefix = None
        
        self.recording_thread = None
        self.box = self.get_content_area()
        
        #Setting up the self.grid in which the elements are to be positionned
        self.grid = Gtk.Grid()
        self.grid.set_column_spacing(3)
        self.grid.set_row_spacing(3)
        self.grid.set_column_homogeneous(True)
        self.grid.set_row_homogeneous(True)
        self.box.add(self.grid)
        
        self.user_name_hbox = Gtk.HBox(homogeneous=True, spacing=10)
        self.user_name_label = Gtk.Label("User Name")
        self.user_name_entry = Gtk.Entry()
        self.user_name_hbox.add(self.user_name_label)
        self.user_name_hbox.add(self.user_name_entry)
        
        self.record_button = Gtk.ToggleButton('Start Record')
        self.record_button.connect("toggled", self.on_record_toggled)
        
        self.train_button = Gtk.Button("Start Training")
        self.train_button.connect("clicked", self.on_train_button_clicked)
        
        self.info_label = Gtk.Label("Use Record button and read the text below or Read from anywhere else . \n Then Click Start Training button.")
        
        self.textview = Gtk.TextView()
        self.textbuffer = self.textview.get_buffer()
        self.textbuffer.set_text("Coming to terms with a hacking and data breach case,\n" + 
                                "Microsoft is reaching out to some users informing them\n" + 
                                " of an Outlook.com hack which exposed data sent over \n" + 
                                "emails to hackers who kept accessing their accounts \n" + 
                                "between January 1 to March 28. Founded in 1996, Outlook.com \n" + 
                                "is a web-based suite of webmail, contacts, \n" + 
                                "tasks, and calendaring services developed and\n" + 
                                " offered by Microsoft. \n " +
                                "Following are some common words used as commands - \n" + 
                                "Insert, Open, Close, Google, Search, Download, Play, Music")
        
        self.spinner = Gtk.Spinner()
        
        self.grid.attach(self.user_name_hbox, 0, 0, 4, 1)
        self.grid.attach(self.info_label, 0, 1, 4, 1)
        self.grid.attach(self.textview, 0, 2, 3, 4)
        self.grid.attach(self.spinner, 3, 2, 1, 1)
        self.grid.attach(self.train_button, 3, 5, 1, 1)
        self.grid.attach(self.record_button, 1, 6, 1, 1)
        
        self.show_all()
        
    def on_record_toggled(self, widget):        
        user = self.user_name_entry.get_text().strip()
        if widget.get_active():
            if user == '':
                widget.set_active(False)
                self.on_empty_string()
                return
            else:
                # to avoid editing while recording or training
                self.user_name_entry.set_editable(False)
                if self.output_file_prefix is None:
                    self.output_file_prefix = self.training_path + '/' + user  
            # Making folder for user if doesnot exist
            if not os.path.isdir(self.output_file_prefix):
                os.mkdir(self.output_file_prefix)
                with open("RegisteredSpeaker.txt", 'a') as fp:
                    fp.write("\n" + user)
                
            
            self.count = len([name for name in os.listdir(self.output_file_prefix)])
            # class for recording audio in different thread
            self.recording_thread = RecordAudio(output_file = self.output_file_prefix + '/' + str(self.count) + ".wav")
            # start recording thread
            self.recording_thread.start()
            widget.set_label('Stop Record')
        else:
            if user == '':
                return
            #stop recording thread
            self.recording_thread.recording = False
            self.count += 1
            widget.set_label('Start Record')
            self.recording_thread.join()
            
    def on_empty_string(self):
        dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.ERROR,
            Gtk.ButtonsType.CANCEL, "Blank Entries Found")
        dialog.format_secondary_text(
            "Entries for'User Name' cannot be empty")
        dialog.run()
        dialog.destroy()
        
    def on_train_button_clicked(self, widget):
        self.spinner.start()
        SpeakerTrainer(source = self.training_path, dest = "SpeakerRecognition/Speakers_models/")
        self.spinner.stop()

