import pymunk

from utils.files import SETTINGS_FILE
import json


# Data Types [Mostly used in math.linear && math.rect4f]
from numpy import float64, float32, int64
FLOAT64 = float64
FLOAT32 = float32
INT64 = int64
ZERO_FLOAT32 = FLOAT32(0)
ONE_FLOAT32 = FLOAT32(1)


# In-Settings Variables
SOUND_PACK: str = ''
MASTER_VOLUME: float = 0.0
GAME_VOLUME: float = 0.0
MUSIC_VOLUME: float = 0.0
TEXTURE_PACK: str = ''
BRIGHTNESS: float = 0.0
WINDOW_RESOLUTION: str = ''
WINDOW_MODE: str = ''
LANGUAGE: str = ''


def load_settings():
    global TEXTURE_PACK, BRIGHTNESS, WINDOW_RESOLUTION, WINDOW_MODE
    global MASTER_VOLUME, GAME_VOLUME, MUSIC_VOLUME, SOUND_PACK
    global LANGUAGE

    with open(SETTINGS_FILE) as f:
        settings = json.load(f)

    TEXTURE_PACK = settings['Texture Pack']
    BRIGHTNESS = settings['Brightness']
    WINDOW_RESOLUTION = settings['Resolution']
    MASTER_VOLUME = settings['Master Volume']
    GAME_VOLUME = settings['Game Volume']
    MUSIC_VOLUME = settings['Music Volume']
    SOUND_PACK = settings['Sound Pack']
    LANGUAGE = settings['Language']
    WINDOW_MODE = settings['Window Mode']


load_settings()


# BASE
TITLE = 'Actually Working Game II'  # window name
DEBUG = False


# FPS
FPS_LOCK = 60  # Do not set more than 60. Game only optimized for <=60
FPS_SHOW = False  # Display FPS counter in console
PHYSIC_UPDATE_FREQUENCY = 1 / 60  # optimal with FPS_LOCK==60


# FONT
FONT_SETTINGS = ('font.ttf', 48)
MENU_FONT_COLOR = (52, 6, 52)


# SCREEN
WINDOW_SIZE = (1920, 1080)  # units
TILE_SIZE = 32
WINDOW_RESOLUTIONS = {
    '16x10FHD': (1920, 1080),
    '16x10low': (1366, 768),
    '4x3low':   (1280, 1024)
}
WINDOW_RESOLUTION: tuple = WINDOW_RESOLUTIONS[WINDOW_RESOLUTION]
WINDOW_MIDDLE = [x / 2 for x in WINDOW_SIZE]
WINDOW_RECT = [*WINDOW_MIDDLE, *WINDOW_SIZE]
FULL_SCREEN = False if WINDOW_MODE == 'windowed' else True


# FOV. Field of View
FOV = 1  # multiplier of screen size
DEFAULT_FOV_W = (WINDOW_SIZE[0] * FOV) / 2
DEFAULT_FOV_H = (WINDOW_SIZE[1] * FOV) / 2

# render rect for fixed must be greater than rect for dynamic
# otherwise dynamic objects may fall through flour
RENDER_RECT_FOR_DYNAMIC = [0, 0, int(DEFAULT_FOV_W * 2.5), int(DEFAULT_FOV_W * 2.5)]
RENDER_RECT_FOR_FIXED = [0, 0, int(DEFAULT_FOV_W * 3), int(DEFAULT_FOV_W * 3)]


# PHYSICS
GRAVITY_VECTOR = (0, -2000)
SLEEP_TIME_THRESHOLD = 0.3


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
AMBIENT_LIGHT = 1.0  # default: 1.0
LIGHT_MULTIPLY = 1.0  # default: 1.0
