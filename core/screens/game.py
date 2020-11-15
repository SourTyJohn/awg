from core.physic.Physics import GLObjectGroup, applyPhysics, startPhysics
from core.rendering.PyOGL import focus_camera_to
from core.Objects.GameObjects import *
from user.KeyMapping import *
from core.Constants import PHYSIC_UPDATE_FREQUENCY

import pygame


background_gr = GLObjectGroup()
obstacles_gr = GLObjectGroup()
characters_gr = GLObjectGroup()
player_gr = GLObjectGroup()

triggers_gr = GLObjectGroup()


hero_inited = False
hero: MainHero  # MainHero object


#  Keys that player is holding
holding_keys = {
    K_MOVE_RIGHT: False,
    K_MOVE_LEFT: False,
    K_MOVE_UP: False,
    K_MOVE_DOWN: False
}


def render():
    focus_camera_to(*hero.rect.getPos())

    exit_code = user_events()
    if exit_code:
        return exit_code

    draw_groups()


def update(dt):
    h = hero
    f, d = startPhysics(h)

    if dt > PHYSIC_UPDATE_FREQUENCY:
        t = dt / PHYSIC_UPDATE_FREQUENCY
        for _ in range(int(t)):

            update_groups()
            applyPhysics(f, d, h)

        t = t % 1
        update_groups(t)
        applyPhysics(f, d, h, t)

    else:
        update_groups()
        applyPhysics(f, d, h)

    update_groups()


def user_events():
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return 'Quit'

        elif event.type == pygame.KEYDOWN:
            key = event.key

            if key in holding_keys.keys():
                holding_keys[key] = True

            elif key == K_MOVE_JUMP:
                hero.jump()

            elif key == K_CLOSE:
                close()
                return 'menu'

        elif event.type == pygame.KEYUP:
            key = event.key

            if key in holding_keys.keys():
                holding_keys[key] = False

    update_hero_movement()

    return None


def update_hero_movement():
    if holding_keys[K_MOVE_RIGHT]:
        hero.walk_direction = 1

    elif holding_keys[K_MOVE_LEFT]:
        hero.walk_direction = -1

    else:
        hero.walk_direction = 0


def draw_groups():
    background_gr.draw_all()
    obstacles_gr.draw_all()
    characters_gr.draw_all()
    player_gr.draw_all()


def update_groups(dt=1):
    characters_gr.update(dt)
    triggers_gr.update(dt)


def init_screen(hero_life=False, first_load=False):
    global hero, hero_inited

    WorldRectangle(obstacles_gr, [-1000, 100], [5500, 200])
    WorldRectangle(obstacles_gr, [800, 300], [80, 400])
    WorldRectangle(obstacles_gr, [500, 500], [800, 40])

    WoodenCrate(obstacles_gr, [600, 700])
    WoodenCrate(obstacles_gr, [600, 800])
    WoodenCrate(obstacles_gr, [600, 900])
    WoodenCrate(obstacles_gr, [600, 600])

    MetalCrate(obstacles_gr, [1000, 400])

    if not hero_inited:
        hero = MainHero(player_gr, [250, 400])
        hero.addVelocity([50, 0])
        hero_inited = True

    WorldRectangle(obstacles_gr, [-500, 300], [500, 10])
    WorldRectangle(obstacles_gr, [-500, 310], [460, 10])
    a = WorldRectangle(obstacles_gr, [-500, 320], [420, 10])
    a.bouncy = 1


def close():
    background_gr.empty()
    obstacles_gr.empty()
    characters_gr.empty()
    player_gr.empty()
    triggers_gr.empty()