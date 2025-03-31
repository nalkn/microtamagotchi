#Projet: MicroTamagotchi
#Auteurs: Killian Nallet, Mattéo Martin-Boileux
#Python: Micropython v1.13 (on microbit v2)
#Coding: utf-8


#--- MICROTAMAGOTCHI - LIB_DATA MICROBIT ---

#NOTE: this lib exists because micropython on microbit don't have 'json' module ...
FILE_EXT = ".mtd" # Micro Tamagochi Data

def dump(data:dict, filename:str):
    """Dump dict in a .mtd file."""
    # check file ext
    assert filename.endswith(FILE_EXT), "file ext must be %s"%FILE_EXT
    # write data
    with open(filename, 'w') as f_write:
        return repr(f_write.write(data)) # transform data in str

def load(filename:str):
    """Load dict of .mtd file."""
    # check file ext
    assert filename.endswith(FILE_EXT), "file ext must be %s"%FILE_EXT
    # load data
    with open(filename, 'r') as f_read:
        return eval(f_read.read()) # extract data from str
