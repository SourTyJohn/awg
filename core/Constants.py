import pygame

TITLE = 'AWG 2'
DEBUG = True
GAME_FPS = 60
TEXTURE_PACK = 'base_pack'


pygame.font.init()
FONT = pygame.font.SysFont('Arial Black', 42)
MENU_FONT_COLOR = (52, 6, 52)


WINDOW_SIZE = (1920, 1080)  # units
UNIT_SIZE = 0.5  # pixels
WINDOW_RESOLUTION = [int(x * UNIT_SIZE) for x in WINDOW_SIZE]
WINDOW_MIDDLE = [x // 2 for x in WINDOW_SIZE]
WINDOW_RECT = [0, 0, *WINDOW_SIZE]

VOLUME = 1
