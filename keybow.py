import board
from keybow2040 import Keybow2040
import time
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
import usb_hid

# Set up Keybow
i2c = board.I2C()
keybow = Keybow2040(i2c)
keys = keybow.keys

kbd = Keyboard(usb_hid.devices)

key_colors = []

while True:
    for key in keys:
        if key.number in [0, 1, 4, 5]: # stop
            key.set_led(255, 0, 0)
            if key.pressed:
                keybow.set_all(0, 0, 0)
                kbd.send(Keycode.S)
                time.sleep(0.1)
        elif key.number in [8, 9, 12, 13]: # go
            key.set_led(0, 255, 0)
            if key.pressed:
                keybow.set_all(0, 0, 0)
                kbd.send(Keycode.G)
                time.sleep(0.1)
        elif key.number == 2: # end jump
            key.set_led(255, 255, 0)
            if key.pressed:
                keybow.set_all(0, 0, 0)
                kbd.send(Keycode.E)
                time.sleep(0.1)
        elif key.number == 3: # restart show
            key.set_led(255, 255, 0)
            if key.pressed:
                keybow.set_all(0, 0, 0)
                kbd.send(Keycode.R)
                time.sleep(0.1)
        elif key.number == 10: # mute
            key.set_led(255, 0, 255)
            if key.pressed:
                keybow.set_all(0, 0, 0)
                kbd.send(Keycode.M)
                time.sleep(0.1)
        elif key.number == 11: # fade out
            key.set_led(255, 0, 255)
            if key.pressed:
                keybow.set_all(0, 0, 0)
                kbd.send(Keycode.F)
                time.sleep(0.1)
        elif key.number == 14: # volume down
            key.set_led(0, 0, 255)
            if key.pressed:
                keybow.set_all(0, 0, 0)
                kbd.send(Keycode.K)
                time.sleep(0.1)
        elif key.number == 15: # volume up
            key.set_led(0, 0, 255)
            if key.pressed:
                keybow.set_all(0, 0, 0)
                kbd.send(Keycode.I)
                time.sleep(0.1)
        
    keybow.update()
