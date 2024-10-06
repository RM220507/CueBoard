#from playsound import playsound
import pathlib
import pygubu
import json
import tkinter as tk
from tkinter import ttk
import time
import pygame

pygame.init()

PROJECT_PATH = pathlib.Path(__file__).parent
PROJECT_UI = PROJECT_PATH / "main_ui.ui"

#! TO DO
# Clock
# Loading shows
# Cue slider

class CueBoard:
    def __init__(self, master=None):
        self.__builder = builder = pygubu.Builder()
        builder.add_resource_path(PROJECT_PATH)
        builder.add_from_file(PROJECT_UI)
        
        self.__mainwindow = builder.get_object("ctk1", master)
        builder.connect_callbacks(self)
        
        builder.get_object("volume_slider").set(100) # set volume slider 100%
        
        # keybinds
        self.__mainwindow.bind("g", lambda e: self.cue_go())
        self.__mainwindow.bind("s", lambda e: self.stop_all())
        self.__mainwindow.bind("e", lambda e: self.jump_end())
        self.__mainwindow.bind("r", lambda e: self.restart_show())
        self.__mainwindow.bind("m", lambda e: self.mute())
        self.__mainwindow.bind("i", lambda e: self.update_volume(self.__volume + 10))
        self.__mainwindow.bind("k", lambda e: self.update_volume(self.__volume - 10))
        
        self.__cue_list = []
        self.__sounds = []
        self.__playing_sounds = {}
        
        self.__volume = 100
        
        # create cue view 
        self.__cue_view = ttk.Treeview(builder.get_object("show_tab"), columns=("desc", "next", "advance_delay", "delay_from", "auto_go", "file"), selectmode=tk.BROWSE)
        self.__cue_view.heading("#0", text="CUE #")
        self.__cue_view.heading("desc", text="DESCRIPTION")
        self.__cue_view.heading("next", text="ADVANCE")
        self.__cue_view.heading("advance_delay", text="ADVANCE DELAY")
        self.__cue_view.heading("delay_from", text="DELAY FROM ...")
        self.__cue_view.heading("auto_go", text="AUTO GO")
        self.__cue_view.heading("file", text="FILE")
        
        self.__cue_view.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        
        self.load_show("shows/test/") # load a show
        
        self.play_loop() # begin play loop
        
    def play_loop(self):
        current_time = time.time()
        
        for sound_file in list(self.__playing_sounds): #! same cue may be playing twice, so this may not work!
            sound_data = self.__playing_sounds[sound_file]
            
            if current_time >= sound_data["end_time"]:
                self.on_sound_end(sound_data["cue"], sound_data["end_time"] == 0)
                
                del self.__playing_sounds[sound_file]
                
        self.__mainwindow.after(50, self.play_loop)
        
    def start_playing(self, file, cue_num):
        sound = self.__sounds[cue_num - 1]
        channel = sound.play()
        channel.set_volume(self.__volume / 100)
        
        sound_duration = sound.get_length()
        end_time = time.time() + sound_duration
        
        cue_data = self.cue_data(cue_num)
        if cue_data["auto_go"] == "True" and cue_data["delay_from"] == "TRACK END":
            self.__mainwindow.after(round(float(cue_data["advance_delay"])) * 1000, lambda: self.cue_go(int(cue_data["next"])))
        
        self.__playing_sounds[file] = {"channel" : channel, "sound" : sound, "end_time" : end_time, "cue" : cue_num, "vol" : 1}
    
    def on_sound_end(self, cue_num, was_forced):
        if was_forced:
            return
        
        cue_data = self.cue_data(cue_num)
        if cue_data["auto_go"] == "True" and cue_data["delay_from"] == "TRACK END":
            self.__mainwindow.after(round(float(cue_data["advance_delay"])) * 1000, lambda: self.cue_go(int(cue_data["next"])))
        
    def load_show(self, filename):
        with open(filename + "show.json", "r") as f:
            self.__cue_list = json.load(f)
            
        for i, cue in enumerate(self.__cue_list):
            if cue[3]:
                delay_from_text = "TRACK END"
            else:
                delay_from_text = "GO"
            
            self.__cue_view.insert(
                "",
                tk.END,
                text = str(i + 1),
                values = (
                    cue[1],
                    str(cue[2]),
                    str(cue[4]),
                    delay_from_text,
                    cue[5],
                    cue[0]
                )
            )
            
            self.__sounds.append(pygame.mixer.Sound(filename + cue[0]))
        
        self.set_current(1)

    def run(self):
        self.__mainwindow.mainloop()

    def cue_data(self, cue_num):
        return self.__cue_view.set(f"I{cue_num:03d}")

    def cue_go(self, cue_num = None):
        if cue_num is not None:
            cue_data = self.cue_data(cue_num)
        else:
            cue_data = self.cue_data(self.__current_cue)
        
        if cue_data["file"] != "":
            self.start_playing(cue_data["file"], self.__current_cue)
        else:
            self.stop_all()
            
        self.set_current(int(cue_data["next"]))
            
    def set_current(self, cue_num):
        self.__current_cue = cue_num
        self.__builder.get_object("cue_label").configure(text = f"Next Cue: {cue_num}")
        self.__cue_view.selection_set(f"I{self.__current_cue:03d}")

    def mute(self):
        self.update_volume(0)

    def stop_all(self):
        for index in list(self.__playing_sounds):
            sound_data = self.__playing_sounds[index]
            
            sound_data["channel"].set_volume(0)
            sound_data["end_time"] = 0

    def fade_out(self):
        FADEOUT_DURATION_MS = 1000
        
        current_time = time.time()
        
        for index in list(self.__playing_sounds):
            sound_data = self.__playing_sounds[index]
            
            sound_data["sound"].fadeout(FADEOUT_DURATION_MS)
            sound_data["end_time"] = current_time + round(FADEOUT_DURATION_MS / 1000)

    def update_volume(self, value):
        if value > 100:
            value = 100
        elif value < 0:
            value = 0
        
        self.__volume = value
        self.__builder.get_object("volume_slider").set(value)
        
        for index in list(self.__playing_sounds):
            sound_data = self.__playing_sounds[index]
            
            sound_data["channel"].set_volume((value / 100) * sound_data["vol"])

    def restart_show(self):
        self.stop_all()
        
        self.set_current(1)

    def next_cue(self):
        self.set_current(self.__current_cue + 1)

    def jump_end(self):
        self.set_current(len(self.__cue_list))

    def jump_cue(self, value):
        self.set_current(value)


if __name__ == "__main__":
    app = CueBoard()
    app.run()