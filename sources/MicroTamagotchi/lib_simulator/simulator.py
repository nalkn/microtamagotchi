#Projet: MicroTamagotchi
#Auteurs: Killian Nallet, Mattéo Martin-Boileux
#Python: Python >= 3.9
#Coding: utf-8


#--- MICROTAMAGOTCHI - MICROBIT SIMULATOR ---

# imports
import os
import tempfile

#TODO: adapter le simulateur pour l'applicztion

# err class
class MicrobitSimulatorError(Exception):

    """
    Microbit Simulator error.
    """

    pass


# simulator
class MicrobitSimulator:

    """
    Microbit Simulator for Windows and Linux (MacOS ot tested).
    """

    MODE_FILE = "launch_file"
    MODE_MODULE = "launch_module"
    arg_launched = "-simulator_started"

    def __init__(self, main_file=None):
        self.main_file = main_file
        if self.main_file != None:
            self.mode = self.MODE_FILE
#            self.launch_main_file()
            self._dir = os.path.dirname(main_file)
        else:
            self.mode = self.MODE_MODULE
            from . import microTk as Microbit
            #TODO: joindre Microbit à self (san setattr si possible ... sinon pas acces aux fonctions)
            self._dir = self._generate_temp_dir()

    def _generate_temp_dir(self):
        """Generate a temporary directore for emulate microbit filesystem."""
        temp_dir = tempfile.TemporaryDirectory()
        print(temp_dir.name)
        # use temp_dir, and when done:
        temp_dir.cleanup()

    def exit(self):
        pass
    
#    def launch_main_file(self):
#        """Launch the main file of the simulator"""
#        # check paths
#        executable = self.check_path(sys.executable)
#        main_file = self.check_path(self.main_file)
#        # exec file
#        cmd = f'{executable} {main_file} {self.arg_launched}'
#        os.system(cmd)

#    def check_path(self, path):
#        """Check if the provided path is valid."""
#        # check file exists
#        if not os.path.exists(path):
#            raise MicrobitSimulatorError(f"path {path} not exists !")
#        # check spaces
#        if " " in path:
#            path = '"'+path+'"'
#        # return new path
#        return path


#def is_launched():
#    """Check if program launched by Microbit_Simulator."""
#    return MicrobitSimulator.arg_launched in sys.argv


#def start(main_file, exit=True):
#    """Start the Microbit Simulator."""
#    if not is_launched():
#        MicrobitSimulator(main_file)
#        if exit:
#            sys.exit(0)
