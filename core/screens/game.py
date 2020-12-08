from core.physic.Physics import world, new_triggers
from core.rendering.PyOGL import camera, GLObjectGroupRender, drawGroups
from user.KeyMapping import *
from core.Objects.GameObjects import *

import pygame


background_gr = GLObjectGroupRender(g_name='g_background', shader='BackgroundShader')
obstacles_gr = GLObjectGroupRender(g_name='g_obstacle')
characters_gr = GLObjectGroupRender(g_name='g_characters')
player_gr = GLObjectGroupRender(g_name='g_player')

triggers_gr = GLObjectGroupRender(g_name='g_triggers')


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
    camera.focusTo(*hero.getPos())
    background_gr.update(1, camera)
    draw_groups()


def update(dt):
    # USER EVENTS
    exit_code = user_input()
    if exit_code:
        return exit_code

    # PHYSIC AND UPDATE
    world.step(dt)

    """new_triggers - set of Trigger objects from Physics.py,
    that were added recently and needs to be added to object group
    Physic.py module can't access object groups from game module
    so it pass new triggers through new_triggers set, to add it to group here"""
    while new_triggers:
        triggers_gr.add(new_triggers.pop())

    update_groups(dt)


def user_input():
    # USER INPUT
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return 'Quit'

        elif event.type == pygame.KEYDOWN:
            key = event.key

            if key in holding_keys.keys():
                holding_keys[key] = True

            elif key == K_MOVE_JUMP:
                hero.jump()

            elif key == pygame.K_q:
                WoodenCrate(obstacles_gr, hero.getPos())

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
    # update direction hero's walking based on USER INPUT from user_events()
    if holding_keys[K_MOVE_RIGHT]:
        hero.walk_direction = 1
    elif holding_keys[K_MOVE_LEFT]:
        hero.walk_direction = -1
    else:
        hero.walk_direction = 0


def draw_groups():
    # drawing all GLSprite groups
    drawGroups(background_gr, obstacles_gr, characters_gr, player_gr)


def update_groups(dt):
    # updating all GLSprite groups
    player_gr.update(dt)
    obstacles_gr.update(dt)
    background_gr.update(dt, camera)
    triggers_gr.update(dt)


def init_screen(hero_life=False, first_load=False):
    global hero, hero_inited

    BackgroundColor(background_gr)
    WorldRectangleRigid(obstacles_gr, pos=[0, 500], size=[4100, 100])
    WorldRectangleRigid(obstacles_gr, pos=[850, 700], size=[200, 200])

    a = WorldRectangleRigid(obstacles_gr, pos=[-500, 575], size=[800, 50])
    a.bfriction = 0.0

    WorldRectangleRigid(obstacles_gr, pos=[1600, 1200], size=[50, 900])
    WorldRectangleRigid(obstacles_gr, pos=[2000, 1000], size=[50, 900])

    MetalCrate(obstacles_gr, pos=[700, 800])
    hero = MainHero(player_gr, pos=[500, 800])


def close():
    obstacles_gr.delete_all()
    triggers_gr.delete_all()
