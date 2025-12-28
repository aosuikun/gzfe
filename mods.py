import os, json, subprocess

DEBUG = False

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


def load_mods(mods_folder, local_save_dir=True):
    # Locate folders inside mods_folder
    folder_names, folder_paths = get_folders_in_path(mods_folder)

    # Create mods dictionary
    mods_dict = dict() # mods information is stored here

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
        mods_dict[folder_names[i]] = \
        {
        "path": folder_path,
        "name": folder_names[i],
        "mod_names": mods,
        "launch_command": launch_command
        }

    return mods_dict


def load_default_config():
    config = {"last_run": None, "mods": {}}
    return config


def save_config(config, path):
    with open(path, "w") as f:
        json.dump(config, f)


class DoomMods():
    def __init__(self, mods_folder, config_path):
        # mods_folder = "/home/deck/games/doom/pwads"
        self.mods_dict = load_mods(mods_folder, True)
        self.mods_list = list(self.mods_dict.keys())
        self.mods_list.sort(key=lambda y: y.lower())

        # Load saved settings
        self.config_path = config_path
        self.config = self.load_config(config_path)
        # for mod in self.config["mods"]:
        #     if mod in self.mods.list:
        #         self.mods_dict[mod]["rating"] = self.config["mods"][mod]["rating"]
        
        if self.config["last_run"] in self.mods_list:
            self.last_run_index = self.mods_list.index(self.config["last_run"])
        else:
            self.last_run_index = 0

        # self.last_run = config["last_run"]

    
    def load_config(self, path):
        # Load previous config if it exists, else create an empty one
        if os.path.exists(path):
            print(path)
            with open(path, "r") as f:
                config = json.load(f)
        else:
            config = load_default_config()

        # If mod is not on the config, populate it with default values
        for mod in self.mods_list:
            if mod not in config["mods"].keys():
                config["mods"][mod] = {'rating': 'unrated'}
        

        return config

    
    def update_mod_rating(self, index):
        # Get previous rating
        # TODO: this is going to fail if rating does not exist.. fix that, need to remove handling from gzfe.py
        rating = self.config['mods'][self.mods_list[index]]["rating"]

        # Update rating (unrated -> silver -> gold -> unrated -> etc):
        if rating == 'unrated':
            rating = 'silver'
        elif rating == 'silver':
            rating = 'gold'
        elif rating == 'gold':
            rating = 'bad'
        else:
            rating = 'unrated'
        
        # Save new rating
        self.config['mods'][self.mods_list[index]]["rating"] = rating
        # self.mods_dict[self.mods_list[index]]["rating"]= rating
        # mod_name = self.mods_dict[mods_list[index]]['name']

        # if mod_name in self.config["mods"].keys():
        #     self.config["mods"][mod_name]["rating"] = rating
        # else:
        #     self.config["mods"][mod_name] = {"rating": rating}

    
    def run_mod(self, mod):
        global DEBUG
        # make mod launch command:
        launch_command = self.mods_dict[mod]["launch_command"]

        # save selected mod as last run so it can be retrieved next time
        self.config["last_run"] = mod
        save_config(self.config, self.config_path)

        # Debug logging
        if DEBUG:
            print(f"DEBUG LOG - Mod selected: {mod}")
            print(f"DEBUG LOG - Run command: {launch_command}")
        
        # run mod
        os.chdir("/home/deck/.var/app/org.zdoom.GZDoom/.config/gzdoom")
        subprocess.Popen(launch_command, shell=True)


def test():
    doom_mods = DoomMods(mods_folder="/home/deck/games/doom/pwads")
    print(doom_mods.mods_list)
    print(doom_mods.config)
    print(doom_mods.mods_dict["Alien Vendetta"])