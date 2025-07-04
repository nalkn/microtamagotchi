# MicroTamagotchi
A project for recreate a customizable [tamagotchi](https://tamagotchi-official.com/us/) on the BBC micro:bit (v2) !
*Why a micro:bit v2 ? Because he had more fonctionnalities than micro:bit v1. V2 use his logo as a button and can play fun sounds !*

## Features
### MicroTamagochi (on micro:bit)
- Inspired by original tamagochi
- Have emotions, need attention
- You create and add characters
- Fun game included 
### MicroTamagochi Tool (for manage MicroTamagochi)
- Connexion with microtamagotchi (micro:bit)
- Flash microtamagotchi on micro:bit (flash a micropython.hex file and download python and data files)
- Create & download custom characters with multiples frames

## Requirements
- [Python](https://www.python.org/downloads/) (version >= 3.9)
- [BBC micro:bit v2](https://en.vittascience.com/shop/187/carte-micro-bit-v2) (if you don't have a micro:bit v2, don't panic, a simulator is included !)
- [RGB Neopixel](https://en.vittascience.com/shop/23/RGB%2030%20Neopixel%20LED%20Strip%20Grove) with [Grove Shield v2](https://en.vittascience.com/shop/107/shield-grove-pour-micro-bit) (optionnal, for games)

## Installation
***Download project in your computer and in the terminal, move into the project directory (with 'requirements.txt').***
### On Windows
Install librairies :
```
$ python3 -m pip install -r requirements.txt
```
### On Linux
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
### MicroTamagochi_Tool (on computer)
***In the "MicroTamagochi_Tool" directory,***
run MicroTamagochi_Tool for manage MicroTamagochi on micro:bit :
```
$ python3 main.py
```
MicroTamagochi_Tool has three main functionalities :
- Left Frame :
    - Save your MicroTamagotchi actual configuration in a file
    - Import MicroTamagotchi configuration from a file and save configuration into
    - Frame of the character in creation
- Connect :
    - Can be connect / disconnect the microbit for send and set personalized figures
    - Can be flash the project on the micro:bit (not need to click on the connect button)
- Create :
    - Create frames for a pixel character to upload in the MicroTamagotchi (with his name, need to be connected)
- Settings :
    - Change settings
    - Can change the character of the MicroTamagotchi
    - See Connected Port
### MicroTamagochi (on micro:bit v2)
***After flashing project***, connect your micro:bit v2 with usb (or plug a battery) for use the MicroTamagotchi !
### MicroTamagotchi Game
***Click on the button A or B and after the micro:bit show a play icon.*** Click on A or B for choose the game mode : server (s) or player (p). This Game is easy to play and fun : 2 players and 1 server, server display leds and if player 1 click, leds (player 1) increase. The same for the player 2. If a player has all the leds, he win ! Connect RGB Neopixel (with Grove Shield v2 on port 1) on server (optional) and enjoy !!!

### MicroTamagochi (on computer !)
***In the "MicroTamagochi" directory,***
run a simulation of MicroTamagochi on computer :
```
$ python3 main.py
```

### Desactivate virtual environnement
```
$ deactivate
```

## Use project Modules
Modules documentation [here](docs/README.md).

## Data Format Explanation
The MicroTamagotchi '.mtd' (Micro Tamagotchi Data) files (created for this project). This is for store a simple python 'dict' of data (but you can't use object storage like 'pickle' module).
### Structure example
images.mtd :
```
{
    "dog": {
        "delay": 150,
        "data": [
            [[0,9,0,0,7, 9,9,6,6,0, 0,6,0,6,0], [5,3]]
            [[0,9,0,0,4, 9,9,6,6,0, 0,6,0,6,0], [5,3]]
        ]
    }
}
```
- "dog" : name of the character
- "delay" : the delay (in miliseconds) between character frames
- "data" : data of the character frames (lists of pixels intensity values from 0 to 9)
#### Note : pixels values generated by MicroTamagotchi_Tool can be -1 (but it doesn't create errors).

## Troubleshooting (MicroTamagotchi_Tool)
### "Status : Connect Failed"
- The cable may be disconnected / break ?
- The microbit may be recognized by your computer manager (miss a driver ?) ?
- The connexion with the Microbit is probably  used by another program ?
### "Status : Flash Failed"
- The cable may be disconnected / break ?
- You may have connected another Microbit or disconnected this one ?
#### You also can replug microbit and retry (and if you want more infos about the problem, see logs in file 'data/microtamagotchi_tool.log').
### MicroTamagotchi_Tool not works
- You also can download the content of 'sources/MicroTamagotchi/' and 'data/microbit_data/' folders in the micro:bit (for use MicroTamagotchi) with a micropython compatible IDE (like [Thonny IDE](https://thonny.org/)) instead of use MicroTamagotchi_Tool for flash micropython and download python code (Thonny IDE works only if micropython is on the Microbit, if this isn't the case, you can use [Microbit Python Editor](https://python.microbit.org/v/3/) for flashing the micropython firmware, with a program).

## Sources
- [Micropython on Microbit](https://tech.microbit.org/software/micropython/#the-micropython-software) (understand micropython hex files mechanism)
- [Micropython Documentation](https://microbit-micropython.readthedocs.io/en/v2-docs/) (use micropython functions on micro:bit)
- [Microbit Python Editor](https://python.microbit.org/v/3/) (edit code with an online simulator)
- [Flaticon](https://www.flaticon.com/) (get fun icons)

## Participation in the **Throphee NSI Competition**
The **[Throphee NSI](https://trophees-nsi.fr)** is a french programming competition for high school students. Finally this project didn't win the competition, but it did qualify for the final! 
- Territorial qualification : Qualified
- National qualification : Eliminated