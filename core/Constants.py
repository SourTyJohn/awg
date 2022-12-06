from utils.files import SETTINGS_FILE

from pymunk.body import Body
from pymunk.vec2d import Vec2d
from numpy import ndarray, array, matrix
from json import load as json_load
from typing import Union, Generator
from numpy import float64, float32, int64, uintc, int16, float16


# DATA TYPES
FLOAT64 = float64
FLOAT32 = float32
FLOAT16 = float16
INT64 = int64
INT16 = int16
UINT = uintc
ARRAY = array

ZERO_FLOAT32 = FLOAT32(0)
ONE_FLOAT32 = FLOAT32(1)
INF = float('inf')

TYPE_FLOAT = Union[float, FLOAT32, FLOAT64]
TYPE_INT = Union[int, INT64]
TYPE_NUM = Union[float, FLOAT32, FLOAT64, int, INT64, uintc]
TYPE_VEC = Union[Vec2d, ndarray, Generator]
TYPE_MAT = Union[ndarray, matrix]


# TAGS
# TAG_PHYSIC_THROWABLE = 1
# TAG_SILENCED = 2  # no sound
# TAG_HUMAN = 4
# TAG_UNDEAD = 8


# PARTICLES
MAX_PARTICLES = 2 ** 12


# IN-SETTINGS VARIABLES
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
        settings = json_load(f)

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


# FOV
FOV: float = 1.0  # multiplier of screen size


# PHYSICS
GRAVITY_VECTOR = (0, -2000)
SLEEP_TIME_THRESHOLD = 0.3


# BODY TYPES
BODY_TYPES = {
    'static': Body.STATIC,
    'dynamic': Body.DYNAMIC,
    'kinematic': Body.KINEMATIC
}


# LIGHTING
AMBIENT_LIGHT = 1.0  # default: 1.0
LIGHT_MULTIPLY = 1.0  # default: 1.0
MAX_LIGHT_SOURCES = 2 ** 10
LIGHT_POWER_UNIT = 8

# RENDER
MAX_INSTANCES = 128
MAX_TEXTURES_BIND = 16
