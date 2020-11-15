import pygame
from core.physic.Vector import Vector2f

# BASE
TITLE = 'AWG 2'
DEBUG = True
TEXTURE_PACK = 'base_pack'


# FPS
FPS_LOCK = 60
PHYSIC_UPDATE_FREQUENCY = 0.017  # optimal with FPS_LOCK==60


# FONT
pygame.font.init()
FONT = pygame.font.SysFont('Arial Black', 42)
MENU_FONT_COLOR = (52, 6, 52)


# SCREEN
WINDOW_SIZE = (1920, 1080)  # units
WINDOW_RESOLUTIONS = {'16x10FHD': (1920, 1080), '16x10low': (1366, 768), '4x3low': (1280, 1024)}  # pixels
WINDOW_RESOLUTION = '16x10low'  # current
WINDOW_RESOLUTION = WINDOW_RESOLUTIONS[WINDOW_RESOLUTION]
FULL_SCREEN = False
WINDOW_MIDDLE = [x // 2 for x in WINDOW_SIZE]
WINDOW_RECT = [0, 0, *WINDOW_SIZE]


# FOV
FOV = 1  # multiplier of screen size
DEFAULT_FOV_W = (WINDOW_SIZE[0] * FOV) // 2
DEFAULT_FOV_H = (WINDOW_SIZE[1] * FOV) // 2

# render rect for fixed must be greater than rect for dynamic
# otherwise dynamic objects may fall through flour
RENDER_RECT_FOR_DYNAMIC = [0, 0, DEFAULT_FOV_W * 2, DEFAULT_FOV_W * 2]
RENDER_RECT_FOR_FIXED = [0, 0, DEFAULT_FOV_W * 3, DEFAULT_FOV_W * 3]


# SOUND
VOLUME = 1


# PHYSICS
BOUNCE = 0.2
AIR_FRICTION = 1
G = 2.2
GRAVITY_VECTOR = Vector2f.xy(0, -G)