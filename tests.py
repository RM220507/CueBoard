import pygame
import time
from threading import Thread

# Initialize pygame mixer
pygame.mixer.init()

# Callback function to be executed when a sound ends
def on_sound_end(sound_file):
    print(f"Sound {sound_file} has finished playing!")

# Function to play a sound and monitor its completion
def play_sound(sound_file, callback):
    # Load the sound file
    sound = pygame.mixer.Sound(sound_file)
    
    # Play the sound
    channel = sound.play()
    
    # Wait until the sound is done playing
    while channel.get_busy():
        time.sleep(0.1)  # Prevent high CPU usage by sleeping a bit

    # Call the callback function when the sound finishes
    callback(sound_file)

# Function to play multiple sounds simultaneously
def play_multiple_sounds(sound_files):
    threads = []
    
    # Create a thread for each sound file to play them simultaneously
    for sound_file in sound_files:
        thread = Thread(target=play_sound, args=(sound_file, on_sound_end))
        threads.append(thread)
        thread.start()
    
    # Join the threads to ensure they all complete
    for thread in threads:
        thread.join()

# List of sound files to be played (replace with actual sound file paths)
sound_files = ["shows/test/1.mp3", "shows/test/2.mp3", "shows/test/3.mp3"]

# Start playing the sounds
play_multiple_sounds(sound_files)