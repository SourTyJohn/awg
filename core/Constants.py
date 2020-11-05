import pygame
from core.physic.Vector import Vector2f


TITLE = 'AWG 2'
DEBUG = True
GAME_FPS = 60
TEXTURE_PACK = 'base_pack'


pygame.font.init()
FONT = pygame.font.SysFont('Arial Black', 42)
MENU_FONT_COLOR = (52, 6, 52)


WINDOW_SIZE = (1920, 1080)  # units
UNIT_SIZE = 0.5  # pixels
FULL_SCREEN = False
WINDOW_RESOLUTION = [int(x * UNIT_SIZE) for x in WINDOW_SIZE]
WINDOW_MIDDLE = [x // 2 for x in WINDOW_SIZE]
WINDOW_RECT = [0, 0, *WINDOW_SIZE]


FOV = 1  # multiplier of screen size
DEFAULT_FOV_W = (WINDOW_SIZE[0] * FOV) // 2
DEFAULT_FOV_H = (WINDOW_SIZE[1] * FOV) // 2


VOLUME = 1


# PHYSICS
BOUNCE = 0.2

AIR_FRICTION = 1

G = 2
GRAVITY_VECTOR = Vector2f.xy(0, -G)
