from core.physic.Physics import world
from core.rendering.PyOGL import camera, GLObjectGroup, drawGroups, BackgroundColor
from user.KeyMapping import *
from core.Constants import PHYSIC_UPDATE_FREQUENCY
from core.Objects.GameObjects import *

import pygame


background_gr = GLObjectGroup(g_name='g_background')
obstacles_gr = GLObjectGroup(g_name='g_obstacle')
characters_gr = GLObjectGroup(g_name='g_characters')
player_gr = GLObjectGroup(g_name='g_player')

triggers_gr = GLObjectGroup(g_name='g_triggers')


hero_inited = False
# hero: MainHero  # MainHero object


#  Keys that player is holding
holding_keys = {
    K_MOVE_RIGHT: False,
    K_MOVE_LEFT: False,
    K_MOVE_UP: False,
    K_MOVE_DOWN: False
}


def render():
    # CAMERA UPDATE
    camera.focusTo(500, 500)
    background_gr.update(1, camera)

    draw_groups()


def update(dt):
    # USER EVENTS
    exit_code = user_events()
    if exit_code:
        return exit_code

    # PHYSIC AND UPDATE
    # h = hero
    # fixed_objs, dynamic_objs = startPhysics(h)
    # fixed, dynamic  objects that will be updated and rendered

    if dt > PHYSIC_UPDATE_FREQUENCY:
        # t = dt / PHYSIC_UPDATE_FREQUENCY
        #
        # for _ in range(int(t)):
        #     physicsStep(fixed_objs, dynamic_objs, h)
        #     update_groups()
        #
        # t = t % 1
        # physicsStep(fixed_objs, dynamic_objs, h, t)
        # update_groups(t)
        pass

    else:
        # physicsStep(fixed_objs, dynamic_objs, h)
        world.step(1)
        update_groups()


def user_events():
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
    return
    if holding_keys[K_MOVE_RIGHT]:
        hero.walk_direction = 1
    elif holding_keys[K_MOVE_LEFT]:
        hero.walk_direction = -1
    else:
        hero.walk_direction = 0


def draw_groups():
    # drawing all GLSprite groups
    drawGroups(background_gr, obstacles_gr, characters_gr, player_gr)


def update_groups(dt=1):
    # updating all GLSprite groups
    obstacles_gr.update(dt)
    background_gr.update(dt, camera)
    triggers_gr.update(dt)


def init_screen(hero_life=False, first_load=False):
    global hero, hero_inited

    b = BackgroundColor(background_gr)
    WoodenCrate(obstacles_gr, [500, 700])
    WoodenCrate(obstacles_gr, [500, 800])
    WoodenCrate(obstacles_gr, [500, 900])

    WorldRectangleRigid(obstacles_gr, pos=[300, 300], size=[1000, 100])


def close():
    pass
