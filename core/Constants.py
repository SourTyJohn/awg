import pymunk

from utils.files import SETTINGS_FILE
import json

# LOAD SETTINGS
settings = {}


def load_settings():
    global settings
    with open(SETTINGS_FILE) as f:
        settings = json.load(f)


load_settings()


# BASE
TITLE = 'AWG 2'  # window name
TEXTURE_PACK = settings['Texture Pack']  # folder name in data/Textures
DEBUG = True
DRAW_TRIGGER = True


# FPS
FPS_LOCK = 60  # Do not set more than 60. Game only optimized for <=60
FPS_SHOW = False  # Display FPS counter in console
PHYSIC_UPDATE_FREQUENCY = 0.017  # optimal with FPS_LOCK==60


# FONT
FONT_SETTINGS = ('font.ttf', 48)
MENU_FONT_COLOR = (52, 6, 52)


# SCREEN
WINDOW_SIZE = (1920, 1080)  # units
BRIGHTNESS = settings['Brightness']
TILE_SIZE = 32

# resolution
WINDOW_RESOLUTIONS = {'16x10FHD': (1920, 1080), '16x10low': (1366, 768),
                      '4x3low': (1280, 1024), 'Maks': (1024, 768)}  # pixels
WINDOW_RESOLUTION = settings['Resolution']  # current
WINDOW_RESOLUTION = WINDOW_RESOLUTIONS[WINDOW_RESOLUTION]
FULL_SCREEN = False

WINDOW_MIDDLE = [x / 2 for x in WINDOW_SIZE]
WINDOW_RECT = [*WINDOW_MIDDLE, *WINDOW_SIZE]


# FOV. Field of View
FOV = 1  # multiplier of screen size
DEFAULT_FOV_W = (WINDOW_SIZE[0] * FOV) / 2
DEFAULT_FOV_H = (WINDOW_SIZE[1] * FOV) / 2

# render rect for fixed must be greater than rect for dynamic
# otherwise dynamic objects may fall through flour
RENDER_RECT_FOR_DYNAMIC = [0, 0, int(DEFAULT_FOV_W * 2.5), int(DEFAULT_FOV_W * 2.5)]
RENDER_RECT_FOR_FIXED = [0, 0, int(DEFAULT_FOV_W * 3), int(DEFAULT_FOV_W * 3)]


# SOUND
VOLUME = settings['Volume']
SOUND_STREAMS_AMOUNT = 4


# PHYSICS
GRAVITY_VECTOR = (0, -2000)


# BODY TYPES
BODY_TYPES = {
    'static': pymunk.Body.STATIC,
    'dynamic': pymunk.Body.DYNAMIC,
    'kinematic': pymunk.Body.KINEMATIC
}


# COLLISION TYPES
COLL_TYPES = {
    'player': 0,
    'mortal': 1,
    'item': 2,
    'obstacle': 3,
    'trigger': 4,
    'particle': 5,

    # Triggers. Must be named t_<coll_type>&&<coll_type>...
    # Check CollisionHandles.triggersSetup() for more info
    't_obstacle': 10,
    't_obstacle&&mortal': 11,
    't_player': 12,
    't_mortal': 13,
    't_item': 14,
    't_*': 15,
}


# SHADERS
AMBIENT_LIGHT = 2.0  # default: 1.0
LIGHT_MULTIPLY = 1.0  # default: 1.0
