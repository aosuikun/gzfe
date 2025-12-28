import pygame
import sys, os
from mods import save_config, DoomMods

# --- Paths ---
# TODO: Make this configurable from the GUI
current_folder = os.path.dirname(__file__)
CONFIG_PATH = os.path.join(current_folder,"doom_mods_config.json")
MODS_FOLDER = "/home/deck/games/doom/pwads"

# --- Setup pygame ---
# Init
pygame.init()

# Window
WIDTH, HEIGHT = 1280, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("gzfe")
# UI / Layout
BACKGROUND_COLOR = (50, 50, 50)
SELECTED_ROW_HIGHLIGHT = (70, 70, 70)
SELECTED_COLUMN_HIGHLIGHT = (90, 90, 90)
COL_X = [100, 1000]
ROW_HEIGHT = 30
VISIBLE_ROWS = 25
TOP_MARGIN = 25
scroll_offset = 0

# Joystick
pygame.joystick.init()
joystick = None
if pygame.joystick.get_count() > 0:
    joystick = pygame.joystick.Joystick(0)
    joystick.init()

# Timing
CLOCK = pygame.time.Clock()


# --- Settings ---
# Hold up/down timing
NAV_REPEAT_DELAY = 300   # ms before repeat starts
NAV_REPEAT_RATE = 30    # ms between repeats

# --- Graphs / Font ---
# Cacodemon ratings
ICON_SIZE = 24

caco_unrated_img = pygame.image.load("cacodemon_outline.png").convert_alpha()
caco_silver_img = pygame.image.load("cacodemon_silver.png").convert_alpha()
caco_gold_img = pygame.image.load("cacodemon_golden.png").convert_alpha()
caco_bad_img = pygame.image.load("cacodemon_bad.png").convert_alpha()

caco_unrated_img = pygame.transform.smoothscale(caco_unrated_img, (ICON_SIZE, ICON_SIZE))
caco_silver_img = pygame.transform.smoothscale(caco_silver_img, (ICON_SIZE, ICON_SIZE))
caco_gold_img = pygame.transform.smoothscale(caco_gold_img, (ICON_SIZE, ICON_SIZE))
caco_bad_img = pygame.transform.smoothscale(caco_bad_img, (ICON_SIZE, ICON_SIZE))

# Font
font = pygame.font.Font("font/ttf/Hack-Regular.ttf", 24)

# --- Load mods ---
doom_mods = DoomMods(mods_folder=MODS_FOLDER, config_path=CONFIG_PATH)

# --- Start index from last run mod ---
selected_row = doom_mods.last_run_index
scroll_offset = selected_row - VISIBLE_ROWS + 1
if scroll_offset < 0: scroll_offset = 0

# --- Hold up/down variables ---
selected_col = 0
held_dir = None          # "up" or "down"
hold_key_time = 0
hold_key_last_scroll_time = 0
held_hat_y = 0


def clamp_scroll():
    global scroll_offset
    if selected_row < scroll_offset:
        scroll_offset = selected_row
    elif selected_row >= scroll_offset + VISIBLE_ROWS:
        scroll_offset = selected_row - VISIBLE_ROWS + 1


def handle_button_press(row, col):
    global running
    if col == 0:
        doom_mods.run_mod(mod = doom_mods.mods_list[row])
        running = False # Stop running GUI after launching mod
    elif col == 1:
        doom_mods.update_mod_rating(index=row)
    else:
        print("WARNING: There should not be more than 2 columns...")


# --- GUI main loop ---
running = True
number_of_mods = len(doom_mods.mods_list)
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        # --- Handle keyboard keys ---
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                held_dir = "up"
                hold_key_time = pygame.time.get_ticks()
                hold_key_last_scroll_time = hold_key_time
                selected_row = max(0, selected_row - 1)
                clamp_scroll()
            elif event.key == pygame.K_DOWN:
                held_dir = "down"
                hold_key_time = pygame.time.get_ticks()
                hold_key_last_scroll_time = hold_key_time
                selected_row = min(number_of_mods - 1, selected_row + 1)
                clamp_scroll()
            elif event.key == pygame.K_LEFT:
                selected_col = 0
            elif event.key == pygame.K_RIGHT:
                selected_col = 1
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                handle_button_press(selected_row, selected_col)
            clamp_scroll()

        elif event.type == pygame.KEYUP:
            if event.key in (pygame.K_UP, pygame.K_DOWN):
                held_dir = None

        # --- Handle Controller keys ---
        # TODO: test if this is actually working...
        if event.type == pygame.JOYHATMOTION:
            hat_x, hat_y = event.value
            held_hat_y = hat_y
            if hat_y == 1:
                selected_row = max(0, selected_row - 1)
            elif hat_y == -1:
                selected_row = min(number_of_mods - 1, selected_row + 1)
            elif event.button == 5:  # R bumper
                selected_row = min(number_of_mods - 1, selected_row + PAGE_JUMP)
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
                handle_button_press(selected_row, selected_col)

    # Hold down up or down buttons behavior
    now = pygame.time.get_ticks()
    if held_dir and now - hold_key_time >= NAV_REPEAT_DELAY:
        if now - hold_key_last_scroll_time >= NAV_REPEAT_RATE:
            if held_dir == "up":
                selected_row = max(0, selected_row - 1)
            elif held_dir == "down":
                selected_row = min(number_of_mods - 1, selected_row + 1)

            clamp_scroll()
            hold_key_last_scroll_time = now

    if held_hat_y != 0 and now - hold_key_time >= NAV_REPEAT_DELAY:
        if now - hold_key_last_scroll_time >= NAV_REPEAT_RATE:
            if held_hat_y == 1:
                selected_row = max(0, selected_row - 1)
            elif held_hat_y == -1:
                selected_row = min(number_of_mods - 1, selected_row + 1)

            clamp_scroll()
            hold_key_last_scroll_time = now

    # --- Draw ---
    screen.fill(BACKGROUND_COLOR)

    start = scroll_offset
    end = min(scroll_offset + VISIBLE_ROWS, number_of_mods)

    for i in range(start, end):
        draw_y = TOP_MARGIN + (i - scroll_offset) * ROW_HEIGHT

        # --- Selected row and column highlights ---
        if i == selected_row:
            pygame.draw.rect(
                screen,
                SELECTED_ROW_HIGHLIGHT,
                pygame.Rect(0, draw_y - 6, WIDTH, ROW_HEIGHT)
            )

        if i == selected_row:
            col_x = COL_X[selected_col]
            pygame.draw.rect(
                screen,
                SELECTED_COLUMN_HIGHLIGHT,
                pygame.Rect(col_x - 10, draw_y - 6, 400, ROW_HEIGHT)
    )

        # Mod name column
        mod_surf = font.render(doom_mods.mods_list[i], True, (255, 255, 255))
        screen.blit(mod_surf, (COL_X[0], draw_y - 5))


        # Caco rating column
        rating = doom_mods.config['mods'][doom_mods.mods_list[i]]['rating']
        
        if rating == 'unrated':
            icon = caco_unrated_img
        elif rating == 'silver':
            icon = caco_silver_img
        elif rating == 'gold':
            icon = caco_gold_img
        else:
            icon = caco_bad_img

        icon_rect = icon.get_rect()
        icon_rect.center = (
            COL_X[1] + ICON_SIZE // 2,
            draw_y + ROW_HEIGHT // 2 - ICON_SIZE/4
        )
        screen.blit(icon, icon_rect)


    pygame.display.flip()
    CLOCK.tick(60)

save_config(config, CONFIG_PATH)
pygame.quit()
sys.exit()