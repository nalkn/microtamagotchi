# original porject: https://gitee.com/water_soul/microTk/

__doc__ = '''Module entry
initialize display and load all sub-modules

Containment:
- method
-- microbit.sleep
-- microbit.sleep_ms
-- microbit.ticks_ms
-- microbit.temperature
- module
-- microbit.display
-- microbit.accelerometer
-- microbit.compass
-- microbit.music
- object
-- microbit.button_a
-- microbit.button_b
-- microbit.pin0-19 (without 17,18)
'''

# root functions & classes
from .display import Image, panic
from ._hardware import *

# sub modules
from . import display
from . import accelerometer
from . import compass
from . import _timebase as time
sleep = time.sleep_ms
from . import music
from .music import Sound
from .radio import radio

# neopix
def init_neopix(*args):
    pass
def set_neopix(*args):
    pass
def neopix_actualize(*args):
    pass
def off_neopix(*args):
    pass
def check_connect(*args):
    pass

__all__ = [
    'display', 'accelerometer','compass', 'Image', 'button_a', 'button_b', 'panic',
    'pin0', 'pin1', 'pin2', 'pin3', 'pin4', 'pin5', 'pin6', 'pin7', 'pin8',
    'pin9', 'pin10', 'pin11', 'pin12', 'pin13', 'pin14', 'pin15', 'pin16',
    'pin19', 'pin20', 'temperature', 'time', 'music', 'sleep', 'radio', 'Sound',
    'pin_logo', 'init_neopix', 'set_neopix', 'neopix_actualize', 'off_neopix',
    'check_connect'
]
