#Projet: MicroTamagotchi
#Auteurs: Killian Nallet, Mattéo Martin-Boileux
#Python: Micropython (on microbit v1)
#Coding: utf-8


#--- MICROTAMAGOTCHI - MAIN TEST_MICROBIT_V1 ---

# imports
from gc import collect

# import required modules
from microbit import display, button_a, button_b, accelerometer #type:ignore
from time import sleep_ms, ticks_ms

# functions for display image and emotions
def display_img(posx, posy, delay=None, imgsize=None, rv=False):
    """Display an image on the screen with his posx, posy and size."""
    # load emotion image
    global image, frame
    if not imgsize:
        img, size = character_frames[frame]
        ## resize
        if rv:            
            new_img = []
            buf = []
            for indx, pix in enumerate(image):
                buf.append(pix)
                if indx != 0 and ((indx+1) % size[0]) == 0:
                    buf.reverse()
                    new_img.extend(buf)
                    buf = []
            img = new_img
        ## resize
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

# collect waste
collect()

# load settings, images and check files exists
settings_file, images_file = "settings.mtd", "images.mtd"
with open(settings_file, 'r') as f_read:
    settings = eval(f_read.read())
with open(images_file, 'r') as f_read:
    images = eval(f_read.read())

# collect waste
collect()

# get character and emotion
character = settings["character"]
emotion = settings["emotion"]
old_emotion = None
frame = 0
posx, posy = 0,2 #posx, posy = 3,3

# load character
character_data = images[character]
character_frames = character_data["data"]
delay = character_data["delay"]
nb_frames = len(character_frames)

# menu
menu = [
    (None, None),
    ([0,9,0, 0,9,9, 0,9,0], None),
]
indx_menu = 0

# other vars
self_sleep = False
force_sleep = 10
start = ticks_ms()
last_activity = start
last_lum = 0
last_emote, emote_wait = start, 5000
hy_ok = False

# collect waste
collect()

# main loop
while True:
    # check emotion
    if emotion != old_emotion:
        # change emotion ...
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
    sleep_ms(force_sleep)

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
                    hy_ok = True
                display_img(posx,posy)

            # reset delay timer
            start = ticks_ms()

    # display menu
    else:
        icon_menu, funct_menu = pan_menu
        # display menu icon
        display_img(1,1, imgsize=(icon_menu,[3,3]))
        # reset activity and emote wait time
        last_activity = last_emote = ticks_ms()

    # collect waste
    collect()
