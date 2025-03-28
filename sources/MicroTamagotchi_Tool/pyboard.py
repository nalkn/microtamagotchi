# --- Modified by Killian Nallet (2025) ---
# This file is part of the MicroPython project, http://micropython.org/
#
# The MIT License (MIT)
#
# Copyright (c) 2014-2021 Damien P. George
# Copyright (c) 2017 Paul Sokolovsky
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

"""
pyboard interface

This module provides the Pyboard class, used to communicate with and
control a MicroPython device over a communication channel. Both real
boards and emulated devices (e.g. running in QEMU) are supported.
Various communication channels are supported, including a serial
connection, telnet-style network connection, external process
connection.

Example usage:

    import pyboard
    pyb = pyboard.Pyboard('/dev/ttyACM0')

"""

#NOTE: We choosed (a part of) pyboard.py tool for communicate with the 
# filesystem instead of other tools (like microfs), because it provides
# a lot of useful commands, like exec, copy or stat

import ast
import errno
import os
import struct
import sys
import time

try:
    stdout = sys.stdout.buffer
except AttributeError:
    # Python2 doesn't have buffer attr
    stdout = sys.stdout

import serial
import serial.tools.list_ports


def stdout_write_bytes(b):
    b = b.replace(b"\x04", b"")
    stdout.write(b)
    stdout.flush()


class PyboardError(Exception):
    def convert(self, info):
        if len(self.args) >= 3:
            if b"OSError" in self.args[2] and b"ENOENT" in self.args[2]:
                return OSError(errno.ENOENT, info)

        return self


class Pyboard:

    """Pyboard Interface for Micropython devices."""

    def __init__(
        self, device, baudrate=115200, wait=0, exclusive=True
    ):
        self.in_raw_repl = False
        self.use_raw_paste = True

        # Set options, and exclusive if pyserial supports it
        serial_kwargs = {"baudrate": baudrate, "interCharTimeout": 1}
        if serial.__version__ >= "3.3":
            serial_kwargs["exclusive"] = exclusive

        delayed = False
        for attempt in range(wait + 1):
            try:
                if os.name == "nt":
                    self.serial = serial.Serial(**serial_kwargs)
                    self.serial.port = device
                    portinfo = list(serial.tools.list_ports.grep(device))  # type: ignore
                    if portinfo and portinfo[0].manufacturer != "Microsoft":
                        # ESP8266/ESP32 boards use RTS/CTS for flashing and boot mode selection.
                        # DTR False: to avoid using the reset button will hang the MCU in bootloader mode
                        # RTS False: to prevent pulses on rts on serial.close() that would POWERON_RESET an ESPxx
                        self.serial.dtr = False  # DTR False = gpio0 High = Normal boot
                        self.serial.rts = False  # RTS False = EN High = MCU enabled
                    self.serial.open()
                else:
                    self.serial = serial.Serial(device, **serial_kwargs)
                    self.serial.dtr = False
                    self.serial.rts = False
                break
            except (OSError, IOError):  # Py2 and Py3 have different errors
                if wait == 0:
                    continue
                if attempt == 0:
                    sys.stdout.write("Waiting {} seconds for pyboard ".format(wait))
                    delayed = True
            time.sleep(1)
            sys.stdout.write(".")
            sys.stdout.flush()
        else:
            if delayed:
                print("")
            raise PyboardError("failed to access " + device)
        if delayed:
            print("")

    def close(self):
        self.serial.close()

    def read_until(self, min_num_bytes, ending, timeout=10, data_consumer=None):
        # if data_consumer is used then data is not accumulated and the ending must be 1 byte long
        assert data_consumer is None or len(ending) == 1

        data = self.serial.read(min_num_bytes)
        if data_consumer:
            data_consumer(data)
        timeout_count = 0
        while True:
            if data.endswith(ending):
                break
            elif self.serial.inWaiting() > 0:
                new_data = self.serial.read(1)
                if data_consumer:
                    data_consumer(new_data)
                    data = new_data
                else:
                    data = data + new_data
                timeout_count = 0
            else:
                timeout_count += 1
                if timeout is not None and timeout_count >= 100 * timeout:
                    break
                time.sleep(0.01)
        return data

    def enter_raw_repl(self, timeout=10, soft_reset=True):
        self.serial.write(b"\r\x03\x03")  # ctrl-C twice: interrupt any running program

        # flush input (without relying on serial.flushInput())
        n = self.serial.inWaiting()
        while n > 0:
            self.serial.read(n)
            n = self.serial.inWaiting()
        #self.serial.write(b"\r\x03\x03") # Add ctrl-c

        self.serial.write(b"\r\x01")  # ctrl-A: enter raw REPL

        if soft_reset:
            data = self.read_until(1, b"raw REPL; CTRL-B to exit\r\n>", timeout=timeout)

            if not data.endswith(b"raw REPL; CTRL-B to exit\r\n>"):
                #print(data) ### Line Modified ###
                raise PyboardError("could not enter raw repl")

            self.serial.write(b"\x04")  # ctrl-D: soft reset

            # Waiting for "soft reboot" independently to "raw REPL" (done below)
            # allows boot.py to print, which will show up after "soft reboot"
            # and before "raw REPL".
            data = self.read_until(1, b"soft reboot\r\n")
            if not data.endswith(b"soft reboot\r\n"):
                raise PyboardError("could not enter raw repl")

        data = self.read_until(1, b"raw REPL; CTRL-B to exit\r\n", timeout=3)
        if not data.endswith(b"raw REPL; CTRL-B to exit\r\n"):
            print(data)
            #raise PyboardError("could not enter raw repl")

        self.in_raw_repl = True

    def exit_raw_repl(self):
        self.serial.write(b"\r\x02")  # ctrl-B: enter friendly REPL
        self.in_raw_repl = False

    def follow(self, timeout, data_consumer=None):
        # wait for normal output
        data = self.read_until(1, b"\x04", timeout=timeout, data_consumer=data_consumer)
        if not data.endswith(b"\x04"):
            raise PyboardError("timeout waiting for first EOF reception")
        data = data[:-1]

        # wait for error output
        data_err = self.read_until(1, b"\x04", timeout=timeout)
        if not data_err.endswith(b"\x04"):
            raise PyboardError("timeout waiting for second EOF reception")
        data_err = data_err[:-1]

        # return normal and error output
        return data, data_err

    def raw_paste_write(self, command_bytes):
        # Read initial header, with window size.
        data = self.serial.read(2)
        window_size = struct.unpack("<H", data)[0]
        window_remain = window_size

        # Write out the command_bytes data.
        i = 0
        while i < len(command_bytes):
            while window_remain == 0 or self.serial.inWaiting():
                data = self.serial.read(1)
                if data == b"\x01":
                    # Device indicated that a new window of data can be sent.
                    window_remain += window_size
                elif data == b"\x04":
                    # Device indicated abrupt end.  Acknowledge it and finish.
                    self.serial.write(b"\x04")
                    return
                else:
                    # Unexpected data from device.
                    raise PyboardError("unexpected read during raw paste: {}".format(data))
            # Send out as much data as possible that fits within the allowed window.
            b = command_bytes[i : min(i + window_remain, len(command_bytes))]
            self.serial.write(b)
            window_remain -= len(b)
            i += len(b)

        # Indicate end of data.
        self.serial.write(b"\x04")

        # Wait for device to acknowledge end of data.
        data = self.read_until(1, b"\x04")
        if not data.endswith(b"\x04"):
            raise PyboardError("could not complete raw paste: {}".format(data))

    def exec_raw_no_follow(self, command):
        if isinstance(command, bytes):
            command_bytes = command
        else:
            command_bytes = bytes(command, encoding="utf8")

        # check we have a prompt
        data = self.read_until(1, b">")
        if not data.endswith(b">"):
            raise PyboardError("could not enter raw repl")

        if self.use_raw_paste:
            # Try to enter raw-paste mode.
            self.serial.write(b"\x05A\x01")
            data = self.serial.read(2)
            if data == b"R\x00":
                # Device understood raw-paste command but doesn't support it.
                pass
            elif data == b"R\x01":
                # Device supports raw-paste mode, write out the command using this mode.
                return self.raw_paste_write(command_bytes)
            else:
                # Device doesn't support raw-paste, fall back to normal raw REPL.
                data = self.read_until(1, b"w REPL; CTRL-B to exit\r\n>")
                if not data.endswith(b"w REPL; CTRL-B to exit\r\n>"):
                    print(data)
                    raise PyboardError("could not enter raw repl")
            # Don't try to use raw-paste mode again for this connection.
            self.use_raw_paste = False

        # Write command using standard raw REPL, 256 bytes every 10ms.
        for i in range(0, len(command_bytes), 256):
            self.serial.write(command_bytes[i : min(i + 256, len(command_bytes))])
            time.sleep(0.01)
        self.serial.write(b"\x04")

        # check if we could exec command
        data = self.serial.read(2)
        if data != b"OK":
            raise PyboardError("could not exec command (response: %r)" % data)

    def exec_raw(self, command, timeout=10, data_consumer=None):
        self.exec_raw_no_follow(command)
        return self.follow(timeout, data_consumer)

    def eval(self, expression, parse=False):
        if parse:
            ret = self.exec("print(repr({}))".format(expression))
            ret = ret.strip()
            return ast.literal_eval(ret.decode())
        else:
            ret = self.exec("print({})".format(expression))
            ret = ret.strip()
            return ret

    def exec(self, command, data_consumer=None):
        """Exec some code on theboard and get result."""
        ret, ret_err = self.exec_raw(command, data_consumer=data_consumer)
        if ret_err:
            raise PyboardError("exception", ret, ret_err)
        return ret

    def execfile(self, filename):
        """Execute a computer file on the board."""
        with open(filename, "rb") as f:
            pyfile = f.read()
        return self.exec(pyfile)

    def get_time(self):
        """Get the actual board time."""
        t = str(self.eval("pyb.RTC().datetime()"), encoding="utf8")[1:-1].split(", ")
        return int(t[4]) * 3600 + int(t[5]) * 60 + int(t[6])

    def fs_exists(self, src):
        """Check if a board file exists."""
        try:
            self.exec("import os;os.stat(%s)" % (("'%s'" % src) if src else ""))
            return True
        except PyboardError:
            return False

    def fs_listdir(self): # microbit doesn't support f'os.listdir("{src}")' 
        "Get files list of the board."
        cmd = 'import os;print(os.listdir())'
        str_files = self.exec(cmd).strip().decode()
        return str_files[2:-2].split("', '")

    def fs_platform(self):
        """Get the board platform."""
        cmd = "import sys;print(sys.platform)"
        return self.exec(cmd).strip().decode()

    def fs_version(self):
        """Get the board platform version."""
        cmd = "import os;print(os.uname()[2])"
        str_version = self.exec(cmd).strip().decode()
        return float(str_version[:2])

    def fs_stat(self, src):
        """Get stat of a board file."""
        try:
            self.exec("import os")
            return os.stat_result(self.eval("os.stat(%s)" % ("'%s'" % src), parse=True))
        except PyboardError as e:
            raise e.convert(src)

    def fs_cat(self, src, chunk_size=256):
        """Print all of a file."""
        cmd = (
            "with open('%s') as f:\n while 1:\n"
            "  b=f.read(%u)\n"
            "  if not b:break\n"
            "  print(b,end='')" % (src, chunk_size)
        )
        self.exec(cmd, data_consumer=stdout_write_bytes)

    def fs_readfile(self, src, chunk_size=256):
        buf = bytearray()

        def repr_consumer(b):
            buf.extend(b.replace(b"\x04", b""))

        cmd = (
            "with open('%s', 'rb') as f:"
            "  while 1:\n"
            "  b=f.read(%u)\n"
            "  if not b:break\n"
            "  print(b,end='')" % (src, chunk_size)
        )
        try:
            self.exec(cmd, data_consumer=repr_consumer)
        except PyboardError as e:
            raise e.convert(src)
        return ast.literal_eval(buf.decode())

    def fs_writefile(self, dest, data, chunk_size=256):
        self.exec("f=open('%s','wb')\nw=f.write" % dest)
        while data:
            chunk = data[:chunk_size]
            self.exec("w(" + repr(chunk) + ")")
            data = data[len(chunk) :]
        self.exec("f.close()")

    def fs_cp(self, src, dest, chunk_size=256, progress_callback=None):
        "Copy a board file to another board file."
        if progress_callback:
            src_size = self.fs_stat(src).st_size
            written = 0
        self.exec("fr=open('%s','rb')\nr=fr.read\nfw=open('%s','wb')\nw=fw.write" % (src, dest))
        while True:
            data_len = int(self.exec("d=r(%u)\nw(d)\nprint(len(d))" % chunk_size))
            if not data_len:
                break
            if progress_callback:
                written += data_len
                progress_callback(written, src_size)
        self.exec("fr.close()\nfw.close()")

    def fs_get(self, src, dest=None, chunk_size=256, progress_callback=None):
        """Get a file from the board."""
        if progress_callback:
            src_size = self.fs_stat(src).st_size
            written = 0
        if dest is None:
            dest = os.path.basename(src)
        self.exec("f=open('%s','rb')\nr=f.read" % src)
        with open(dest, "wb") as f:
            while True:
                data = bytearray()
                self.exec("print(r(%u))" % chunk_size, data_consumer=lambda d: data.extend(d))
                assert data.endswith(b"\r\n\x04")
                try:
                    data = ast.literal_eval(str(data[:-3], "ascii"))
                    if not isinstance(data, bytes):
                        raise ValueError("Not bytes")
                except (UnicodeError, ValueError) as e:
                    raise PyboardError("fs_get: Could not interpret received data: %s" % str(e))
                if not data:
                    break
                f.write(data)
                if progress_callback:
                    written += len(data)
                    progress_callback(written, src_size)
        self.exec("f.close()")

    def fs_put(self, src, chunk_size=256, progress_callback=None):
        """Put a computer file in the board."""
        if progress_callback:
            src_size = os.path.getsize(src)
            written = 0
        dest = os.path.basename(src)
        self.exec("f=open('%s','wb')\nw=f.write" % dest)
        with open(src, "rb") as f:
            while True:
                data = f.read(chunk_size)
                if not data:
                    break
                if sys.version_info < (3,):
                    self.exec("w(b" + repr(data) + ")")
                else:
                    self.exec("w(" + repr(data) + ")")
                if progress_callback:
                    written += len(data)
                    progress_callback(written, src_size)
        self.exec("f.close()")

    def fs_rm(self, src):
        """Remove a file in the board."""
        self.exec("import os\nos.remove('%s')" % src)

    def fs_touch(self, src):
        """Create an empty file in the board."""
        self.exec("f=open('%s','a')\nf.close()" % src)

    def reset(self, soft=False):
        """Restart the board."""
        if soft:
            self.serial.write(b"\x04") # soft reset
        else:
            self.exec_raw_no_follow("import machine; machine.reset()")
            self.serial.close()
