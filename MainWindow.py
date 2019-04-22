from __future__ import print_function
import os
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
import subprocess
import json
from PreferencesWindow import PreferencesWindow
from NewUserWindow import UserTrainingWindow
from record_sound import RecordAudio
from SpeechRecognition import SpeechRecognizer

class NewCommandWindow(Gtk.Dialog):
    def __init__(self, parent, command = None, registered_speaker_file = "RegisteredSpeaker.txt"):
        Gtk.Dialog.__init__(self, "New Command", parent, 0,
                        (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                         Gtk.STOCK_OK, Gtk.ResponseType.OK))

        self.parent = parent
        self.command = command
        
        self.box = self.get_content_area()
        self.box.set_spacing(5)

        self.users_hbox = Gtk.HBox(homogeneous=True, spacing=10)
        self.users_label = Gtk.Label("User")
        
        default_user_index = 0
        # setting up combobox for users 
        self.user_store = Gtk.ListStore(str)
        with open(registered_speaker_file, 'r') as fp:
            count = 0
            for user in fp:
                if command is not None:
                    if user.strip() == command[2]:
                        default_user_index += count
                        print ("deafault found")
                    count += 1
                self.user_store.append([user.strip()])
        self.user_combo = Gtk.ComboBox.new_with_model(self.user_store)
        cell = Gtk.CellRendererText()
        self.user_combo.pack_start(cell, True)
        self.user_combo.add_attribute(cell, 'text', 0)
        self.user_combo.set_active(default_user_index)
        
        self.users_hbox.add(self.users_label)
        self.users_hbox.add(self.user_combo)
        
        #Setting up the self.grid in which the elements are to be positionned
        self.grid = Gtk.Grid()
        self.grid.set_column_spacing(3)
        self.grid.set_row_spacing(3)
        self.grid.set_column_homogeneous(True)
        self.grid.set_row_homogeneous(True)
        self.box.add(self.grid)
        
        self.voice_command_hbox = Gtk.HBox(homogeneous=True, spacing=10)
        self.voice_command_label = Gtk.Label("Voice Command")
        self.voice_command_entry = Gtk.Entry()
        if command is not None:
            self.voice_command_entry.set_text(command[0])
        self.voice_command_hbox.add(self.voice_command_label)
        self.voice_command_hbox.add(self.voice_command_entry)
        
        self.voice_run_command_hbox = Gtk.HBox(homogeneous=True, spacing=10)
        self.voice_run_command_label = Gtk.Label("Command to Run")
        self.voice_run_command_entry = Gtk.Entry()
        if command is not None:
            self.voice_run_command_entry.set_text(command[1])
        self.voice_run_command_hbox.add(self.voice_run_command_label)
        self.voice_run_command_hbox.add(self.voice_run_command_entry)
        
        self.ok_button = self.get_widget_for_response (Gtk.ResponseType.OK)
        self.ok_button.connect("clicked", self.on_ok_clicked)
        
        self.grid.attach(self.voice_command_hbox, 1, 1, 4, 1)
        self.grid.attach(self.voice_run_command_hbox, 1, 2, 4, 1)
        self.grid.attach(self.users_hbox, 1, 3, 4, 1)
        self.show_all()
        
    def on_ok_clicked(self, widget):
        tree_iter = self.user_combo.get_active_iter()
        if tree_iter is not None:
            model = self.user_combo.get_model()
            user = model[tree_iter][0]
        command_to_run = self.voice_run_command_entry.get_text().strip()
        command_name = self.voice_command_entry.get_text().strip()
        
        if command_name == '' or command_to_run == '':
            self.on_empty_string()
        else:
            if self.command is None:
                self.parent.command_liststore.append([command_name, command_to_run, user])
            else: # updateing
                del self.parent.command_list[self.command[0].replace(' ', '_')]
                self.parent.command_liststore[self.parent.selected_treeiter][0] = command_name
                self.parent.command_liststore[self.parent.selected_treeiter][1] = command_to_run
                self.parent.command_liststore[self.parent.selected_treeiter][2] = user
            # creating new command
            command_name = command_name.replace(' ', '_')
            
            self.parent.command_list[command_name] = {}
            self.parent.command_list[command_name]["Command to run"] = command_to_run
            self.parent.command_list[command_name]["User"] = user
            
    def on_empty_string(self):
        dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.ERROR,
            Gtk.ButtonsType.CANCEL, "Blank Entries Found")
        dialog.format_secondary_text(
            "Entries for'Command to run' and 'Voice Command' cannot be empty and are discarded")
        dialog.run()
        dialog.destroy()
        
class TrainingWindow(Gtk.Dialog):
    def __init__(self, parent, command_name, training_path = "SpeechRecognition/TrainingData"):
        Gtk.Dialog.__init__(self, "Training Commands - " + command_name, parent, 0,
                    (Gtk.STOCK_CLOSE, Gtk.ResponseType.CLOSE))

        self.command_name = command_name.strip().replace(' ', '_')
        self.training_path = training_path + '/' + self.command_name
        if not os.path.isdir(self.training_path):
            os.mkdir(self.training_path)

        self.count = len([name for name in os.listdir(self.training_path)])
        
        self.output_file_prefix = self.training_path + '/' + self.command_name + "_"
        
        self.recording_thread = None
        self.box = self.get_content_area()
        
        #Setting up the self.grid in which the elements are to be positionned
        self.grid = Gtk.Grid()
        self.grid.set_column_spacing(3)
        self.grid.set_row_spacing(3)
        self.grid.set_column_homogeneous(True)
        self.grid.set_row_homogeneous(True)
        self.box.add(self.grid)
        
        self.command_label = Gtk.Label("Command Name : " + command_name)
        self.training_count_label = Gtk.Label("Number of Training Samples : " + str(self.count))
        
        self.record_button = Gtk.ToggleButton('Start Record')
        self.record_button.connect("toggled", self.on_record_toggled)
        
        self.train_button = Gtk.Button("Start Training")
        self.train_button.connect("clicked", self.on_train_button_clicked)
        
        self.grid.attach(self.command_label, 0, 0, 3, 1)
        self.grid.attach(self.training_count_label, 0, 1, 3, 1)        
        self.grid.attach(self.record_button, 1, 3, 1, 1)
        
        action_area = self.get_action_area()
        print (action_area)
        action_area.add(self.train_button)
        action_area.reorder_child(self.train_button, Gtk.PackType.START)
        self.show_all()
        
    def on_record_toggled(self, widget):
        if widget.get_active():
            # class for recording audio in different thread
            self.recording_thread = RecordAudio(output_file = self.output_file_prefix + str(self.count) + ".wav")
            # start recording thread
            self.recording_thread.start()
            widget.set_label('Stop Record')
        else:
            #stop recording thread
            self.recording_thread.recording = False
            self.count += 1
            widget.set_label('Start Record')
            self.recording_thread.join()
            self.training_count_label.set_label("Number of Training Samples : " + str(self.count))
        
    def on_train_button_clicked(self, widget): 
        speech_trainer = SpeechRecognizer()
        with open("SpeechTraining.txt", 'w') as fp:
            fp.write(self.command_name)
        speech_trainer.train_hmm(source = "SpeechRecognition/TrainingData/", 
                                dest = "SpeechRecognition/Speech_Models/", 
                                train_file = "SpeechTraining.txt")
        
class MainWindow(Gtk.Window):

    def __init__(self, commands_file, speech_train_path):
        Gtk.Window.__init__(self, title="Secure Voice Controller")
        self.set_border_width(10)
        self.command_list = json.load( open(commands_file) )
        
        self.commands_file = commands_file
        self.speech_train_path = speech_train_path
        
        #Setting up the self.grid in which the elements are to be positioned
        self.grid = Gtk.Grid()
        self.grid.set_column_homogeneous(True)
        self.grid.set_row_homogeneous(True)
        self.grid.set_row_spacing(20)
        self.add(self.grid)

        #Creating the ListStore model
        self.command_liststore = Gtk.ListStore(str, str, str)
        for command_name in self.command_list:
            self.command_liststore.append(list((command_name.replace('_', ' '), 
                                                self.command_list[command_name]["Command to run"],
                                                self.command_list[command_name]["User"])))

        # Selecting first entry of the list as selected
        self.selected_command = None
        self.selected_treeiter = self.command_liststore.get_iter(0)
        if self.selected_command is None:
            self.selected_command = self.command_liststore[self.selected_treeiter]

        #creating the treeview and adding the columns
        self.treeview = Gtk.TreeView(self.command_liststore)
        for i, column_title in enumerate(["Voice Commmand", "Command to run", "User"]):
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(column_title, renderer, text=i)
            self.treeview.append_column(column)
        self.treeview.set_cursor(0) # set first row as selected
        self.treeview.get_selection().connect("changed", self.on_selection_button_clicked)
        
        #creating buttons to filter by programming language, and setting up their events
        self.pref_button = Gtk.Button("Preferences")
        self.pref_button.connect("clicked", self.on_pref_button_clicked)
        
        self.train_button = Gtk.Button("Train Command")
        self.train_button.connect("clicked", self.on_train_button_clicked)
        
        self.edit_command_button = Gtk.Button("Edit Command")
        self.edit_command_button.connect("clicked", self.on_edit_command_button_clicked)
        
        self.test_command_button = Gtk.Button("Test Command")
        self.test_command_button.connect("clicked", self.on_test_command_button_clicked)
        
        self.new_command_button = Gtk.Button("New Command")
        self.new_command_button.connect("clicked", self.on_new_command_button_clicked)
        
        self.del_command_button = Gtk.Button("Delete Command")
        self.del_command_button.connect("clicked", self.on_del_command_button_clicked)
        
        self.new_user_button = Gtk.Button("Add User")
        self.new_user_button.connect("clicked", self.on_new_user_button_clicked)
        
        #setting up the layout, putting the treeview in a scrollwindow, and the buttons in a row
        self.scrollable_treelist = Gtk.ScrolledWindow()
        self.scrollable_treelist.set_vexpand(True)
        self.grid.attach(self.scrollable_treelist, 0, 0, 5, 7)
        self.grid.attach(self.pref_button, 5, 0, 1, 1)
        self.grid.attach(self.train_button, 5, 1, 1, 1)
        self.grid.attach(self.test_command_button, 5, 2, 1, 1)
        self.grid.attach(self.edit_command_button, 5, 3, 1, 1)
        self.grid.attach(self.del_command_button, 5, 4, 1, 1)
        self.grid.attach(self.new_command_button, 5, 5, 1, 1)
        self.grid.attach(self.new_user_button, 5, 6, 1, 1)
        
        self.scrollable_treelist.add(self.treeview)

        self.show_all()

    def on_selection_button_clicked(self, widget):
        model, self.selected_treeiter = widget.get_selected()
        if self.selected_treeiter is not None:
            self.selected_command = model[self.selected_treeiter]
            print (self.selected_command)
        
    def on_test_command_button_clicked(self, widget):
        """Called on clicking test Command Button"""
        print (" Tested", self.selected_command[1])
        subprocess.Popen(self.selected_command[1])
        
    def on_pref_button_clicked(self, widget):
        """Called on clicking Preferences Command Button"""
        dialog = PreferencesWindow(self)
        response = dialog.run()
        dialog.destroy()
        
    def on_train_button_clicked(self, widget):
        """Called on clicking Train Command Button"""
        dialog = TrainingWindow(self, self.selected_command[0], self.speech_train_path )
        response = dialog.run()
        if dialog.recording_thread is not None:
            dialog.recording_thread.terminate_thread = True
        dialog.destroy()
        print ("train by recording", self.selected_command[0])

    def on_edit_command_button_clicked(self, widget):
        """Called on clicking Edit Command Button"""
        dialog = NewCommandWindow(self, command = self.selected_command)
        response = dialog.run()
        dialog.destroy()
        if response == Gtk.ResponseType.OK:
            self.update_commands_list()
    
    def on_new_command_button_clicked(self, widget):
        """Called on clicking New Command Button"""
        dialog = NewCommandWindow(self)
        response = dialog.run()
        dialog.destroy()
        if response == Gtk.ResponseType.OK:
            self.update_commands_list()
            
    def on_del_command_button_clicked(self, widget):
        """Called on clicking delete command button"""
        del self.command_list[self.selected_command[0].replace(' ', '_')]
        self.command_liststore.remove(self.selected_treeiter)
        self.update_commands_list()
        
    def on_new_user_button_clicked(self, widget):
        """Called on clicking New User Button"""
        dialog = UserTrainingWindow(self, training_path = "SpeakerRecognition/trainingData")
        response = dialog.run()
        if dialog.recording_thread is not None:
            dialog.recording_thread.terminate_thread = True
        dialog.destroy()
        print ("new User Button Clicked ", self.selected_command[2])
    
    def update_commands_list(self):
        json.dump( self.command_list, open( self.commands_file, 'w' ) )
        
if __name__ == '__main__':
    commands_file = "Config/Commands.json"
    speech_train_path = "SpeechRecognition/TrainingData"
    win = MainWindow(commands_file, speech_train_path)
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()
