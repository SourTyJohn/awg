from utils.files import SETTINGS_FILE
from pymunk.body import Body
from json import load as json_load

# TAGS
# TAG_PHYSIC_THROWABLE = 1
# TAG_SILENCED = 2  # no sound
# TAG_HUMAN = 4
# TAG_UNDEAD = 8


# PARTICLES
MAX_PARTICLES = 2 ** 12


# IN-SETTINGS VARIABLES
STN_SOUND_PACK: str = ''
STN_TEXTURE_PACK: str = ''
STN_MATERIAL_PACK: str = ''

STN_MASTER_VOLUME: float = 0.0
STN_GAME_VOLUME: float = 0.0
STN_MUSIC_VOLUME: float = 0.0
STN_BRIGHTNESS: float = 0.0
STN_WINDOW_RESOLUTION: str = ''
STN_WINDOW_MODE: str = ''
STN_LANGUAGE: str = ''


def load_settings():
    global STN_TEXTURE_PACK, STN_BRIGHTNESS, STN_WINDOW_RESOLUTION, STN_WINDOW_MODE
    global STN_MASTER_VOLUME, STN_GAME_VOLUME, STN_MUSIC_VOLUME, STN_SOUND_PACK
    global STN_LANGUAGE, STN_MATERIAL_PACK

    with open(SETTINGS_FILE) as f:
        settings = json_load(f)

    STN_TEXTURE_PACK = settings['Texture Pack']
    STN_SOUND_PACK = settings['Sound Pack']
    STN_MATERIAL_PACK = settings["Material Pack"]

    STN_BRIGHTNESS = settings['Brightness']
    STN_WINDOW_RESOLUTION = settings['Resolution']
    STN_MASTER_VOLUME = settings['Master Volume']
    STN_GAME_VOLUME = settings['Game Volume']
    STN_MUSIC_VOLUME = settings['Music Volume']
    STN_LANGUAGE = settings['Language']
    STN_WINDOW_MODE = settings['Window Mode']


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
TILE_SIZE = 48
WINDOW_RESOLUTIONS = {
    '16x10FHD': (1920, 1080),
    '16x10low': (1366, 768),
    '4x3low':   (1280, 1024)
}
STN_WINDOW_RESOLUTION: tuple = WINDOW_RESOLUTIONS[STN_WINDOW_RESOLUTION]
WINDOW_MIDDLE = [x / 2 for x in WINDOW_SIZE]
WINDOW_RECT = [*WINDOW_MIDDLE, *WINDOW_SIZE]
FULL_SCREEN = False if STN_WINDOW_MODE == 'windowed' else True


# FOV
FOV: float = 1.0  # multiplier of screen size


# PHYSICS
GRAVITY_VECTOR = (0, -2000)
SLEEP_TIME_THRESHOLD = 0.3
MAX_PHYSIC_STEP = 1 / 60


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
MAX_TEXTURES_BIND = 32
MAX_TEXTURE_3D_LAYERS = 2048
MATERIAL_SIZE = TILE_SIZE
