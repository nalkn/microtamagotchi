#Projet: MicroTamagotchi
#Auteurs: Killian Nallet, Mattéo Martin-Boileux
#Python: Micropython v1.13 (on microbit v2)
#Coding: utf-8


#--- MICROTAMAGOTCHI - LIB_NEOPIX MICROBIT ---

# imports
from microbit import *
from neopixel import NeoPixel


# variables for neopixel band
actual_mode = None
actual_data = None
np = None
nb_leds = None
redefine_list_pulse = True
lsts_values_pulse = [[i for i in range(0, 256, 1)], [i for i in range(255, -1, -1)]]
indx_lst_pulse = 0
lst_values_pulse = None
indx_value_pulse = None

def init_neopix(nb, pin):
    """ Function for init neopix """
    global nb_leds
    global np
    nb_leds = nb
    np = NeoPixel(pin, nb_leds)


def neopix_actualize(new_data=None):
    """Function for actualize neopix with mode set"""
    global actual_data
    if new_data != None:
        actual_data = new_data
    # all
    if actual_mode == "all":
        for i in range(nb_leds):
            np[i] = actual_data
        np.show()

    # pulse (to test)
    elif actual_mode == "pulse":
        global redefine_list_pulse
        global indx_lst_pulse
        global lst_values_pulse
        global indx_value_pulse

        color_led, vit = actual_data
        if redefine_list_pulse:
            if indx_lst_pulse == 1:
                indx_lst_pulse = 0
            else:
                indx_lst_pulse = 1
            lst_values_pulse = lsts_values_pulse[indx_lst_pulse]
            indx_value_pulse = 0
            redefine_list_pulse = False

        value = lst_values_pulse[indx_value_pulse]
        color_led = list(color_led)
        color_led[color_led.index(255)] = value
        color_led = tuple(color_led)
        for i in range(nb_leds):
            np[i] = color_led
        np.show()
        indx_value_pulse += vit

        if indx_value_pulse >= 255:
            redefine_list_pulse = True

    # count
    elif actual_mode == "count":
        count, color_led1, color_led2 = actual_data
        for i in range(nb_leds):
            if i+1 > count:
                np[i] = color_led1
            else:
                np[i] = color_led2
        np.show()


def set_neopix(mode:str, data, act=False):
    """Function for set the mode to use neopix"""
    global actual_mode
    global actual_data
    assert mode in ["pulse", "all", "count"]
    actual_mode, actual_data = mode, data
    if act:
        neopix_actualize()


def off_neopix():
    """Function for off neopix leds"""
    for i in range(nb_leds):
        np[i] = (0,0,0)
    np.show()
