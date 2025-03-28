#Projet: MicroTamagotchi
#Auteurs: Killian Nallet, Mattéo Martin-Boileux
#Python: Micropython v1.13 (on microbit v2) / Python >= 3.9
#Coding: utf-8


#--- MICROTAMAGOTCHI - MAIN MICROBIT ---

# imports
import os
import sys
import data_lib
from random import randint
from gc import collect


# check platform and modules to import
if sys.platform in ["win32", "linux"]:
    # imports required modules for the file
    from lib_simulator.microTk import *
    from lib_simulator.microTk._timebase import sleep_ms, ticks_ms

elif sys.platform == "microbit":
    # import required modules
    from microbit import *
    from time import sleep_ms, ticks_ms
    import radio
    from lib_neopix import init_neopix, set_neopix, neopix_actualize, off_neopix
    set_volume(222)

else:
    # platform is not supported
    raise Exception("The platform %s is not supported for [main - microbit] !"%sys.platform)

# functions for display image and emotions
def reverse_img(image, size):
    """Return an reversed image."""
    new_img = []
    buf = []
    for indx, pix in enumerate(image):
        buf.append(pix)
        if indx != 0 and ((indx+1) % size[0]) == 0:
            buf.reverse()
            new_img.extend(buf)
            buf = []
    return new_img

def display_img(posx, posy, delay=None, imgsize=None, rv=False):
    """Display an image on the screen with his posx, posy and size."""
    # load emotion image
    global image, frame, size
    if not imgsize:
        img = figure_frames[frame]
        if rv: img = reverse_img(img, size)
        frame += 1
        if frame >= nb_frames:
            frame = 0
        image, sz = img, size
    else:
        img, sz = imgsize

    # show img at pos
    display.clear()
    for x in range(sz[0]):
        for y in range(sz[1]):
            try:
                display.set_pixel(
                    x+posx,
                    y+posy,
                    img[x+y*sz[0]]
                )
            except:
                pass
    # sleep delay
    if delay:
        sleep_ms(delay)

# menu functions
def menu_play():
    """Play games menu."""
    # if in the simulator
    if sys.platform != "microbit": 
        display.scroll("error")
        return
    import game
    # wait button released
    while pin_logo.is_touched(): pass
    # choose mode
    slct = "s"
    while not pin_logo.is_touched():
        display.show(slct)
        sleep(10)
        if button_b.is_pressed():
            if slct == "s":
                slct = "p"
            else:
                slct = "s"
        while button_b.is_pressed(): pass
    # wait button released
    while pin_logo.is_touched(): pass

    # exec game
    audio.play(Sound.GIGGLE)
    if slct == "s":
        # server
        init_neopix(30, pin0)
        game.server(radio, set_neopix, neopix_actualize, off_neopix)
        off_neopix()
    else:
        # player
        game.player(radio)

    # wait button released
    while pin_logo.is_touched(): pass

#def menu_conn(a, b, l):
#    """Connexion menu."""
#    pass

#def menu_set(a, b, l):
#    """Settings menu."""
#    pass

#TODO: changer l'emotion
#TODO: personnage qui se déplace aléatoirement avec émotions aléatoires

# init radio
radio.on()
radio.config(group=222)

# load settings, images and check files exists
settings_file, images_file = "settings.mtd", "images.mtd"
data = []
for file in [settings_file, images_file]:
    # modif path
    if sys.platform in ["win32", "linux"]:
        PATH_PRJ = os.path.dirname(os.path.dirname(os.path.dirname(__file__))) # /
        file = os.path.join(PATH_PRJ, "data", "microbit_data", file)
    # try open file
    try:
        data.append(data_lib.load(file))
    # if except: show err
    except:
        while True:
            display.show(Image.SAD)
            sleep_ms(1000)
            display.scroll("file %s not found !"%str(file))
settings, images = data

# collect waste
collect()

# get figure and emotion
figure = settings["figure"]
emotion = settings["emotion"]
emotion_soundsfaces = {
    "happy": (Sound.HAPPY, Image.HAPPY),
    "bored": (Sound.SOARING, Image.ASLEEP),
    "sad": (Sound.SAD, Image.SAD),
    "angry": (Sound.MYSTERIOUS, Image.ANGRY),
#    "hungry": (Sound.SOARING, Image.CONFUSED),
}
old_emotion = None
frame = 0
posx, posy = 0,2 #posx, posy = 3,3

# menu
menu = [
    (None, None),
    ([0,9,0, 0,9,9, 0,9,0], menu_play),
#    ([9,9,9, 0,0,0, 0,9,0], menu_conn),
#    ([9,9,9, 9,0,9, 9,9,9], menu_set)
]
indx_menu = 0

# other vars
self_sleep = False
force_sleep = 10
start = ticks_ms()
last_activity = start
last_lum = 0
last_emote, emote_wait = start, randint(6,10)*1000
hy_ok = False

# collect waste
collect()

# main loop
while True:
    # check emotion
    if emotion != old_emotion:
        figure_data = images[figure]
        figure_frames = figure_data["data"]
        nb_frames = len(figure_frames)
        size = figure_data["size"]
        delay = figure_data["delay"]
        old_emotion = emotion

    # --- events --------------------

    # menu
    if not self_sleep:
        logo_press = False
        if button_a.is_pressed():
            indx_menu -= 1
            while button_a.is_pressed(): pass
        elif button_b.is_pressed():
            indx_menu += 1
            while button_b.is_pressed(): pass

    # set menu state
    if indx_menu < 0: indx_menu = 1
    if indx_menu > 1: indx_menu = 0
    pan_menu = menu[indx_menu]
    in_menu = pan_menu[0] != None
    
    # animations
    if not in_menu:
        # get data
        x = accelerometer.get_x()
        z = accelerometer.get_z()
        try: lum = display.read_light_level()
        except: lum = 0

        # check events
        if abs(last_lum - lum) > 50: # lum
            last_activity = ticks_ms()
        last_lum = lum
        if z > -60: # jump
            while posy > -3:
                posy -= 1
                display_img(posx,posy, 200, rv=True)
            for _ in range(5):
                posy += 1
                display_img(posx,posy, 200)
            last_activity, emotion = ticks_ms(), "happy"
        elif x > 500: # right
            while posx < 5:
                posx += 1
                display_img(posx,posy, 200, rv=True)
            for _ in range(5):
                posx -= 1
                display_img(posx,posy, 200)
            last_activity, emotion = ticks_ms(), "happy"
        elif x < -500: # left
            while posx > -5:
                posx -= 1
                display_img(posx,posy, 200)
            for _ in range(5):
                posx += 1
                display_img(posx,posy, 200, rv=True)
            last_activity, emotion = ticks_ms(), "happy"

    # -------------------------------

    # collect waste
    collect()

    # sleep a little
    sleep(force_sleep)

    # change image if not in menu:
    if not in_menu:
        if ticks_ms() - start >= delay-force_sleep:
            # check activity
            if ticks_ms() - last_activity > 15000:
                self_sleep = True
                hy_ok = False
                emotion = "bored"
                display.clear()
            else:
                self_sleep = False

            if not self_sleep:
                # display image
                if not hy_ok:
                    try: audio.play(Sound.HELLO) # type: ignore
                    except: pass
                    hy_ok = True
                display_img(posx,posy)

                # display emotion
                if ticks_ms() - last_emote > emote_wait:
                    sound, face = emotion_soundsfaces[emotion]
                    display.show(face)
                    try: audio.play(sound) # type: ignore
                    except: pass
                    sleep(500)
                    last_emote, emote_wait = ticks_ms(), randint(6,10)*1000

            # reset delay timer
            start = ticks_ms()

    # display menu
    else:
        icon_menu, funct_menu = pan_menu
        # display menu icon
        display_img(1,1, imgsize=(icon_menu,[3,3]))
        # call menu funct
        if pin_logo.is_touched():
            funct_menu()
        # reset activity and emote wait time
        last_activity = last_emote = ticks_ms()

    # collect waste
    collect()
