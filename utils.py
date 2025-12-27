import os, subprocess, json
import tkinter as tk
from tkinter import ttk

def get_folders_in_path(path):
    contents = os.listdir(path)     # List all files and directories
    folder_names = [c for c in contents if os.path.isdir(os.path.join(path, c))]  # Filter to only get folder names
    folder_paths = [os.path.join(path, fn) for fn in folder_names]  # Make full folder paths
    return folder_names, folder_paths

def get_mods_in_path(path):
    # Get all mods inside path (Supported extensions: .WAD, .wad and .pk3)
    contents = os.listdir(path)
    mods = [file for file in contents if file[-4:] == ".wad" or file[-4:] == ".WAD" or file[-4:] == ".pk3"]
    return mods

def create_mod_launch_command(folder_path, mods, local_save_dir=True):
    # Prepare mod information for launch command
    mods_paths = [os.path.join(folder_path, mod) for mod in mods]
    mods_paths_str = ""
    for mp in mods_paths:
        mods_paths_str += mp.replace(" ", "\\ ") + " "
    
    # Make launch command
    launch_command_prefix = "/usr/bin/flatpak run --branch=stable --arch=x86_64 --command=gzdoom.sh org.zdoom.GZDoom \
    -file "
    if local_save_dir:
        folder_path_str = folder_path.replace(" ", "\\ ")
        launch_command_suffix = f"-savedir {folder_path_str}/save"
    else:
        launch_command_suffix = " $@"

    launch_command = launch_command_prefix + mods_paths_str + launch_command_suffix

    return launch_command

def load_mods_info(mods_folder, local_save_dir):
    # Locate folders inside mods_folder
    folder_names, folder_paths = get_folders_in_path(mods_folder)

    # Create mods dictionary
    mods_info = dict() # mods information is stored here

    # For each mod folder found, create the relevant information for that mod
    for i, folder_path in enumerate(folder_paths):
    
        mods = get_mods_in_path(folder_path)

        # Skip if no mods were found in the folder
        if not mods:
            print(f"WARNING: No mods found in {folder_path}")
            continue
        
        # Create launch command for the mods found
        launch_command = create_mod_launch_command(folder_path, mods, local_save_dir)

        # Adding info to mods dictionary
        mods_info[folder_names[i]] = \
        {
        "path": folder_path,
        "name": folder_names[i],
        "mod_names": mods,
        "launch_command": launch_command
        }

    return mods_info

def load_defaults():
    config = {"last_run": None}
    return config

def load_config(path):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except:
        # Create defaults and return
        config = load_defaults()
        return config

def save_config(config, path):
    with open(path, "w") as f:
        json.dump(config, f)

class ModsListGUI():

    def __init__(self, mods_folder, local_save_dir=True, debug_mode=False):
        self.debug_mode = debug_mode

        # Load previous configuration or create new from defaults
        self.config_file_path = "gzfe.json"
        self.config = load_config(self.config_file_path)
        try:
            last_run = self.config["last_run"]
        except:
            print(f"Error loading config file: {self.config_file_path}.\n\
            Either fix the file or delete it (it will be re-created from defauts) and run the app again.")

        # Get mods info and sort alphabetically
        self.mods_info = load_mods_info(mods_folder, local_save_dir)
        self.mods_names = list(self.mods_info.keys())
        self.mods_names.sort(key=lambda y: y.lower())

        # Get index of previously run mod if available
        if last_run in self.mods_names:
            init_index = self.mods_names.index(last_run)
        else:
            init_index = 0

        # Make GUI window
        self.window = tk.Tk()
        self.window.title("GZDOOM mods launcher")
        # Create label informing mods folder location
        self.title = tk.Label(self.window, text=f"Mods folder: {mods_folder}", bg="light gray", fg="black")
        self.title.pack()

        # Create list box
        self.listbox = tk.Listbox(self.window, selectmode=tk.SINGLE, 
                                    height = 20, width = 50, bg="light gray",
                                    exportselection=False, activestyle="none") 
        # Create scroll bar
        scrollbar = ttk.Scrollbar(
            self.window,
            orient=tk.VERTICAL,
            command=self.listbox.yview
        )
        self.listbox['yscrollcommand'] = scrollbar.set
        scrollbar.pack(side=tk.RIGHT, expand=True, fill=tk.Y)
        # Populate list box with mods names
        for x in self.mods_names: self.listbox.insert(tk.END, x)
        self.listbox.pack() # put listbox on window

        # Make run and exit buttons
        tk.Button(self.window,text="Run",command=self.run_mod).pack(side=tk.LEFT)
        tk.Button(self.window,text="Exit",command=lambda: self.window.destroy()).pack(side=tk.RIGHT)

        # Select line on listbox and set focus to the window
        self.listbox.select_set(init_index)
        self.listbox.activate(init_index)
        self.listbox.see(init_index)
        self.listbox.focus_set()

        # Handle key presses
        self.window.bind("<Key>", self.handle_key_press)

    def handle_key_press(self, event=None):
        key_name = event.keysym
        if key_name == "Up":
            selected_index = self.listbox.curselection()[0]
            if selected_index>0:
                self.listbox.select_clear(selected_index)
                self.listbox.select_set(selected_index-1)
            return
        if key_name == "Down":
            selected_index = self.listbox.curselection()[0]
            if selected_index < len(self.mods_names)-1:
                self.listbox.select_clear(selected_index)
                self.listbox.select_set(selected_index+1)
            return
        if key_name == "Escape":
            self.window.destroy()
            return
        # Else, other key presses should just run the selected mod
        self.run_mod(self)

    def run_mod(self, event=None):
        # get mod selected:
        mod_selected = self.listbox.curselection()
        mod_selected = self.listbox.get(mod_selected)
        
        # get mod launch command:
        launch_command = self.mods_info[mod_selected]["launch_command"]

        # save mod name to config file
        self.config["last_run"] = mod_selected
        save_config(self.config, self.config_file_path)
        
        # run mod
        os.chdir("/home/deck/.var/app/org.zdoom.GZDoom/.config/gzdoom")
        subprocess.Popen(launch_command, shell=True)

        if self.debug_mode:
            print(f"DEBUG LOG - Mod selected: {mod_selected}")
            print(f"DEBUG LOG - Run command: {launch_command}")

        # kill GUI
        self.window.destroy()


def main():

    mods_folder = "/home/deck/games/doom/pwads_untested"
    local_save_dir = True   # If True save files are stored separately inside each mod folder
    debug_mode = False      # If True prints some debug information to the console

    ModsGUI = ModsListGUI(mods_folder, local_save_dir, debug_mode)
    ModsGUI.window.mainloop()

    if debug_mode:
        print("DEBUG LOG - Exiting gzfe")


if __name__ == "__main__":
    main()
