#Projet: MicroTamagotchi
#Auteurs: Killian Nallet
#Python: Python >= 3.9
#Coding: utf-8


#--- MICROTAMAGOTCHI - MAIN TOOL ---

# imports
import os
import sys
import json
from backend import MicroBit_Backend

from PIL import Image, ImageTk
import tkinter as tk
from tkinter import filedialog
import customtkinter as ctk
from CTkMessagebox import CTkMessagebox
from threading import Thread


# constants
PATH_PRJ = os.path.dirname(os.path.dirname(os.path.dirname(__file__))) # /
#Thanks to Smashicons for app icon :
# https://www.flaticon.com/free-icon/tamagotchi_1974720?term=tamagotchi&related_id=1974720
PATH_LOG = os.path.join(PATH_PRJ, "data", "microtamagotchi_tool.log")
PATH_ICON = os.path.join(PATH_PRJ, "data", "icon.ico") # data/icon.ico
PATH_SETTINGS = os.path.join(PATH_PRJ, "data", "settings.json") # data/settings.json
PATH_TEMP = os.path.join(PATH_PRJ, "data", "temp") # data/temp/


# tempfiles
if not os.path.exists(PATH_TEMP):
    os.mkdir(PATH_TEMP)

def temp_path(filename):
    return os.path.join(PATH_TEMP, filename) # data/temp/[filename]


# widgets
class CtkConnectStatus(ctk.CTkFrame):

    """
    Connection Status Widget for show actual connection status with a color.
    """

    def __init__(
            self,
            master,
            **kwargs
        ):
        # init frame
        super().__init__(master, **kwargs)
        # vars
        self._tkvar_label = ctk.StringVar()
        self.color = None
        # init widget
        self._setup_widgets()

    def _setup_widgets(self):
        """Create internal widgets."""
        self.size = 20
        self._stat_canvas = ctk.CTkCanvas(
            self, height=self.size+1, width=self.size+1,
            bg=self._apply_appearance_mode(self._fg_color),
            highlightthickness=0
        )
        self._stat_canvas.grid(row=0, column=0, padx=15, pady=3)
        self._label = ctk.CTkLabel(self, textvariable=self._tkvar_label)
        self._label.grid(row=0, column=1, padx=15, pady=3)
        self.state_colors = {
            "connected": "#00FF00",
            "connecting": "#FFFF00",
            "disconnected": "#FF0000"
        }
        self._old_oval = None

    def set_text(self, text):
        """Set the text of the connection status label."""
        self._tkvar_label.set(text)

    def set_color(self, color=None):
        """Set th color of the ConnectStatus."""
        # delete old color oval
        if self._old_oval is not None:
            self._stat_canvas.delete(self._old_oval)
        # display new color
        if color is None:
            color = self.color
        self._old_oval = self._stat_canvas.create_oval(
            0,0, self.size,self.size,
            fill=color,
            outline='',
            width=0
        )
        self.color = color

    def set_from_state(self, state, set_text=True):
        """Set color (and text) from a state."""
        # try get color from state
        color = self.state_colors[state]
        # set text of label
        if set_text:
            self.set_text(state)
        # set color
        self.set_color(color)

    def set_from_vars(self, connected, connecting):
        """Set the colors from variables."""
        # get state from vars
        if connected:
            state = "connected"
        else:
            if connecting:
                state = "connecting"
            else:
                state = "disconnected"
        # set state
        self.set_from_state(state)

class LED:

    """Led object for the Led Matrice Widget."""

    def __init__(self):
        self.value = 0
        self.uptodate = False
        self.cv = None

    def color(self, fr, to, val):
        return '#%02x%02x%02x' % tuple(
            min(max(int(fr[i] + (to[i] - fr[i]) * val / 9), 0), 255)
            for i in range(3))

    def create(self, cv, x, y, size):
        self.cv = cv
        self.inner = cv.create_rectangle(
            x - size[0],
            y - size[1],
            x + size[0],
            y + size[1],
            outline="")
        self.update()

    def set(self, value):
        self.value = max(0, (min(9, value)))
        self.uptodate = False

    def update(self):
        if not self.uptodate:
            self.cv.itemconfig(
                self.inner,
                fill=self.color((10, 15, 10), (255, 30, 30), self.value))
        self.uptodate = True

class CtkLedMatrice(ctk.CTkFrame):

    """
    Led Matrice Widget for create matrices with a color for microbit screen.
    """

    def __init__(
            self,
            master,
            **kwargs
        ):
        # init frame
        super().__init__(master, **kwargs)
        # vars
        self.height = self.width = 350
        self.led_size = self.height/5
        self.led_select = None
        # create wisget
        self._setup_widgets()
        self._create_matrice()
        # tk binds
        self._create_canvas.bind("<Button-1>", self._on_click)
        self._create_canvas.bind("<MouseWheel>", self._on_scroll)
        #NOTE: scroll function isn't supported on linux

    def _setup_widgets(self):
        """Create internal widgets."""
        self._create_canvas = tk.Canvas(
            self, width=self.width, height=self.height,
            bg=self._apply_appearance_mode(self._fg_color),
            highlightthickness=0
        )
        self._create_canvas.pack()

    def _create_matrice(self):
        """Create led matrice."""
        self._matrice = [[None] * 5 for _ in range(5)]
        for x in range(5):
            for y in range(5):
                center = (self.led_size * x + self.led_size // 2,
                          self.led_size * y + self.led_size // 2)
                self._matrice[y][x] = LED()
                self._matrice[y][x].create(
                    self._create_canvas, 
                    * center,
                    (int(self.led_size//2.4), int(self.led_size//2.4))
                )

    def _update_colors(self):
        """Update colors of the led matrice"""
        for x in range(5):
            for y in range(5):
                self._matrice[x][y].update()

    def _get_select(self, event):
        """Get a led selected by the mousepointer."""
        led_x, led_y = int(event.x // self.led_size), int(event.y // self.led_size)
        if 0 <= led_x < 5 and 0 <= led_y < 5:
            return self._matrice[led_y][led_x]
        return None

    def _on_click(self, event):
        """Click event."""
        led = self._get_select(event)
        if led:
            if led.value == 9: led.set(0)
            else: led.set(9)
            self._update_colors()

    def _on_scroll(self, event):
        """Scroll event."""
        led = self._get_select(event)
        if led:
            led.set(led.value + 1 if event.delta > 0 else -1)
            self._update_colors()

    def get(self):
        """Get the self matrice !"""
        return self._matrice
    
    def _strip_values(self, matrice):
        """Strip the matrice if lines of pixel are unused for optimise."""
        
        # split col before
        col_indx_first = 0
        for y in range(5):
            sum = 0
            for x in range(5):
                sum += matrice[x][y].value
            if sum != 0:
                col_indx_first = y
                break
        # split col after
        col_indx_last = 0
        for y in range(4,-1, -1):
            sum = 0
            for x in range(4,-1, -1):
                sum += matrice[x][y].value
            if sum != 0:
                col_indx_last = y
                break
        # check empty (0) matrice
        if col_indx_first == 0 and col_indx_last == 0:
            return None

        # split row before
        row_indx_first = 0
        for x in range(5):
            sum = 0
            for y in range(5):
                sum += matrice[x][y].value
            if sum != 0:
                row_indx_first = x
                break
        # split row after
        row_indx_last = 0
        for x in range(4,-1, -1):
            sum = 0
            for y in range(4,-1, -1):
                sum += matrice[x][y].value
            if sum != 0:
                row_indx_last = x
                break

        # get values matrice
        temp_matrice = [[None for _ in range(5)] for _ in range(5)] #(else, err and modify self._matrice)
        for x in range(5):
            for y in range(5):
                temp_matrice[x][y] = matrice[x][y].value

        # temp lists
        _new_matrice = []
        new_matrice = []

        # split cols
        for row in temp_matrice:
            _new_matrice.append(row[col_indx_first:col_indx_last+1])
        # split rows
        for indx, col in enumerate(_new_matrice):
            if indx >= row_indx_first and indx <= row_indx_last:
                new_matrice.append(col)

        # tests
#        print(col_indx_first,col_indx_last, "tst", row_indx_first, row_indx_last)
#        for row in new_matrice:
#            for led in row:
#                led.set(5)
#                led.update()

        # return
        return new_matrice

    def _matrice_to_list(self, matrice):
        """Return a matrice and size from a list."""
        final_list = []
        size = [len(matrice), len(matrice[0])]
        for row in matrice:
            final_list.extend(row)
        return final_list, size

    def get_values(self):
        """Convert the matrice to an optimized list of values."""
        # get splitted matrice
        matrice = self._strip_values(self._matrice)

        # return matrice
        if matrice is not None:
            return self._matrice_to_list(matrice)


# App
class MicroTamagochi_Tool():

    """
    Micro:Tamagochi Tool.

    A tool created for for create and download images in micro:tamagochi.
    NOTE: This program use a personalized version of pyboard.py tool.
    """

    def __init__(self):
        # init app
        self.root = ctk.CTk()
        self.root.title("Micro:Tamagochi Tool")
        self.root.protocol("WM_DELETE_WINDOW", self.exit)
        ctk.set_appearance_mode("dark")

        # create app widgets
        self.setup_widgets()

        # init connect backend
        self.backend = MicroBit_Backend(
            show_conn_stat=self.show_connection_status,
            logfile_path=PATH_LOG
        )

        # load settings
        self.load_settings()
        self.load_mt_settings()

        # set widget need settings
        self.restart_after_optm.set("Restart" if self.get_setting("restart_after_flash") else "Stay Connected")

        # variables
        self.need_save = False
        self.file_saved = False
        self.file_imported = False
        self.need_load_mt_settings = True

        # center app on the screen make this not resizable
        x_cord = int((self.root.winfo_screenwidth() / 2) - (self.root.winfo_width() / 2))
        y_cord = int((self.root.winfo_screenheight() / 2) - (self.root.winfo_height() / 2))
        self.root.geometry(f"+{x_cord}+{y_cord-20}")
        self.root.resizable(False, False)

        # launch root
        if sys.platform == "linux":
            self.iconpath = ImageTk.PhotoImage(Image.open(PATH_ICON))
            self.root.wm_iconphoto(True, self.iconpath)
        elif sys.platform == "win32":
            self.root.iconbitmap(PATH_ICON)
        self.root.mainloop()

    # --- Interface ---

    def setup_widgets(self):
        """Create all widgets of the application."""
        #left frame
        sidebar_frame = ctk.CTkFrame(self.root, width=80, corner_radius=0)
        sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        
        self.conn_status = CtkConnectStatus(sidebar_frame)
        self.conn_status.grid(row=0, column=0, pady=(10,5))
        
        import_file_button = ctk.CTkButton(
            sidebar_frame, text="Import File", command=self.cmd_import_file_from_computer
        )
        import_file_button.grid(row=1, column=0, padx=20, pady=(10,5))
        
        new_file_button = ctk.CTkButton(sidebar_frame, text="New File", command=None)
        new_file_button.grid(row=2, column=0, padx=20, pady=(10,5))
        
        save_file_button = ctk.CTkButton(sidebar_frame, text="Save File", command=None)
        save_file_button.grid(row=3, column=0, padx=20, pady=(10,5))
        
        self.files_frame = ctk.CTkScrollableFrame(sidebar_frame, width=120)
        self.files_frame.grid(row=4, column=0, padx=20, pady=20)
        #right tabview
        self.tabview = ctk.CTkTabview(self.root, height=400, width=500)
        self.tabview.grid(row=0, column=1, padx=20, pady=(5,10), sticky="nsew")

        #connect
        connect_tab = self.tabview.add("Connect")
        connect_tab.grid_columnconfigure((0,1), weight=1)

        frame_up = ctk.CTkFrame(connect_tab)
        self.var_txt_btn_connect = ctk.StringVar()
        self.var_connect_status = ctk.StringVar()
        self.conn_button = ctk.CTkButton(
            frame_up, 
            textvariable=self.var_txt_btn_connect,
            command=self.cmd_connect_stop_or_disconnect
        )
        self.conn_button.grid(row=0, column=0, padx=10, pady=10)
        
        status_conn_label = ctk.CTkLabel(frame_up, textvariable=self.var_connect_status)
        status_conn_label.grid(row=0, column=1, padx=10, pady=10)
        
        self.connect_status_pbar = ctk.CTkProgressBar(frame_up, width=300)
        self.connect_status_pbar.grid(row=1, column=0, columnspan=2, pady=15)
        frame_up.pack(pady=55)

        frame_down = ctk.CTkFrame(connect_tab)
        self.var_txt_btn_flash = ctk.StringVar()
        self.var_flash_status = ctk.StringVar()
        self.flash_button = ctk.CTkButton(
            frame_down,
            textvariable=self.var_txt_btn_flash,
            command=self.cmd_flash_initial_firmware
        )
        self.flash_button.grid(row=0, column=0, padx=10, pady=10)
        
        status_flash_label = ctk.CTkLabel(frame_down, textvariable=self.var_flash_status)
        status_flash_label.grid(row=0, column=1, padx=10, pady=10)
        
        self.flash_status_pbar = ctk.CTkProgressBar(frame_down, width=300, indeterminate_speed=.4)
        self.flash_status_pbar.grid(row=1, column=0, columnspan=2, pady=15)
        frame_down.pack()

        #create
        create_tab = self.tabview.add("Create")
        
        self.create_leds = CtkLedMatrice(create_tab)
        self.create_leds.grid(row=0, column=0, pady=10, columnspan=2)
        
        ctk.CTkLabel(create_tab, text="Figure Name").grid(row=1, column=0, padx=10)
        self.entry_name_figure = ctk.CTkEntry(create_tab)
        self.entry_name_figure.grid(row=2, column=0, padx=10)
        
        self.btn_add_perso = ctk.CTkButton(
            create_tab, 
            text = "Add Figure",
            command = self.add_figure_frame
        )
        self.btn_add_perso.grid(row=1, column=1, padx=10, rowspan=2)
        create_tab.columnconfigure((0,1), weight=1)

        #TODO: pouvoir ajouter cette image dans une scrollableframe (qui peut en contenir plusieures)

        #settings/infos
        settings_tab = self.tabview.add("Settings")
        settings_tab.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(settings_tab, text="After Flash :").pack(pady=(10,5))
        self.restart_after_optm = ctk.CTkOptionMenu(
            settings_tab, values=["Restart", "Stay Connected"],
            command = self.cmd_optm_restart_after
        )
        self.restart_after_optm.pack(pady=(5,10))
        
        ctk.CTkLabel(settings_tab, text="Figure selected :").pack(pady=(10,5))
        self.figure_selected_optm = ctk.CTkOptionMenu(
            settings_tab,
            command = self.cmd_optm_figure_selected
        )
        self.figure_selected_optm.pack(pady=(5,10))

        self.conn_port = ctk.CTkLabel(settings_tab)
        self.conn_port.pack(pady=10)

        #TODO: choisir la chemin d'accès au simulateur tests (et pouvoir l'utiliser dans l'app)

    def set_tab_settings(self, connected=False):
        """Set the widgets in the settings tab."""
        #TODO: a finir

        # set figures list and selected
        if not connected:
            self.figure_selected_optm.configure(state="disabled")
            self.figures_list = ["None"]
        else:
            self.figure_selected_optm.configure(state="normal")
            self.figures_list = ["None"]

        self.figure_selected_optm.configure(values=self.figures_list)
        self.figure_selected_optm.set(self.figures_list[0])

        # show conn port
        self.conn_port.configure(text=f"Connected Port : {self.backend.port}")

    def cmd_optm_figure_selected(self):
        """Set the selected figure in MicroTamagotchi Settings."""
        #TODO: get microbit settings
        #TODO: update settings in microbit

    def show_connection_status(
            self, 
            connected, connecting, connect_failed, 
            flashed, flashing, flash_failed,
            flash_hex_info, *args
        ):
        """Show connect and flash status."""
        pbar_c, conn_status = self.connect_status_pbar, self.conn_status
        pbar_f = self.flash_status_pbar
        conn_btn_state = flash_btn_state = "normal"
        # connect status
        if connected:
            txt_btn, status = "Disconnect", "Connected !"
            pbar_c.stop()
            pbar_c.configure(mode="determinate")
            pbar_c.set(1)
            if self.need_load_mt_settings:
                Thread(target=self.load_mt_settings).start()
                self.need_load_mt_settings = False
            self.btn_add_perso.configure(state="normal")
        elif connecting:
            txt_btn, status = "Stop", "Connecting ..."
            pbar_c.configure(mode="indeterminnate")
            pbar_c.set(0)
            pbar_c.start()
            flash_btn_state = "disabled"
        else:
            txt_btn = "Connect"
            if connect_failed: status = "Connect Failed"
            else: status = "Disconnected"
            pbar_c.stop()
            pbar_c.configure(mode="determinate")
            pbar_c.set(0)
            self.need_load_mt_settings = True
            self.btn_add_perso.configure(state="disabled")
        # flash status
        if flashed:
            flash_txt_btn, flash_status = "Re-Flash", "Flashed !"
            pbar_f.stop()
            pbar_f.configure(mode="determinate")
            pbar_f.set(1)
        elif flashing: # and connected
            flash_txt_btn, flash_status = "Stop", "Flashing ..."
            conn_btn_state = flash_btn_state= "disabled"
            pbar_f.configure(mode="indeterminnate")
            pbar_f.set(0)
            pbar_f.start()
#            f_ty, wri, tot = flash_hex_info
#            if f_ty is None:
#                pbar_f.configure(mode="indeterminnate")
#                pbar_f.set(0)
#                pbar_f.start()
#            elif f_ty == "hex":
#                pbar_f.configure(mode="indeterminnate")
#                pbar_f.set((tot - wri) // tot)
#            elif f_ty == "files":
#                pass
        else:
            flash_txt_btn = "Flash Project"
            if flash_failed: flash_status = "Flash Failed"
            else: flash_status = "Not Flashed"
            pbar_f.stop()
            pbar_f.configure(mode="determinate")
            pbar_f.set(0)
        # set windgets
        self.conn_button.configure(state=conn_btn_state)
        conn_status.set_from_vars(connected, connecting)
        self.var_txt_btn_connect.set(txt_btn)
        self.var_connect_status.set("Status : "+status)
        self.flash_button.configure(state=flash_btn_state)
        self.var_txt_btn_flash.set(flash_txt_btn)
        self.var_flash_status.set("Status : "+flash_status)

    # --- Settings ---

    def load_settings(self):
        """Load settings form a json file."""
        default_settings = {
            "restart_after_flash": False,
            "microbit_figure": None
        }
        self.settings = default_settings
        self.settingsfile_found = True
        try:
            # search existing settings file
            if os.path.exists(PATH_SETTINGS):
                with open(PATH_SETTINGS, "r") as r_stt:
                    self.settings = json.load(r_stt)
            # else, write default data into
            else:
                self.save_settings(default_settings)
        except:
            self.settingsfile_found = False
            self.backend.log.error("can't load/save settings in/from a file !")

    def save_settings(self, settings=None):
        """Save settings in a json file."""
        if not settings:
            settings = self.settings
        with open(PATH_SETTINGS, "w") as w_stt:
            json.dump(self.settings, w_stt)

    def get_setting(self, setting:str):
        """Get a setting value."""
        return self.settings[setting]

    def set_setting(self, setting:str, val, save=True):
        """Set setting to a value."""
        self.settings[setting] = val
        if save and self.settingsfile_found: 
            self.save_settings()

    def load_mt_settings(self):
        """Load settings from the MicroTamagotchi."""
        settfile = 'settings.mtd'
        tempfile = temp_path(settfile)
        # get data in a tempfile
        self.backend.send_cmd(f"get", (settfile, tempfile))
        try:
            with open(tempfile, "r") as rf:
                # actualize mt_settings
                self.mt_settings = eval(rf.read())
            # remove tempfile
            os.remove(tempfile)
        except Exception as e:
            self.mt_settings = None

        self.set_tab_settings()

    def save_mt_settings(self):
        """Save settings in MicroTamagotchi."""
        settfile = 'settings.mtd'
        tempfile = temp_path(settfile)

        if self.mt_settings is not None:
            # write data
            with open(tempfile, "w") as rw:
                rw.write(repr(self.mt_settings))
            # rm temp file
            self.backend.send_cmd(f"put", (tempfile,))
            os.remove(tempfile)

    # --- Other ---

    def add_figure_to_mt(self, name, figure, size):
        """Insert a figure in microTamagotchi."""
        # create data
        fig_data = {
            "size": size,
            "delay": 200,
            "data": figure
        }
        imgfile = 'images.mtd'
        tempfile = temp_path(imgfile)

        # get data
        self.backend.send_cmd(f"get", (imgfile, tempfile))
        with open(tempfile, "r") as rf:
            data = eval(rf.read())
        data[name] = fig_data

        # write data
        with open(tempfile, "w") as rw:
            rw.write(repr(data))

        # rm temp file
        self.backend.send_cmd(f"put", (tempfile,))
        os.remove(tempfile)


    # --- Commands ---

    def cmd_connect_stop_or_disconnect(self):
        """Connect or disconnect the microbit"""
        if self.backend.connected:
            self.backend.send_cmd("restart")
        else:
            self.backend.connecting = not self.backend.connecting
        self.backend.show_conn_stat()

    def cmd_flash_initial_firmware(self):
        """Flash the initial firmware of the microtamagotchi with data."""
        msg_check = "Flash a firmware will erase all data ! \
        Do you want to flash the project in micro:bit ?"
        if CTkMessagebox(
            title="Warning !", message=msg_check, icon="warning", 
            option_1="Cancel", option_2="No", option_3="Yes"
        ).get() == "Yes":
            self.backend.flashing = True
        self.backend.show_conn_stat()

    def add_figure_frame(self):
        """Add a frame in list of frames."""
        values = self.create_leds.get_values()
        name = self.entry_name_figure.get()
        if values is not None and name != None:
            figure, size = values
            self.add_figure_to_mt(name, figure, size)

    def cmd_optm_restart_after(self, value):
        """Set the parameter 'restart_after_flash'."""
        restart =  value == "Restart"
        self.set_setting(
            "restart_after_flash",
            restart
        )   
        self.backend.restart_after_flash = restart

    def cmd_import_file_from_computer(self):
        """Choose a data file to import."""
        file = filedialog.askopenfilename(
            filetypes=[('Data', '*.json'), ('All Files', '*.*')]
        )
        if os.path.exists(file):
            pass

    def cmd_export_file_in_computer(self):
        """Export a file in computer."""
        pass

    def cmd_import_file_from_microbit(self):
        """Import a file from microbit."""
        pass

    def cmd_export_file_in_microbit(self):
        """Export a file in microbit."""
        pass

    # --- Other ---

    def save_work(self):
        """Save ... in a .json file."""
        msg_save = "Do you want to save your work in a file ?"
        if self.need_save:
            if CTkMessagebox(
                title="Save ?", message=msg_save, icon="question", 
                option_2="No", option_3="Yes"
            ).get() == "Yes":
                pass

    def exit(self):
        """Quit application and close the serial."""
        # save work in a file if needed
        if self.need_save:
            self.save_work()
        # ask quit app
        msg_quit = "Do you want to close this program ?"
        if CTkMessagebox(
            title="Exit ?", message=msg_quit, icon="question", 
            option_1="Cancel", option_2="No", option_3="Yes"
        ).get() == "Yes":
            self.backend.send_cmd("restart")
            self.backend.exit()
            self.root.destroy()


# launch app if this file is launched
if __name__ == "__main__":
    MicroTamagochi_Tool()
