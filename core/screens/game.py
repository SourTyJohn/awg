from core.physic.Physics import GLObjectGroup, Rect
from core.objects.GameObjects import *
import pygame


background_gr = GLObjectGroup()
obstacles_gr = GLObjectGroup()
characters_gr = GLObjectGroup()
player_gr = GLObjectGroup()

triggers_gr = GLObjectGroup()


def render():
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return 'Quit'

    update_and_draw()


def update_and_draw():
    background_gr.update()
    obstacles_gr.update()
    characters_gr.update()
    player_gr.update()
    triggers_gr.update()

    background_gr.draw_all()
    obstacles_gr.draw_all()
    characters_gr.draw_all()
    player_gr.draw_all()


def init_screen(hero_life=False, first_load=False):
    WorldRectangle(player_gr, [100, 100], [250, 500])


def close():
    pass
