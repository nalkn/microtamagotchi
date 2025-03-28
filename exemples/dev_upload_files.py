# imports
import os
from backend import MicroBit_Backend

# constants
PATH_SRC_MICROBIT = "" # put here folder path of files to download

# init backend and connect
backend = MicroBit_Backend()
backend.send_cmd("connect")

# send files
for file_or_dir in os.listdir(PATH_SRC_MICROBIT): # including main.py
    path = os.path.join(PATH_SRC_MICROBIT, file_or_dir)
    if os.path.isfile(path):
        backend.send_cmd("put", (path,))

# exit
backend.send_cmd("restart")
backend.exit()
