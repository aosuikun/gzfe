import pygame
import sys, os, subprocess, json
from utils import get_folders_in_path, get_mods_in_path, load_mods_info


# TODO: Organize this
# TODO: hold down or up is a bit buggy

pygame.init()
pygame.joystick.init()

# ---------- Setup ----------
WIDTH, HEIGHT = 1280, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("gzfe")

# Holding up/down settings
NAV_REPEAT_DELAY = 100   # ms before repeat starts
NAV_REPEAT_RATE = 5    # ms between repeats

# UI highlight
ROW_BG_SELECTED = (70, 70, 70)
ROW_BG_FOCUSED = (90, 90, 90)  # optional: active column

# Cacodemon favorites icon
ICON_SIZE = 24

caco_outline_img = pygame.image.load("cacodemon_outline.png").convert_alpha()
caco_silver_img = pygame.image.load("cacodemon_silver.png").convert_alpha()
caco_gold_img = pygame.image.load("cacodemon_golden.png").convert_alpha()

caco_outline_img = pygame.transform.smoothscale(caco_outline_img, (ICON_SIZE, ICON_SIZE))
caco_silver_img = pygame.transform.smoothscale(caco_silver_img, (ICON_SIZE, ICON_SIZE))
caco_gold_img = pygame.transform.smoothscale(caco_gold_img, (ICON_SIZE, ICON_SIZE))


# Font
font = pygame.font.Font("font/ttf/Hack-Regular.ttf", 24)

# Pygame settings
CLOCK = pygame.time.Clock()

joystick = None
if pygame.joystick.get_count() > 0:
    joystick = pygame.joystick.Joystick(0)
    joystick.init()

# Layout
COL_X = [100, 1000]
ROW_HEIGHT = 30
VISIBLE_ROWS = 25
TOP_MARGIN = 25

scroll_offset = 0

# Functions
def load_default_config(mod_names):
    config = {"last_run": None, "mods": {}}
    return config

def load_config(path, mod_names):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except:
        # Create defaults and return
        config = load_default_config(mod_names)
        return config

def save_config(config, path):
    with open(path, "w") as f:
        json.dump(config, f)

def clamp_scroll():
    global scroll_offset
    if selected_row < scroll_offset:
        scroll_offset = selected_row
    elif selected_row >= scroll_offset + VISIBLE_ROWS:
        scroll_offset = selected_row - VISIBLE_ROWS + 1

def update_rating(row):
    global config, mods_dict
    rating = mods_dict[mods_list[row]]["rating"]
    if rating == 'unrated':
        rating = 'silver'
    elif rating == 'silver':
        rating = 'gold'
    else:
        rating = 'unrated'
    
    mods_dict[mods_list[row]]["rating"]= rating
    mod_name = mods_dict[mods_list[row]]['name']

    if mod_name in config["mods"].keys():
        config["mods"][mod_name]["rating"] = rating
    else:
        config["mods"][mod_name] = {"rating": rating}


def handle_action(row, col):
    if col == 0:
        run_mod(mods_list[row])
    else:
        update_rating(row=row)

def run_mod(mod_selected):
    global running
    global config
    # get mod launch command:
    launch_command = mods_dict[mod_selected]["launch_command"]

    # save selected mod as last run so it can be retrieved next time
    config["last_run"] = mod_selected

    # Save config
    save_config(config, config_file_path)
    
    # run mod
    os.chdir("/home/deck/.var/app/org.zdoom.GZDoom/.config/gzdoom")
    subprocess.Popen(launch_command, shell=True)

    print(f"DEBUG LOG - Mod selected: {mod_selected}")
    print(f"DEBUG LOG - Run command: {launch_command}")

    # Stop python GUI made from this script
    running = False

# Getting Doom mods data
mods_folder = "/home/deck/games/doom/pwads"
mods_dict = load_mods_info(mods_folder, True)
mods_list = list(mods_dict.keys())
mods_list.sort(key=lambda y: y.lower())

# Initial setup
config_file_path = "gzfe.json"
config = load_config(config_file_path, mods_list)
# Selected row and columns counter
last_run = config["last_run"]


if last_run in mods_list:
    selected_row = mods_list.index(last_run)
else:
    selected_row = 0

selected_col = 0

def load_mod_ratings():
    global mods_dict, config, mods_list
    for mod in config["mods"]:
        mod_name = mod
        if mod_name in mods_list:
            mods_dict[mod_name]["rating"] = config["mods"][mod_name]["rating"]


load_mod_ratings()

held_dir = None          # "up" or "down"
last_nav_time = 0
held_hat_y = 0

# ---------- Main Loop ----------
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        # -------- Keyboard --------
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                held_dir = "up"
                last_nav_time = pygame.time.get_ticks()
                selected_row = max(0, selected_row - 1)
                clamp_scroll()

            elif event.key == pygame.K_DOWN:
                held_dir = "down"
                last_nav_time = pygame.time.get_ticks()
                selected_row = min(len(mods_list) - 1, selected_row + 1)
                clamp_scroll()
            elif event.key == pygame.K_LEFT:
                selected_col = 0
            elif event.key == pygame.K_RIGHT:
                selected_col = 1
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                handle_action(selected_row, selected_col)
            clamp_scroll()

        elif event.type == pygame.KEYUP:
            if event.key in (pygame.K_UP, pygame.K_DOWN):
                held_dir = None

        # -------- Controller --------
        if event.type == pygame.JOYHATMOTION:
            hat_x, hat_y = event.value
            held_hat_y = hat_y
            if hat_y == 1:
                selected_row = max(0, selected_row - 1)
            elif hat_y == -1:
                selected_row = min(len(mods_list) - 1, selected_row + 1)
            elif event.button == 5:  # R bumper
                selected_row = min(len(mods_list) - 1, selected_row + PAGE_JUMP)
                clamp_scroll()
            elif event.button == 4:  # L bumper
                selected_row = max(0, selected_row - PAGE_JUMP)
                clamp_scroll()
            
            if hat_x == -1:
                selected_col = 0
            elif hat_x == 1:
                selected_col = 1
            clamp_scroll()

        if event.type == pygame.JOYBUTTONDOWN:
            if event.button == 0:
                handle_action(selected_row, selected_col)

    
    now = pygame.time.get_ticks()
    if held_dir and now - last_nav_time >= NAV_REPEAT_DELAY:
        if now - last_nav_time >= NAV_REPEAT_RATE:
            if held_dir == "up":
                selected_row = max(0, selected_row - 1)
            elif held_dir == "down":
                selected_row = min(len(mods_list) - 1, selected_row + 1)

            clamp_scroll()
            last_nav_time = now

    if held_hat_y != 0 and now - last_nav_time >= NAV_REPEAT_DELAY:
        if now - last_nav_time >= NAV_REPEAT_RATE:
            if held_hat_y == 1:
                selected_row = max(0, selected_row - 1)
            elif held_hat_y == -1:
                selected_row = min(len(mods_list) - 1, selected_row + 1)

            clamp_scroll()
            last_nav_time = now

    # ---------- Draw ----------
    screen.fill((30, 30, 30))

    start = scroll_offset
    end = min(scroll_offset + VISIBLE_ROWS, len(mods_list))

    for i in range(start, end):
        draw_y = TOP_MARGIN + (i - scroll_offset) * ROW_HEIGHT

        # --- Row background (file-manager style) ---
        if i == selected_row:
            pygame.draw.rect(
                screen,
                ROW_BG_SELECTED,
                pygame.Rect(0, draw_y - 6, WIDTH, ROW_HEIGHT)
            )

        if i == selected_row:
            col_x = COL_X[selected_col]
            pygame.draw.rect(
                screen,
                ROW_BG_FOCUSED,
                pygame.Rect(col_x - 10, draw_y - 6, 400, ROW_HEIGHT)
    )

        # --- Fruit text ---
        fruit_surf = font.render(mods_list[i], True, (255, 255, 255))
        screen.blit(fruit_surf, (COL_X[0], draw_y - 5))


        # Caco column
        if 'rating' not in mods_dict[mods_list[i]].keys():
            mods_dict[mods_list[i]]['rating'] = 'unrated'

        rating = mods_dict[mods_list[i]]['rating']
        
        if rating == 'unrated':
            icon = caco_outline_img
        elif rating == 'silver':
            icon = caco_silver_img
        else:
            icon = caco_gold_img

        icon_rect = icon.get_rect()
        icon_rect.center = (
            COL_X[1] + ICON_SIZE // 2,
            draw_y + ROW_HEIGHT // 2 - ICON_SIZE/4
        )
        screen.blit(icon, icon_rect)


    pygame.display.flip()
    CLOCK.tick(60)

save_config(config, config_file_path)
pygame.quit()
sys.exit()
