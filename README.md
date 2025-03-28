# MicroTamagotchi
A project for recreate a customizable [tamagotchi](https://tamagotchi-official.com/us/) on the BBC micro:bit (v2) !
*Why a micro:bit v2 ? Because he had more fonctionnalities than micro:bit v1. He using logo as a button and can play fun sounds !*

## Features
### MicroTamagochi (on micro:bit) :
- Inspired by original tamagochi
- Have emotions, need attention and need to be fed
- You can change / add characters
- Menu with games, character and sleep mode
### MicroTamagochi Tool (for manage MicroTamagochi) :
- Connexion with microtamagotchi (micro:bit)
- Flash microtamagotchi on micro:bit
- Create & download custom characters

## Requirements
- [Python](https://www.python.org/downloads/) (version >= 3.9)
- [BBC micro:bit v2](https://en.vittascience.com/shop/187/carte-micro-bit-v2) (if you don't have a micro:bit v2, don't panic, a simulator is included !)
- [RGB Neopixel](https://en.vittascience.com/shop/23/RGB%2030%20Neopixel%20LED%20Strip%20Grove) with [Grove Shield v2](https://en.vittascience.com/shop/107/shield-grove-pour-micro-bit) (optionnal, for games)

## Installation
***Download project in your computer and in the terminal, move into the "MicroTamagochi_Tool" directory.***
### On Windows :
Install librairies :
```
$ python3 -m pip install -r requirements.txt
```
### On Linux :
Create virtual environnement :
```
$ python3 -m venv env/
```
Activate virtual environnement :
```
$ source env/bin/activate
```
Install librairies :
```
$ pip install -r requirements.txt
```
### Not tested on macOS 

## Usage
### MicroTamagochi_Tool (on computer) :
***In the "MicroTamagochi_Tool" directory,***
run MicroTamagochi_Tool for manage MicroTamagochi on micro:bit :
```
$ python3 main.py
```
MicroTamagochi_Tool has three tabs :
- Connect :
    - Can be connect / disconnect the microbit for send and set personalized figures
    - Can be flash the project on the micro:bit (not need to click on the connect button)
- Create :
    - Create a pixel figure to upload in the MicroTamagotchi (with his name, need to be connected)
- Settings :
    - Change settings
    - Can change the figure of the MicroTamagotchi (not actually supported, in developpement)
    - See Connected Port
### MicroTamagochi (on micro:bit v2) :
***After flashing project***, plug a battery to your micro:bit v2 (or connect this with usb) for use the MicroTamagotchi !
### Game :
Click on the button A or B and after the micro:bit show a play icon. Click on A or B for choose the game program : server (s) or plater (p). Connect RGB Neopix and enjoy ! This Game is easy and fun : 2 players and 1 server, server display leds and if player 1 click, leds (player 1) increase. The same for the player 2. If a player has all the leds, he win !!!

### MicroTamagochi (on computer !) :
***In the "MicroTamagochi" directory,***
run a simulation of MicroTamagochi on micro:bit :
```
$ python3 main.py
```

### Desactivate virtual environnement :
```
$ desactivate
```

## Reuse project Modules
Modules documentation [here](docs/README.md).

### MicroBit_Backend
MicroBit_Backend class is the base of MicroTamagotchi_Tool. It can connect, interact with micropython (on micro:bit) filsystem. This class depends of (modified) pyboard.py tool.
#### Example :
```python
# imports
from backend import MicroBit_Backend

# init backend and connect
backend = MicroBit_Backend(loglevel="debug")
backend.send_cmd("connect")

# exec cmds
platform = backend.send_cmd("platform")
version = backend.send_cmd("version")
print(platform, version, "connected")

# exit
backend.send_cmd("restart")
backend.exit()
```

## Troubleshooting (MicroTamagotchi_Tool) :
### "Status : Connect Failed" :
- The cable may be disconnected / break ?
- The microbit may be recognized by your computer manager (miss a driver ?) ?
- The connexion with the Microbit is probably  used by another program ?
### "Status : Flash Failed" :
- The cable may be disconnected / break ?
- You may have connected another Microbit or disconnected this one ?
#### You also can replug microbit and retry (and if you want more infos about the problem, see logs in data/microtamagotchi_tool.log).
### MicroTamagotchi_Tool not works :
- You also can download the content of MicroTamagotchi folder in the micro:bit (for use MicroTamagotchi) with an IDE (like [Thonny IDE](https://thonny.org/)) instead of use MicroTamagotchi_Tool to flash micropython firmware and download code (Thonny IDE works if micropython is running on the Microbit, if this isn't the case, you can use [Microbit Python Editor](https://python.microbit.org/v/3/) for flashing the micropython firmware, with a program).

## Sources
- [Micropython on Microbit](https://tech.microbit.org/software/micropython/#the-micropython-software) (understand micropython hex files mechanism)
- [Documentation](https://microbit-micropython.readthedocs.io/en/v2-docs/) (use micropython functions on micro:bit)
- [Microbit Python Editor](https://python.microbit.org/v/3/) (edit code with an online simulator)
- [Flaticon](https://www.flaticon.com/) (get fun icons)
