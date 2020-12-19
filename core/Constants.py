import pygame
import pymunk

# BASE
TITLE = 'AWG 2'  # window name
TEXTURE_PACK = 'base_pack'  # folder name in data/Textures
DEBUG = True


# FPS
FPS_LOCK = 60  # Do not set more than 60. Game only optimized for <=60
FPS_SHOW = True  # Display FPS counter in console
PHYSIC_UPDATE_FREQUENCY = 0.017  # optimal with FPS_LOCK==60


# FONT
pygame.font.init()
FONT = pygame.font.SysFont('Arial Black', 42)
MENU_FONT_COLOR = (52, 6, 52)


# SCREEN
WINDOW_SIZE = (1920, 1080)  # units
WINDOW_RESOLUTIONS = {'16x10FHD': (1920, 1080), '16x10low': (1366, 768),
                      '4x3low': (1280, 1024), 'Maks': (1024, 768), '4:3': (800, 640)}  # pixels
WINDOW_RESOLUTION = '16x10low'  # current
WINDOW_RESOLUTION = WINDOW_RESOLUTIONS[WINDOW_RESOLUTION]

DEDICATED_RESOLUTION = '4:3'
DEDICATED_RESOLUTION = WINDOW_RESOLUTIONS[DEDICATED_RESOLUTION]

FULL_SCREEN = False
WINDOW_MIDDLE = [x // 2 for x in WINDOW_SIZE]
WINDOW_RECT = [*WINDOW_MIDDLE, *WINDOW_SIZE]
DEFAULT_SCALE = 1


# FOV. Field of View
FOV = 1  # multiplier of screen size
DEFAULT_FOV_W = (WINDOW_SIZE[0] * FOV) // 2
DEFAULT_FOV_H = (WINDOW_SIZE[1] * FOV) // 2

# render rect for fixed must be greater than rect for dynamic
# otherwise dynamic objects may fall through flour
RENDER_RECT_FOR_DYNAMIC = [0, 0, int(DEFAULT_FOV_W * 2.5), int(DEFAULT_FOV_W * 2.5)]
RENDER_RECT_FOR_FIXED = [0, 0, int(DEFAULT_FOV_W * 3), int(DEFAULT_FOV_W * 3)]


# SOUND
VOLUME = 1


# PHYSICS
GRAVITY_VECTOR = (0, -2000)

# body types from pymunk
BODY_TYPES = (
    pymunk.Body.STATIC,
    pymunk.Body.DYNAMIC,
    pymunk.Body.KINEMATIC
)

# collision types for pymunk.Shape
COLL_TYPES = {
    'player': 0,
    'mortal': 1,
    'item': 2,
    'obstacle': 3,

    'trigger_obstacle': 10,
    'trigger_player': 11,
    'trigger_mortal': 12,
    'trigger_item': 13,
}