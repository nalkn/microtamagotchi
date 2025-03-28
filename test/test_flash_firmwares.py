import os
import uflash
import hex_firmwares

src = os.path.dirname(os.path.dirname(__file__))
path_python_script = os.path.join(src, "sources", "MicroTamagotchi", "main.py")
path_out_hexfile = os.path.join(src, "tests", "micropython.hex")

def save_script_to_hex(path_script=None, path_hex=None):
    """Include and save python script in a micropython .hex file."""
    # read script code
    if path_script is None:
        python_script = """from microbit import *
display.show(Image("00000:00900:09990:00900:00000:"))""".encode('utf-8')
    else:
        with open(path_script, 'rb') as python_file:
            python_script = python_file.read()

    # choose runtime (base micropython firmware)
    runtime = hex_firmwares.RUNTIME_1 #uflash._RUNTIME
    # generate hex code with the script code
    hex_code = uflash.embed_fs_uhex(runtime, python_script)

    # if not output path for the firmware, write on a microbit
    if path_hex is None:
        path_hex = os.path.join(uflash.find_microbit(), "micropython.hex")

    # save hex code in a file
    with open(path_hex, 'wb') as output:
        output.write(hex_code.encode('ascii'))
        if path_hex is None:
            output.flush()
            os.fsync(output.fileno()) # only for write hex on the microbit

save_script_to_hex()
