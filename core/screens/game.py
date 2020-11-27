from core.physic.Physics import physicsStep, startPhysics, vanish_objects
from core.rendering.PyOGL import camera, GLObjectGroup, drawGroups
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
    # VISUAL
    camera.focusTo(*hero.rect.getPos())
    draw_groups()


def update(dt):
    # USER EVENTS
    exit_code = user_events()
    if exit_code:
        return exit_code

    # PHYSIC AND UPDATE
    h = hero
    fixed_objs, dynamic_objs = startPhysics(h)  # fixed, dynamic  objects that will be updated and rendered

    if dt > PHYSIC_UPDATE_FREQUENCY:
        t = dt / PHYSIC_UPDATE_FREQUENCY

        for _ in range(int(t)):
            physicsStep(fixed_objs, dynamic_objs, h)
            update_groups()

        t = t % 1
        physicsStep(fixed_objs, dynamic_objs, h, t)
        update_groups(t)

    else:
        physicsStep(fixed_objs, dynamic_objs, h)
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
    background_gr.update(dt, camera)
    triggers_gr.update(dt)


def init_screen(hero_life=False, first_load=False):
    global hero, hero_inited

    WorldRectangleRigid(obstacles_gr, [-1000, 0], [5500, 200])
    WorldRectangleRigid(obstacles_gr, [800, 200], [80, 400])
    WorldRectangleRigid(obstacles_gr, [500, 400], [800, 40])

    WoodenCrate(obstacles_gr, [600, 700])
    WoodenCrate(obstacles_gr, [600, 800])
    WoodenCrate(obstacles_gr, [600, 900])
    WoodenCrate(obstacles_gr, [600, 600])

    b = WoodenCrate(obstacles_gr, [700, 700])
    WoodenCrate(obstacles_gr, [700, 800])
    WoodenCrate(obstacles_gr, [700, 900])
    WoodenCrate(obstacles_gr, [700, 600])

    WoodenCrate(obstacles_gr, [500, 700])
    WoodenCrate(obstacles_gr, [500, 800])
    WoodenCrate(obstacles_gr, [500, 900])
    a = WoodenCrate(obstacles_gr, [500, 600])
    vanish_objects(a.id, b.id)

    MetalCrate(obstacles_gr, [1000, 400])

    a = WorldRectangleRigid(obstacles_gr, [-500, 200], [420, 50])
    a.bouncy = 3

    WorldRectangleRigid(obstacles_gr, [-500, 400], [256, 256 + 256])

    # b = Background(background_gr, 1, [0, -1080], 'Backgrounds/back1', )

    # if not hero_inited:
    hero = MainHero(player_gr, [250, 400])
    hero.addVelocity([50, 0])
    hero_inited = True


def close():
    pass
