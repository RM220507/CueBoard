import pathlib
import pygubu
import json
import tkinter as tk
from tkinter import ttk
import time
import pygame
from tkinter.filedialog import askdirectory
import os.path

pygame.init()

PROJECT_PATH = pathlib.Path(__file__).parent
PROJECT_UI = PROJECT_PATH / "main_ui.ui"

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
        
        self.__playing_sounds = []
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
        
        self.__builder.get_object("cue_select_slider").configure(from_=1, to=1, number_of_steps=0)
        
        self.load_show("shows/omtg/") # load a show
        
        self.play_loop() # begin play loop
        
    def update_clock(self):
        if not self.__show_started:
            self.__builder.get_object("clock_label").configure(text="00:00:00:00")
            return
        
        current_time = time.time()
        time_delta = current_time - self.__start_time
        
        hours, rem = divmod(time_delta, 3600)
        minutes, seconds = divmod(rem, 60)
        milliseconds = (seconds - int(seconds)) * 100
        
        formatted_time_delta = f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}:{int(milliseconds):02}"
        self.__builder.get_object("clock_label").configure(text=formatted_time_delta)
        
        self.__mainwindow.after(10, self.update_clock)
        
    def play_loop(self):
        current_time = time.time()
        
        to_end = []
        for i, data in enumerate(self.__playing_sounds): #! same cue may be playing twice, so this may not work!
            if current_time >= data["end_time"]:
                self.on_sound_end(data["cue"], data["end_time"] == 0)
                
                to_end.append(i)
            
        for i, index_to_pop in enumerate(to_end):
            self.__playing_sounds.pop(index_to_pop - i)
            
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
        
        self.__playing_sounds.append({"channel" : channel, "sound" : sound, "end_time" : end_time, "cue" : cue_num, "vol" : 1})
    
    def on_sound_end(self, cue_num, was_forced):
        if was_forced:
            return
        
        cue_data = self.cue_data(cue_num)
        if cue_data["auto_go"] == "True" and cue_data["delay_from"] == "TRACK END":
            self.__mainwindow.after(round(float(cue_data["advance_delay"])) * 1000, lambda: self.cue_go(int(cue_data["next"])))
        
    def load_show_prompt(self):
        directory = askdirectory()
        self.load_show(directory)
        
    def load_show(self, filename):
        self.__show_started = False
        self.stop_all()
        
        # delete the current cue view table, and replace it
        for i in self.__cue_view.get_children():
            self.__cue_view.delete(i)
        
        self.__cue_list = []
        self.__sounds = []
        self.__playing_sounds = []
        self.__cue_lookup = []
        
        with open(os.path.join(filename, "show.json"), "r") as f:
            self.__cue_list = json.load(f)
            
        for i, cue in enumerate(self.__cue_list):
            if cue[3]:
                delay_from_text = "TRACK END"
            else:
                delay_from_text = "GO"
            
            id = self.__cue_view.insert(
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
            
            self.__cue_lookup.append(id)
            
            self.__sounds.append(pygame.mixer.Sound(os.path.join(filename, cue[0])))
        
        self.__builder.get_object("cue_select_slider").configure(from_=1, to=len(self.__sounds), number_of_steps=len(self.__sounds) - 1)
        self.set_current(1)

    def run(self):
        self.__mainwindow.mainloop()

    def cue_data(self, cue_num):
        return self.__cue_view.set(self.__cue_lookup[cue_num - 1])

    def cue_go(self, cue_num = None):
        if cue_num is not None:
            cue_data = self.cue_data(cue_num)
        else:
            cue_data = self.cue_data(self.__current_cue)
            
        if not self.__show_started:
            self.__show_started = True
            self.__start_time = time.time()
            self.update_clock()
        
        if cue_data["file"] != "":
            self.start_playing(cue_data["file"], self.__current_cue)
        else:
            self.stop_all()
            
        self.set_current(int(cue_data["next"]))
            
    def set_current(self, cue_num):
        if cue_num > len(self.__sounds):
            cue_num = len(self.__sounds)
        
        self.__builder.get_object("cue_select_slider").set(cue_num)
        self.__current_cue = cue_num
        self.__builder.get_object("cue_label").configure(text = f"Next Cue: {cue_num}")
        self.__cue_view.selection_set(self.__cue_lookup[self.__current_cue - 1])

    def mute(self):
        self.update_volume(0)

    def stop_all(self):
        for sound_data in self.__playing_sounds:
            sound_data["channel"].set_volume(0)
            sound_data["end_time"] = 0

    def fade_out(self):
        FADEOUT_DURATION_MS = 1000
        
        current_time = time.time()
        
        for sound_data in self.__playing_sounds:
            sound_data["sound"].fadeout(FADEOUT_DURATION_MS)
            sound_data["end_time"] = current_time + round(FADEOUT_DURATION_MS / 1000)

    def update_volume(self, value):
        if value > 100:
            value = 100
        elif value < 0:
            value = 0
        
        self.__volume = value
        self.__builder.get_object("volume_slider").set(value)
        
        for sound_data in list(self.__playing_sounds):
            sound_data["channel"].set_volume((value / 100) * sound_data["vol"])

    def restart_show(self):
        self.__show_started = False
        
        self.stop_all()
        
        self.set_current(1)

    def next_cue(self):
        self.set_current(self.__current_cue + 1)

    def jump_end(self):
        self.set_current(len(self.__cue_list))
        self.__show_started = False

    def jump_cue(self, value):
        self.set_current(int(value))


if __name__ == "__main__":
    app = CueBoard()
    app.run()