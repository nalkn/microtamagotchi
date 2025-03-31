#Projet: MicroTamagotchi
#Auteurs: Killian Nallet, Mattéo Martin-Boileux
#Python: Micropython v1.13 (on microbit v2)
#Coding: utf-8


#--- MICROTAMAGOTCHI - GAME MICROBIT ---

# imports
import gc


# server program (with neopix)
def server(radio, set_np, actualize_np, off_np):
    """MicroTamagotchi Game - Server Program"""
    # imports
    from microbit import display, Image, sleep, pin_logo
    import machine

    # variables
    nb_all_leds = 30
    count = nb_all_leds/2
    count_locked = False
    red = (255,0,0)
    green = (0,255,0)
    blue = (0,0,255)
    player1_started = False
    player2_started = False

    # functions
    def actualize_count(new_count):
        global count
        if new_count >= 0 and new_count <= nb_all_leds:
            count = new_count

    # animations for wait players conneted
    display.show(Image.ASLEEP)
    set_np("pulse", (red, 3), True)
    while not (player1_started and player2_started):
        message = radio.receive()

        if pin_logo.is_touched():
            return
        
        if message != None:
            if message == "player1_started":
                player1_started = True
            elif message == "player2_started":
                player2_started = True
        
        actualize_np()
        gc.collect()

    # send start
    radio.send("starting")
    off_np()
    for i in range(3, 0, -1):
        display.show(i)
        sleep(1000)
    radio.send("started")

    # while loop for manage events
    set_np("count", (count, blue,green), True)
    display.show(Image.HAPPY)
    while True:
        message = radio.receive()
        
        if pin_logo.is_touched():
            return

        elif not count_locked and message != None:
            if message == "1":
                actualize_count(count+1)
                str_cnt = str(int(count))
                radio.send(str_cnt)
            elif message == "2":
                actualize_count(count-1)
                str_cnt = str(int(count))
                radio.send(str_cnt)
            actualize_np((count, blue,green))
            if count == 30:
                count_locked = True
                display.scroll("player 1 win")
            elif count == 0:
                count_locked = True
                display.scroll("player 2 win")

        gc.collect()


# player program
def player(radio):
    """MicroTamagotchi Game - Server Program"""
    # imports
    from microbit import display, Image, set_volume, sleep, button_a,button_b,pin_logo
    from time import ticks_ms
    import music

    # variables
    display.clear()
    while True:
        if button_a.is_pressed():
            player = "1"
            break
        if button_b.is_pressed():
            player = "2"
            break
    count = 15
    theme_played = False
    game_starting = False

    def actualize_count(new_count):
        """Actualize var count with new value"""
        global count
        global theme_played
        if new_count >= 0 and new_count <= 30:
            count = new_count
            print("new count:", count)
        if count == 30:
            display.show(Image.HAPPY)
            if not theme_played:
                music.play(["e", "e", "e", "e", "f", "g", "g", "e", "d", "e"])
                theme_played = True
            display.scroll("You win", loop=True)
        elif count == 0:
            display.show(Image.ASLEEP)
            sleep(1000)
            display.scroll("You lose", loop=True)

    # wait all players connected
    display.show(player)
    sleep(1000)
    ms_st = ticks_ms()
    while True:
        message = radio.receive()

        if pin_logo.is_touched():
            return

        if message is not None:
            if message == "starting":
                game_starting = True
                display.clear()
            elif message == "started":
                break
 
        if not game_starting:
            ms = ticks_ms() - ms_st
            if ms < 300:
                display.clear()
                display.set_pixel(1,2, 9)
            elif ms < 600:
                display.set_pixel(2,2, 9)
            elif ms < 900:
                display.set_pixel(3,2, 9)
            else:
                radio.send("player" + player + "_started")
                ms_st = ticks_ms()

        gc.collect()

    # main loop
    display.show(Image.HAPPY)
    while True:
        message = radio.receive()

        if pin_logo.is_touched():
            return

        if message is not None:
            try:
                new_cnt = int(message)
                if player == "2":
                    new_cnt = 30-new_cnt
                actualize_count(new_cnt)
            except:
                pass

        if button_a.is_pressed():
            radio.send(player)
            while button_a.is_pressed(): pass
        elif button_b.is_pressed():
            radio.send(player)
            while button_b.is_pressed(): pass

        gc.collect()


# collect garbage
gc.collect()