#Projet: MicroTamagotchi
#Auteurs: Killian Nallet
#Python: Python >= 3.9
#Coding: utf-8


#--- MICROTAMAGOTCHI - MAIN TOOL ---

# imports
import os
import sys
import json
import time
from backend import MicroBit_Backend

from PIL import Image, ImageDraw, ImageTk
import tkinter as tk
from tkinter import filedialog # python >= 3.9
import customtkinter as ctk
from CTkMessagebox import CTkMessagebox
from threading import Thread



# constants
PATH_PRJ = os.path.dirname(os.path.dirname(os.path.dirname(__file__))) # /
# Thanks to Smashicons for app icon :
# https://www.flaticon.com/free-icon/tamagotchi_1974720?term=tamagotchi&related_id=1974720
PATH_LOG = os.path.join(PATH_PRJ, "data", "microtamagotchi_tool.log")
PATH_ICON_APP = os.path.join(PATH_PRJ, "data", "icon.ico") # data/icon.ico
PATH_ICON_DELETE = os.path.join(PATH_PRJ, "data", "delete.ico") # data/delete.ico
PATH_SETTINGS = os.path.join(PATH_PRJ, "data", "microtamagotchi_settings.json") # data/settings.json
PATH_TEMP = os.path.join(PATH_PRJ, "data", "temp") # data/temp/


# tempfiles
def temp_path(filename:str) -> str:
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
        ) -> None:
        # init frame
        super().__init__(master, **kwargs)
        # vars
        self._tkvar_label = ctk.StringVar()
        self.color = None
        # init widget
        self._setup_widgets()

    def _setup_widgets(self) -> None:
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
            "disconnected": "#FF0000",
            "flashing": "#FFA500"
        }
        self._old_oval = None

    def set_text(self, text:str) -> None:
        """Set the text of the connection status label."""
        self._tkvar_label.set(text)

    def set_color(self, color:str=None) -> None:
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

    def set_from_state(self, state:str, set_text=True) -> None:
        """Set color (and text) from a state."""
        # try get color from state
        color = self.state_colors[state]
        # set text of label
        if set_text:
            self.set_text(state)
        # set color
        self.set_color(color)

    def set_from_vars(self, connected:bool, connecting:bool, flashing=False):
        """Set the colors from variables."""
        # get state from vars
        if flashing:
            state = "flashing"
        elif connected:
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
    # code inspired by microTk

    @staticmethod
    def color(val:int, fr=(10, 15, 10), to=(255, 30, 30)) -> str:
        if val == -1:
            return '#808080' # grey
        return '#%02x%02x%02x' % tuple(
            min(max(int(fr[i] + (to[i] - fr[i]) * val / 9), 0), 255)
            for i in range(3))

    def __init__(self) -> None:
        self.value = 0
        self.uptodate = False
        self.cv = None

    def create(self, cv, x:int, y:int, size:tuple) -> None:
        self.cv = cv
        self.inner = cv.create_rectangle(
            x - size[0],
            y - size[1],
            x + size[0],
            y + size[1],
            outline=""
        )
        self.update()

    def set(self, value:int) -> None:
        self.value = max(-1, (min(9, value)))
        self.uptodate = False

    def update(self) -> None:
        if not self.uptodate:
            self.cv.itemconfig(
                self.inner,
                fill=self.color(self.value))
        self.uptodate = True

class CtkLedMatrice(ctk.CTkFrame):

    """
    Led Matrice Widget for create matrices with a color for microbit screen.
    """

    def __init__(self, master, **kwargs) -> None:
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
        self.dclick_flag = False
        self._create_canvas.bind("<Button-1>", self._on_click)
        self._create_canvas.bind("<Double-1>", self._on_dclick)
        self._create_canvas.bind("<MouseWheel>", self._on_scroll)
        #NOTE: scroll function is not supported on linux

    def _setup_widgets(self) -> None:
        """Create internal widgets."""
        self._create_canvas = tk.Canvas(
            self, width=self.width, height=self.height,
            bg=self._apply_appearance_mode(self._fg_color),
            highlightthickness=0
        )
        self._create_canvas.pack()

    def _create_matrice(self) -> None:
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

    def _get_select(self, event) -> None:
        """Get the led selected by the mousepointer."""
        led_x, led_y = int(event.x // self.led_size), int(event.y // self.led_size)
        if 0 <= led_x < 5 and 0 <= led_y < 5:
            return self._matrice[led_y][led_x]
        return None

    def _on_click(self, event) -> None:
        """Click event."""
        self.dled = None
        led = self._get_select(event)
        self.after(200, self._click_action, led)

    def _on_dclick(self, event) -> None:
        """Double Click event."""
        self.dled = self._get_select(event)
        self.dclick_flag = True

    def _click_action(self, led:LED) -> None:
        """Click action."""
        # code inspired by :
        # https://stackoverflow.com/questions/27262580/tkinter-binding-mouse-double-click
        if self.dled != led:
            self.dclick_flag = False
        if led:
            if self.dclick_flag:
                if led.value == -1: led.set(0)
                else: 
                    led.set(-1)
                led.update()
                self.dclick_flag = False
            else:
                if led.value == 9: led.set(0)
                else: led.set(9)
                led.update()

    def _on_scroll(self, event) -> None:
        """Scroll event."""
        led = self._get_select(event)
        if led:
            led.set(led.value + 1 if event.delta > 0 else led.value - 1)
            led.update()
    
    def get_matrice_values(self) -> list[list]:
        """Get a copy of the matrice, leds remplaced by their values."""
        temp_matrice = [[None for _ in range(5)] for _ in range(5)] #(else, err and modify self._matrice)
        for x in range(5):
            for y in range(5):
                temp_matrice[x][y] = self._matrice[x][y].value
        return temp_matrice

    def _strip_values(self, matrice:list[list]) -> list[list]:
        """Strip the matrice if lines of pixel are unused for optimise data."""
        # split col before
        col_indx_first = 0
        for y in range(5):
            sum = 0
            for x in range(5):
                sum += matrice[x][y]
            if sum != 0:
                col_indx_first = y
                break
        # split col after
        col_indx_last = 0
        for y in range(4,-1, -1):
            sum = 0
            for x in range(4,-1, -1):
                sum += matrice[x][y]
            if sum != 0:
                col_indx_last = y
                break
        # check empty (0 value) matrice
        if col_indx_first == 0 and col_indx_last == 0:
            return None

        # split row before
        row_indx_first = 0
        for x in range(5):
            sum = 0
            for y in range(5):
                sum += matrice[x][y]
            if sum != 0:
                row_indx_first = x
                break
        # split row after
        row_indx_last = 0
        for x in range(4,-1, -1):
            sum = 0
            for y in range(4,-1, -1):
                sum += matrice[x][y]
            if sum != 0:
                row_indx_last = x
                break

        # temp lists
        _new_matrice = []
        new_matrice = []

        # split cols
        for row in matrice:
            _new_matrice.append(row[col_indx_first:col_indx_last+1])
        # split rows
        for indx, col in enumerate(_new_matrice):
            if indx >= row_indx_first and indx <= row_indx_last:
                new_matrice.append(col)

        # test for print splitted matrice
#        print(col_indx_first, col_indx_last, "tst", row_indx_first, row_indx_last)
#        for row in new_matrice:
#            for led in row:
#                led.set(5); led.update()

        # return
        return new_matrice

    def _matrice_to_list(self, matrice:list[list]) -> list:
        """Return a list and size from a matrice."""
        size = [len(matrice[0]), len(matrice)]
        matrice_list = []
        for row in matrice:
            matrice_list.extend(row)
        return [matrice_list, size]

    def get_frame(self) -> list | None:
        """Convert the matrice to an optimized list of values."""
        # get values of the matrice
        matrice = self.get_matrice_values()

        # get stripped matrice
        matrice = self._strip_values(matrice)

        # return matrice
        if matrice is not None:
            return self._matrice_to_list(matrice)

    def clear_values(self) -> None:
        """Clear the matrice."""
        for x in range(5):
            for y in range(5):
                led = self._matrice[x][y]
                led.set(0)
                led.update()


class CharacterScrollableFrame(ctk.CTkScrollableFrame):

    """ScrollableFrame with miniatures for add a Character in the MicroTamagotchi."""
    # code inspired by https://customtkinter.tomschimansky.com/tutorial/scrollable-frames/

    def __init__(self, master, width=120) -> None:
        super().__init__(master, width, label_text="Frames")
        self.del_icon = ctk.CTkImage(Image.open(PATH_ICON_DELETE))
        self.nb_frames = 0
        self.miniatures_frames = []
        self.character_frames = {}

    def suppr(self, miniature_frame, id_data:int) -> None:
        """Delete a frame of the CharacterScrollableFrame and his data."""
        miniature_frame.destroy()
        self.character_frames.pop(id_data)

    def add(self, matrice:list, character_frame:list) -> None:
        """Add a frame to the CharacterScrollableFrame."""
        miniature_size = 40
        # create miniature
        size = (miniature_size, miniature_size)
        miniature = Image.new('RGBA', size)
        draw = ImageDraw.Draw(miniature)
        led_size = int(miniature_size // 5)
        for x in range(5):
            for y in range(5):
                st, nd = y*led_size, x*led_size
                draw.rectangle(
                    [(st,nd), (st+led_size,nd+led_size)], 
                    fill=LED.color(matrice[x][y])
                )
        ctk_miniature = ctk.CTkImage(miniature, size=size)
        # create miniature_frame
        miniature_frame = ctk.CTkFrame(self)
        miniature_frame.grid(row=self.nb_frames, column=0, padx=10, pady=(10, 0), sticky="w")
        id = self.nb_frames
        # display miniature and del button widgets
        ctk.CTkLabel(
            miniature_frame, 
            text="",
            image=ctk_miniature
        ).grid(row=0, column=0, padx=(10,5), pady=10)
        ctk.CTkButton(
            miniature_frame,
            width=30,
            text="",
            image=self.del_icon,
            command=lambda: self.suppr(miniature_frame, id)
        ).grid(row=0, column=1, padx=(5,10), pady=10)
        # append value
        self.miniatures_frames.append(miniature_frame) # for destroy all
        self.character_frames[id] = character_frame
        self.nb_frames += 1

    def clear(self) -> None:
        """Clear the CharacterScrollableFrame and all data."""
        # delete all frames
        for frame in self.miniatures_frames:
            frame.destroy()
        # delete all data
        self.nb_frames = 0
        self.miniatures_frames = []
        self.character_frames = {}

    def get(self) -> list:
        """Get all data frames of the CharacterScrollableFrame."""
        data = []
        for character_frame in self.character_frames.values():
            data.append(character_frame)
        return data


# App
class MicroTamagochi_Tool():

    """
    Micro:Tamagochi Tool.

    A tool created for for create and download images in micro:tamagochi.
    NOTE: This program use a personalized version of pyboard.py tool.
    """

    jsonfile_uuid = "ba1f4ccc-efc6-4766-8111-30408e2feb5d" # created with https://www.uuidgenerator.net/

    def __init__(self) -> None:
        # init app
        self.root = ctk.CTk()
        self.root.title("MicroTamagochi Tool")
        self.root.protocol("WM_DELETE_WINDOW", self.exit)
        ctk.set_appearance_mode("dark")

        # create app widgets
        self.mt_settings = None
        self.setup_widgets()

        # init connect backend
        self.backend = MicroBit_Backend(
            show_conn_stat=self.show_connection_status,
            logfile_path=PATH_LOG
        )

        # create temp dir
        try:
            if not os.path.exists(PATH_TEMP):
                os.mkdir(PATH_TEMP)
        except:
            self.backend.log.error(f"cannot create temp directory ({PATH_TEMP}) !")

        # load settings
        self.load_settings()

        # set widget need settings
        self.restart_after_optm.set("Restart" if self.get_setting("restart_after_flash") else "Stay Connected")

        # variables
        self.need_save = False
        self.need_load_mt_settings = True

        # center app on the screen make this not resizable
        x_cord = int((self.root.winfo_screenwidth() / 2) - (self.root.winfo_width() / 2))
        y_cord = int((self.root.winfo_screenheight() / 2) - (self.root.winfo_height() / 2))
        self.root.geometry(f"+{x_cord}+{y_cord-20}")
        self.root.resizable(False, False)

        # launch root
        if sys.platform == "linux":
            self.iconpath = ImageTk.PhotoImage(Image.open(PATH_ICON_APP))
            self.root.wm_iconphoto(True, self.iconpath)
        elif sys.platform == "win32":
            self.root.iconbitmap(PATH_ICON_APP)
        self.root.mainloop()

    # --- Interface ---

    def setup_widgets(self) -> None:
        """Create all widgets of the application."""
        #left frame
        sidebar_frame = ctk.CTkFrame(self.root, width=80, corner_radius=0)
        sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        
        self.conn_status = CtkConnectStatus(sidebar_frame)
        self.conn_status.grid(row=0, column=0, pady=(10,5))
        
        self.import_file_btn = ctk.CTkButton(
            sidebar_frame, text="Import Conf", command=self.cmd_import_conf
        )
        self.import_file_btn.grid(row=1, column=0, padx=20, pady=(10,5))
        
        self.save_file_btn = ctk.CTkButton(sidebar_frame, text="Save Conf", command=self.cmd_save_conf)
        self.save_file_btn.grid(row=2, column=0, padx=20, pady=(10,5))

        self.create_character_frames = CharacterScrollableFrame(sidebar_frame)
        self.create_character_frames.grid(row=3, column=0, padx=20, pady=20)
        
        #right tabview
        self.tabv = ctk.CTkTabview(self.root, height=400, width=500)
        self.tabv.grid(row=0, column=1, padx=20, pady=(5,10), sticky="nsew")

        #connect
        connect_tab = self.tabv.add("Connect")
        connect_tab.grid_columnconfigure((0,1), weight=1)

        frame_up = ctk.CTkFrame(connect_tab)
        self.tkvar_txt_btn_connect = ctk.StringVar()
        self.tkvar_connect_status = ctk.StringVar()
        self.conn_btn = ctk.CTkButton(
            frame_up, 
            textvariable=self.tkvar_txt_btn_connect,
            command=self.cmd_connect_stop_or_disconnect
        )
        self.conn_btn.grid(row=0, column=0, padx=10, pady=10)
        
        status_conn_lb = ctk.CTkLabel(frame_up, textvariable=self.tkvar_connect_status)
        status_conn_lb.grid(row=0, column=1, padx=10, pady=10)
        
        self.connect_status_pbar = ctk.CTkProgressBar(frame_up, width=300)
        self.connect_status_pbar.grid(row=1, column=0, columnspan=2, pady=15)
        frame_up.pack(pady=55)

        frame_down = ctk.CTkFrame(connect_tab)
        self.tkvar_txt_btn_flash = ctk.StringVar()
        self.tkvar_flash_status = ctk.StringVar()
        self.flash_btn = ctk.CTkButton(
            frame_down,
            textvariable=self.tkvar_txt_btn_flash,
            command=self.cmd_flash_initial_firmware
        )
        self.flash_btn.grid(row=0, column=0, padx=10, pady=10)
        
        status_flash_lb = ctk.CTkLabel(frame_down, textvariable=self.tkvar_flash_status)
        status_flash_lb.grid(row=0, column=1, padx=10, pady=10)
        
        self.flash_status_pbar = ctk.CTkProgressBar(frame_down, width=300, indeterminate_speed=.4)
        self.flash_status_pbar.grid(row=1, column=0, columnspan=2, pady=15)
        frame_down.pack()

        #create
        create_tab = self.tabv.add("Create")
        create_tab.grid_columnconfigure((0,1), weight=1)
        create_tab.grid_rowconfigure(0, weight=1)
        
        self.create_leds = CtkLedMatrice(create_tab)
        self.create_leds.grid(row=0, column=0, pady=50, rowspan=5)

        frame_right = ctk.CTkFrame(create_tab)
        add_frame_btn = ctk.CTkButton(
            frame_right, text = "Add Frame",
            command = self.cmd_add_frame_to_character
        )
        add_frame_btn.pack(pady=(10,5))

        clear_character_btn = ctk.CTkButton(
            frame_right, text="Clear Frames", 
            command=self.create_character_frames.clear
        )
        clear_character_btn.pack(pady=(10,5))

        ctk.CTkLabel(frame_right, text="Character Name").pack(pady=(40,0))
        self.character_name_entry = ctk.CTkEntry(frame_right)
        self.character_name_entry.pack(pady=5)
        
        self.add_character_btn = ctk.CTkButton(
            frame_right, text="Add Character", 
            command=self.cmd_add_character
        )
        self.add_character_btn.pack(pady=(10,5))
        frame_right.grid(row=0, column=1)
        
        #settings/infos
        settings_tab = self.tabv.add("Settings")
        settings_tab.grid_columnconfigure((0,1), weight=1)

        ctk.CTkLabel(settings_tab, text="After Flash :").pack(pady=(10,5))
        self.restart_after_optm = ctk.CTkOptionMenu(
            settings_tab, values=["Restart", "Stay Connected"],
            command = self.cmd_optm_restart_after
        )
        self.restart_after_optm.pack(pady=(5,10))
        
        ctk.CTkLabel(settings_tab, text="Character selected :").pack(pady=(10,5))
        self.character_selected_optm = ctk.CTkOptionMenu(
            settings_tab,
            command = self.cmd_optm_character_selected
        )
        self.character_selected_optm.pack(pady=(5,10))

        self.conn_port_lb = ctk.CTkLabel(settings_tab, text="Connected Port : None")
        self.conn_port_lb.pack(pady=10)

        #TODO: choisir la chemin d'accès au simulateur tests (et pouvoir l'utiliser dans l'app)

    def show_connection_status(
            self, 
            connected, connecting, connect_failed, 
            flashed, flashing, flash_failed,
            flash_hex_info, 
            *args
        ) -> None:
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
            self.add_character_btn.configure(state="normal")
            self.import_file_btn.configure(state="normal")
            self.save_file_btn.configure(state="normal")
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
            self.mt_settings = None
            self.add_character_btn.configure(state="disabled")
            self.import_file_btn.configure(state="disabled")
            self.save_file_btn.configure(state="disabled")
            self.set_tab_settings()
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
        self.conn_btn.configure(state=conn_btn_state)
        conn_status.set_from_vars(connected, connecting, flashing)
        self.tkvar_txt_btn_connect.set(txt_btn)
        self.tkvar_connect_status.set("Status : "+status)
        self.flash_btn.configure(state=flash_btn_state)
        self.tkvar_txt_btn_flash.set(flash_txt_btn)
        self.tkvar_flash_status.set("Status : "+flash_status)

    def set_tab_settings(self) -> None:
        """Set the widgets in the settings tab."""
        # set characters list and selected
        if self.mt_settings is None:
            self.character_selected_optm.configure(state="disabled")
            characters_list = ["None"]
            character_selected = characters_list[0]
        else:
            self.character_selected_optm.configure(state="normal")
            characters_list = self.mt_settings["characters_list"]
            character_selected = self.mt_settings["character"]

        # show selected character
        self.character_selected_optm.configure(values=characters_list)
        self.character_selected_optm.set(character_selected)

        # show conn port
        try:
            if not self.backend.connected: raise
            conn_port_lb = self.backend.port
        except:
            conn_port_lb = None
        self.conn_port_lb.configure(text=f"Connected Port : {conn_port_lb}")

    # --- Settings ---

    def load_settings(self) -> None:
        """Load settings form a json file."""
        default_settings = {
            "restart_after_flash": False
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

    def save_settings(self, settings=None) -> None:
        """Save settings in a json file."""
        if not settings:
            settings = self.settings
        with open(PATH_SETTINGS, "w") as w_stt:
            json.dump(self.settings, w_stt)

    def get_setting(self, setting:str) -> dict:
        """Get a setting value."""
        return self.settings[setting]

    def set_setting(self, setting:str, val:str, save=True) -> None:
        """Set setting to a value."""
        self.settings[setting] = val
        if save and self.settingsfile_found: 
            self.save_settings()

    def read_mt_file(self, file, remove=True) -> dict:
        """Get a mt file and read his content."""
        # create tempfile
        tempfile = temp_path(file)
        # get file
        self.backend.send_cmd("get", (file, tempfile)) # get the file at the path tempfile
        with open(tempfile, "r") as rf:
            # load data
            data = eval(rf.read())
        # remove tempfile
        if remove:
            os.remove(tempfile)
        # return data
        return data

    def write_mt_file(self, file, data, remove=True) -> None:
        """Write data in a file and put this."""
        # create tempfile
        tempfile = temp_path(file)
        # write data in a tempfile
        with open(tempfile, "w") as rw:
            rw.write(repr(data))
        # send tempfile
        self.backend.send_cmd(f"put", (tempfile,)) # put the modified tempfile (with data)
        # remove temp file
        if remove:
            os.remove(tempfile)

    def load_mt_settings(self, wait=0.5) -> None:
        """Load settings from the MicroTamagotchi."""
        # setting file
        settfile = 'settings.mtd'
        # sleep a little (wait connected cmd executed)
        st = time.time()
        while time.time() - st < wait: time.sleep(0.05)
        # get data in a tempfile
        try:
            # get mt settings data
            self.mt_settings = self.read_mt_file(settfile)
            # actualize save var
            self.need_save = True
        except:
            self.mt_settings = None
        # actualize settings tab widgets
        self.set_tab_settings()

    def save_mt_settings(self) -> bool:
        """Save settings in MicroTamagotchi."""
        # setting file
        settfile = 'settings.mtd'
        # try to get settings
        if self.mt_settings is not None:
            try:
                # save mt settings
                self.write_mt_file(settfile, self.mt_settings)
            except:
                return False
            else:
                return True

    # --- Other ---

    def add_character_to_mt(self, name:str, new_character:list) -> None:
        """Insert a character in microTamagotchi."""
        # create data
        fig_data = {
            "delay": 300, #TODO: add delay btn
            "data": new_character
        }
        imgfile = 'images.mtd'

        #add new character
        try:
            # read and modify data
            data_imgs = self.read_mt_file(imgfile)
            data_imgs[name] = fig_data # erase character with same name
            # write data
            self.write_mt_file(imgfile, data_imgs)

            # save new character name in settings
            if name not in self.mt_settings["characters_list"]:
                self.mt_settings["characters_list"].append(name) # check character name
            self.save_mt_settings()
            self.need_save = True
        except:
            return False
        else:
            return True
    
    def save_configurations(self) -> bool:
        """Save MicroTamagotchi configuration in a .json file."""
        action = CTkMessagebox(
            title="Save Data & Exit ?", icon="question", 
            message="Do you want to save actual MicroTamagotchi configurations in a file ?",
            option_1="Cancel", option_2="No", option_3="Yes"
        ).get()
        if action == "Yes":
            self.cmd_save_conf()
            return True
        elif action == "No":
            return True
        else:
            return False


    # --- Widgets Commands ---

    def cmd_optm_character_selected(self, character:list) -> None:
        """Set the selected character in MicroTamagotchi Settings."""
        # change setting
        self.mt_settings["character"] = character

        # save settingg
        if self.save_mt_settings():
            self.create_leds.clear_values()
            CTkMessagebox(
                title="Info", icon="info",
                message=f"Character '{character}' is selected on the MicroTamagotchi !"
            )
            self.need_save = True
        else:
            CTkMessagebox(
                title="Warning !", icon="warning",
                message=f"Selection of Character '{character}' on the MicroTamagotchi failed !" 
            )

    def cmd_connect_stop_or_disconnect(self) -> None:
        """Connect or disconnect the microbit"""
        if self.backend.connected:
            self.backend.send_cmd("restart")
        else:
            self.backend.connecting = not self.backend.connecting
        self.backend.show_conn_stat()

    def cmd_flash_initial_firmware(self) -> None:
        """Flash the initial firmware of the microtamagotchi with data."""
        if CTkMessagebox(
            title="Warning !", icon="warning", 
            message="Flash a firmware will erase all data ! "+
                    "Do you want to flash the project in micro:bit ?",
            option_1="Cancel", option_2="No", option_3="Yes"
        ).get() == "Yes":
            self.backend.flashing = True
        self.backend.show_conn_stat()

    def cmd_add_frame_to_character(self) -> None:
        """Add a frame to the character to add to MicroTamagotchi."""
        # get actual led matrice
        character_frame = self.create_leds.get_frame()
        # add led matrice
        if character_frame is not None:
            # add frame to character
            self.create_character_frames.add(
                matrice = self.create_leds.get_matrice_values(),
                character_frame = character_frame
            )
            self.create_leds.clear_values()

    def cmd_add_character(self) -> None:
        """Add a character to the MicroTamagotchi."""
        # check user data
        new_character = self.create_character_frames.get()
        if new_character == []:
            CTkMessagebox(
                title="Info", icon="info",
                message="Create at least a pixels frame for your character !" 
            )
            return
        name = self.character_name_entry.get()
        if name == "":
            CTkMessagebox(
                title="Info", icon="info",
                message="Name your character !"
            )
            return
        # add character
        if self.add_character_to_mt(name, new_character):
            # clear data on widgets
            self.character_name_entry.delete(0, "end")
            self.create_character_frames.clear()
            self.load_mt_settings(wait=0)
            # show msg ok
            CTkMessagebox(
                title="Info", icon="info",
                message=f"Character '{name}' saved in the MicroTamagotchi !"
            )
        else:
            CTkMessagebox(
                title="Warning !", icon="warning",
                message=f"Save of character '{name}' in the MicroTamagotchi failed !"
            )

    def cmd_optm_restart_after(self, value:str) -> None:
        """Set the parameter 'restart_after_flash' for the backend."""
        restart = value=="Restart"
        self.set_setting(
            "restart_after_flash",
            restart
        )
        self.backend.restart_after_flash = restart
    
    def cmd_import_conf(self) -> None:
        """Import configurations from a .json file."""
        # search file
        file = filedialog.askopenfilename(
            title="Import MicroTamagotchi Configurations",
            filetypes=[('data', '*.json')]
        )

        if file is not None:
            # read conf file    
            with open(file, "r") as r_conf:
                data_conf = json.load(r_conf)
            # check uuid
            if self.jsonfile_uuid == data_conf['uuid']:
                # extract data
                self.mt_settings = data_conf["settings"]
                images = data_conf["images"]
                # unformat data (from more readable data in json file)
                for chr in images:
                    for indx, data in enumerate(images[chr]["data"]):
                        images[chr]["data"][indx] = eval(data)
                # send conf data
                self.save_mt_settings()
                self.set_tab_settings()
                self.write_mt_file('images.mtd', images)
                # show ok
                CTkMessagebox(
                    title="Info", icon="info",
                    message=f"Configurations imported from a file !"
                )

            else:
                CTkMessagebox(
                    title="Warning !", icon="warning",
                    message="Configuration file is not valid, can't import this !"
                )

    def cmd_save_conf(self) -> None:
        """Save configurations in a .json file."""
        file_conf = filedialog.asksaveasfile(
            title="Save MicroTamagotchi Configurations",
            initialfile="microtamagotchi_conf.json",
            filetypes=[('data', '*.json')], 
            defaultextension=".json"
        )
        if file_conf is not None:
            # get images
            images = self.read_mt_file("images.mtd")
            # format a little the data for more visibility when read json conf file
            for chr in images:
                for indx, data in enumerate(images[chr]["data"]):
                    images[chr]["data"][indx] = repr(data)
            # create conf
            data_conf = {
                "uuid": self.jsonfile_uuid, # unique id for recognize microtamagotchi_confs
                "settings": self.mt_settings, # settings are already loaded
                "images": images # actual images of the microtamagotchi
            }
            # save conf
            json.dump(data_conf, file_conf, indent=4)
            self.need_save = False
            # close file
            file_conf.close()

    # --- Exit ---

    def _exit(self, wait=True) -> None:
        """Quit application and close the serial."""
        # quit backend
        if wait: 
            self.backend.send_cmd("restart")
        self.backend.exit(wait)
        # destroy app
        self.root.destroy()
        # quit even if backend threads running
        os._exit(0)

    def exit(self) -> None:
        """Quit application and close the serial."""
        # save configurations in a file if needed
        if self.need_save and self.backend.connected:
            if self.save_configurations():
                # exit app if "Cancel" button not clicked
                self._exit()
        elif self.backend.flashing:
            if CTkMessagebox(
                title="Exit ?", icon="warning",
                message="MicroTamagotchi is in flashing, do you want to close this program ?",
                option_1="Cancel", option_2="No", option_3="Yes"
            ).get() == "Yes":
                self._exit(wait=False)
        else:
            # ask quit app
            if CTkMessagebox(
                title="Exit ?", icon="question", 
                message="Do you want to close this program ?",
                option_1="Cancel", option_2="No", option_3="Yes"
            ).get() == "Yes":
                self._exit()


# launch app if this file is launched
if __name__ == "__main__":
    MicroTamagochi_Tool()
