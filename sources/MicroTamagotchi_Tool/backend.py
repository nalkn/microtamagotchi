#Projet: MicroTamagotchi
#Auteurs: Killian Nallet, Mattéo Martin-Boileux
#Python: Python >= 3.9
#Coding: utf-8


#--- MICROTAMAGOTCHI - TOOL BACKEND ---

# imports
import os
import time
import logging
from threading import Thread

import uflash

import serial.tools.list_ports
import pyboard as tool


# constants
MICROPYTHON_RUNTIME = uflash._RUNTIME # micropython firmware runtime (v1 and v2)
PATH_SRC = os.path.dirname(os.path.dirname(__file__)) # sources/
PATH_DATA = os.path.join(os.path.dirname(PATH_SRC), "data") # data/
PATH_SRC_MAIN_MICROBIT = os.path.join(PATH_SRC, "MicroTamagotchi") # sources/MicroTamagotchi/
PATH_DATA_MAIN_MICROBIT = os.path.join(PATH_DATA, "microbit_data") # data/microbit_data/


# Connect Backend
class MicroBit_Backend:

    """
    Serial Connexion Backend using pyboard for send, read files to the microbit.
    """

    image_sync = "00000:00000:90909:00000:00000:"

    def __init__(
            self, 
            show_conn_stat=None, 
            send_sync=True,
            console_log=False,
            logfile_path=None,
            loglevel="info",
            check_platform=True
        ):
        self._show_conn_stat = show_conn_stat
        self._send_sync_payload = send_sync
        self.check_platform = check_platform
        self.connected, self.connecting, self.connect_failed = False, False, False
        self.flashed, self.flashing, self.flash_failed = False, False, False
        self.flash_hex_info = (None, None, None)
        self.restart_after_flash = False
        self.microbit = None
        self.port = None
        self.version = None
        self.restarted = False
        self._cmd = None
        self._cmd_data = None
        self._cmd_return = None
        self._in_exec = False
        self._exit = False
        self.backend_cmds = [
            # if c (or 'connect') called here, microbit already connected
            (["connect", "c"], lambda: self.log.info("-> already connected"), None),
            # other commands
            (["disconnect", "d", "close"], self._close, None),
            (["restart", "rsta"], self._restart, None),
            (["reset", "rst"], self._reset, ["restart"]),
            (["exec", "ex"], "exec", ["command"]),
            (["execfile", "exf"], "execfile", ["filename"]),
    #        (["time", "t"], "get_time", None),
            (["exists", "exs"], "fs_exists", ["src"]),
            (["listdir", "ls"], "fs_listdir", None),
            (["platform", "p"], "fs_platform", None),
            (["version", "v"], "fs_version", None),
            (["st", "stat", "st"], "fs_stat", ["src"]),
            (["ct", "cat", "ct"], "fs_cat", ["src","chunk_size"]),
            (["read_file", "rf"], "fs_readfile", ["src","chunk_size"]),
            (["write_file", "wf"], "fs_writefile", ["src","chunk_size"]),
            (["copy", "cp"], "fs_cp", ["src","dest"]),
            (["get", "g"], "fs_get", ["src","dest"]),
            (["put", "p"], "fs_put", ["src"]),
            (["remove", "rm"], "fs_rm", ["src"]),
            (["touch", "th"], "fs_touch", ["src"])
        ]
        # configure logger
        self.log = logging.getLogger(__name__)
        self.log.setLevel("DEBUG")
        # console log
        if console_log:
            logconsformat = logging.Formatter(
                "{message}",style="{"
            )
            console_handler = logging.StreamHandler()
            console_handler.setLevel(loglevel.upper())
            console_handler.setFormatter(logconsformat)
            self.log.addHandler(console_handler)
        # file log        
        if logfile_path is not None: # example: data/backend.log
            logfileformat = logging.Formatter(
                "{asctime}-{levelname}: {message}",style="{", datefmt="%H.%M.%S"
            )
            file_handler = logging.FileHandler(logfile_path, mode="a", encoding="utf-8")
            file_handler.setLevel("DEBUG")
            file_handler.setFormatter(logfileformat)
            self.log.addHandler(file_handler)
        # main thread
        self._th_backend = Thread(
            target=self._backend
        )
        # sync thread
        self._th_backend_show_sync = Thread(
            target=self._backend_show_sync, 
            daemon=True
        )
        # start backend
        self._th_backend.start()
        self._th_backend_show_sync.start()
        self.log.info("Microbit Backend -> started")
        self.show_conn_stat()

    def show_conn_stat(self):
        try:
            self._show_conn_stat(
                self.connected, self.connecting, self.connect_failed,
                self.flashed, self.flashing, self.flash_failed,
                self.flash_hex_info
            )
            self.log.debug("show conn stat")
        except Exception as err:
            self.log.debug(f"show conn stat -> failed ({type(err).__name__}: {err})")

    def _list_ports(self, only_device=False):
        """List open ports for the serial connection."""
        serial_ports = []
        for port in serial.tools.list_ports.comports():
            if only_device:
                serial_ports.append(port.device)
            else:
                serial_ports.append(port)
        return serial_ports

    def _try_connect(self, device) -> bool:
        """Try to connect a port."""
        try:
            self.log.debug(f"try to connect [{device}]")
            self.microbit = None
            self.microbit = tool.Pyboard(device)
            self.port = device
            time.sleep(1)
        except tool.PyboardError as err:
            self.log.warning(f"failed to connect [{device}] ({type(err).__name__}: {err})")
            return False # used port ?
        except:
            pass
        else:
            try:
                self.microbit.enter_raw_repl()
                self.log.debug(f"connected to [{device}]")
                return True # open port
            except:
                self.log.debug(f"connecting to [{device}] failed")
                return False # board program wait something ...
        self.microbit, self.port, self.version = None, None, None
        return None # no port

    def _connect(self, wait_if_not_conn=True) -> bool:
        """Create serial connexion with the microbit, return True if sucess."""
        # try connect old port
        connected = False
        if self._try_connect(self.port):
            connected = True
        # try connect to each port
        for port in self._list_ports():
            if self._try_connect(port.device):
                connected = True        

        # check if microbit connected
        if self.connecting and connected: # (if self.connecting=False: aborted)
            self.log.info(f"-> connected to [{self.port}]")
            platform = self.microbit.fs_platform()
            if self.check_platform and platform != "microbit":
                self.log.warning(f"backend can don't work with '{platform}' platform !")
            self.version = self.microbit.fs_version()
            self.connected = True
            self.connect_failed = False
            self.restarted = False
        else:
            # some wait if no port found (for app)
            if wait_if_not_conn:
                start = time.time()
                while self.connecting and time.time() - start < 2:
                    time.sleep(0.05)
                self.log.info(f"-> no device to connect found !")
            self._close()
            self.connect_failed = True

        # show new connexion status
        self.connecting = False

    def _close(self):
        """Close serial connexion with the microbit."""
        # if the microbit reseted, not need to close (don't stop the microbit)
        if not self.restarted:
            if self.port is not None:
                self.log.info(f"-> [{self.port}] disconnected")
            try:
                self.microbit.exit_raw_repl()
                self.microbit.close()
            except:
                pass
        self.microbit = None
        self.connected = False
        self.version = None

    def _restart(self):
        """Restart the microbit."""
        self.log.debug(f"restart [{self.port}]")
        self.microbit.reset()
        self.connected = False
        self.version = None
        self.restarted = True

    def _save_hex_callback(self, src:str, dest:str):
        """Write a file with progress callback."""
        src_size = os.stat(src).st_size
        written = 0
        data_len = 1
        with open(src, 'rb') as f_src:
            with open(dest, 'wb') as f_dest:
                while data_len:
                    data = f_src.read(256)
                    f_dest.write(data)
                    data_len = len(data)
                    written += data_len
    #                self.flash_hex_info = ("hex", written, src_size)
                f_dest.flush()
                os.fsync(f_dest.fileno())

    def _reset(self, restart=True):
        """Flash micropython filesystem on microbit with main file and initial data."""
        # check args type
        if type(restart) == str: restart = eval(restart)
        # check if 'main.py' for the microbit exists
        self.log.debug(f"reset filesystem of microbit at [{self.port}] ...")
        self.flashed, self.flashing = False, True
        if not os.path.exists(os.path.join(PATH_SRC_MAIN_MICROBIT, "main.py")):
            self.log.error("-> failed - 'main.py' file not found !")
            self.flashing, self.flash_failed = False, True; return
        # generate fs hex code based on runtime and script (for v1 et v2) 
        temp_script = "pass".encode('utf-8')
        hex_code = uflash.embed_fs_uhex(MICROPYTHON_RUNTIME, temp_script)
        # get microbit path
        self.log.debug("find microbit ...")
        microbit_path = uflash.find_microbit()
        if microbit_path is None:
            self.log.error("-> failed - microbit not connected !")
            self.flashing, self.flash_failed = False, True; return

        # flash micropython filesystem on the microbit with the initial script
        self.log.debug("save .hex firmware into 'data' folder and in microbit ...")
        # save firmware
        firmware_path = os.path.join(PATH_DATA, "micropython.hex")
        with open(firmware_path, 'wb') as output:
            output.write(hex_code.encode('ascii'))
        # flash firmware
        microbit_path = os.path.join(microbit_path, "micropython.hex")
        self._save_hex_callback(firmware_path, microbit_path)
        uflash.save_hex(hex_code, microbit_path)

        # reconnect microbit and check if the same is connected
        self.log.debug("reconnect microbit ...")
        self.connecting = True
        self._connect()
        if not self.connected:
            self.log.error("-> failed - microbit to reset was disconnected !")
            self.flashing, self.flash_failed = False, True; return
        # send files to fs
        self.log.debug("send files to filesystem ...")
        time.sleep(0.5)
        try:
            # write files
            for base_path in [PATH_SRC_MAIN_MICROBIT, PATH_DATA_MAIN_MICROBIT]:
                for file_or_dir in os.listdir(base_path):
                    path = os.path.join(base_path, file_or_dir)
                    if os.path.isfile(path):
                        self.microbit.fs_put(path)

        except Exception as err:
            self.log.error(f"-> failed to upload files into fs ! ({type(err).__name__}: {err})")
            self.flashing, self.flash_failed = False, True; return
        else:
            self.log.info("-> microbit filsystem updated with firmware and data")

        # restart the microbit if necessary
        if restart and self.restart_after_flash:
            self._restart()
        self.flashed, self.flashing, self.flash_failed = True, False, False

    def _help_cmds(self):
        """Print all available commands."""
        self.log.info("\nCommands [command (alias): args] :")
        # print commands with alias and args
        for cmds, _, args in self.backend_cmds:
            txt_cmd = f"- {cmds[0]} ({' / '.join([i for i in cmds[1:]])})"
            if args is not None:
                txt_cmd += f": {', '.join([i for i in args])}"
            self.log.info(txt_cmd)

    def _exec_cmd(self, payload=None):
        """Execute self._cmd with self._cmd_data."""
        self._in_exec = True
        if self.connected:
            # try exec src code in microbit
            if payload:
                self.log.debug(f"exec payload '{payload}'")
                self.microbit.exec(payload)
            # try to exec a pyboard cmd or a self function
            else:
                try:
                    for cmds, cmd_funct, _ in self.backend_cmds:
                        if self._cmd in cmds:
                            self.log.debug(f"exec cmd '{self._cmd}' with args {self._cmd_data}")
                            if not callable(cmd_funct):
                                cmd_funct = getattr(self.microbit, cmd_funct)
                            if self._cmd_data is None:
                                self._cmd_return = cmd_funct()
                            else:
                                self._cmd_return = cmd_funct(*self._cmd_data)
                            break
                    else:
                        self._cmd_return = f"-> cmd {self._cmd} not found"
                except Exception as err:
                    self.log.error(f"failed to exec cmd ({type(err).__name__}: {err})")
        self._in_exec = False

    def _wait_not_in_exec(self):
        """Wait last cmd executed."""
        while self._in_exec:
            time.sleep(0.05)

    def _backend(self):
        """Main backend function."""
        while not self._exit:
            # exec cmd
            self._cmd_return = None
            if self._cmd != None:
                if self._cmd in ["h", "help"]:
                    self._help_cmds()
                else:
                    if self.connected:
                        self._wait_not_in_exec()
                        self._exec_cmd()
                    else:
                        if self._cmd in ["c", "connect"]:
                            self.connecting = True

            # try connect
            if self.connecting:
                self._connect()
                self.show_conn_stat()
            # try flash
            elif self.flashing:
                self._reset()
                self.show_conn_stat()

            # reset cmd
            self._cmd = None

            # sleep a little
            time.sleep(0.05)

        # close serial connexion at the end
        self._close()

    def _backend_show_sync(self):
        """Backend for show an image on the microbit screen during connection."""
        need_resync = True
        payload_sync = f"from microbit import display, Image;display.show(Image('{self.image_sync}'))"

        # main sync backend loop
        while not self._exit:
            # sleep a little
            time.sleep(0.1)

            if self.connected:
                if need_resync and self._send_sync_payload:
                    # resync image
                    need_resync = False
                    try:
                        self._wait_not_in_exec()
                        self._exec_cmd(payload_sync)
                    except:
                        pass
                    else:
                        continue
                else:
                    # check if self.port in computer connected ports
                    if self.port in self._list_ports(True):
                        continue
                # disconnect if this stage reached
                self._close()
                self.show_conn_stat()

            else:
                # if microbit was disconnected, resync image needed
                need_resync = True

    def send_cmd(self, cmd, cmd_data=None, wait=True):
        """Send a cmd to execute at the backend."""
        # TODO: cmd_stack ?
        self._cmd = cmd
        self._cmd_data = cmd_data
        if wait:
            while self._cmd != None:
                time.sleep(0.05)
        return self._cmd_return

    def exit(self, wait=True):
        """Quit the backend."""
        self._exit = True
        if wait:
            self.log.debug("wait terminated ...")
            self._th_backend.join()
        self.log.info("Microbit Backend -> exit")


# cli interface
class Cli_Backend():

    """
    Command Line Interface for use the MicroBit_Backend.
    """

    def __init__(self, loglevel="info"):
        # init connect backend
        self.backend = MicroBit_Backend(
            console_log=True,
            logfile_path=os.path.join(PATH_DATA, "cli_backend.log"),
            loglevel=loglevel,
        )
        # start cli
        self.start()

    def start(self):
        # chdir to current dir (for find files to put)
        os.chdir(PATH_SRC_MAIN_MICROBIT)
        print(f"current dir : {PATH_SRC_MAIN_MICROBIT}/")
        # main loop
        while True:
            # get cmd
            cmd = input("\n[cmd]: ")

            if cmd in ["e", "q", "exit", "quit"]:
                # exec cmd
                self.backend.exit()
                break
            
            else:
                # try get cmd_data (args)
                args = cmd.split(" ")
                adds_args = args[1:]
                if adds_args == []:
                    cmd_data = None
                else:
                    cmd_data = adds_args
                    cmd = args[0]

                # exec and get retrn of cmd 
                retrn = self.backend.send_cmd(cmd, cmd_data)
                if retrn != None: print(retrn)


# call Cli_Backend if this program is executed
if __name__ == "__main__":
    Cli_Backend()
