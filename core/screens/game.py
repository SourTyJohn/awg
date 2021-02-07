from core.physic.physics import world, objects
from user.KeyMapping import *
from core.objects.gObjects import *
from core.objects.gGUI import *
from core.rendering.PyOGL import *
from core.rendering.Lighting import add_light

import pygame


# GROUPS
background_gr = RenderGroup(shader='BackgroundShader')
background_near_gr = RenderGroup()
obstacles_gr = RenderGroup()
characters_gr = RenderGroup()
player_gr = RenderGroup()
front_gr = RenderGroup()
gui_gr = RenderGroup(shader='GUIShader')


hero_inited = False
hero: MainHero  # MainHero object
render_zone: Trigger


#  Keys that player is holding
holding_keys = {
    K_MOVE_RIGHT: False,
    K_MOVE_LEFT: False,
    K_MOVE_UP: False,
    K_MOVE_DOWN: False
}


def render():
    camera.focusTo(*hero.pos)
    background_gr.update(1, camera)

    pre_render()
    draw_groups()
    post_render()


def update(dt):
    # USER EVENTS
    exit_code = user_input()
    if exit_code:
        return exit_code

    # PHYSIC AND UPDATE
    world.step(dt)
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
                summon('WoodenCrate', obstacles_gr, hero.pos)
                # add_light(hero.pos, 12, 'round_smooth')

            elif key == K_GRAB:
                hero.grab_nearest_put(objects)

            elif key == K_CLOSE:
                close()
                return 'menu'

        elif event.type == pygame.KEYUP:
            key = event.key

            if key in holding_keys.keys():
                holding_keys[key] = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            key = event.button

            if key == K_ACTION1:
                hero.throw_grabbed()

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
    drawGroups(None, characters_gr, player_gr, obstacles_gr, front_gr, background_near_gr, background_gr, gui_gr)


def update_groups(dt):
    # updating all GLSprite groups
    player_gr.update(dt)
    obstacles_gr.update(dt)
    background_gr.update(dt, camera)


def init_screen(hero_life=False, first_load=False):
    global hero, hero_inited, render_zone
    BackgroundColor(background_gr)
    # #  render distance
    # render_zone = Trigger(None, 't_*', bound_to=camera, size=WINDOW_SIZE)
    # render_zone.visible = False

    # --- TEST LEVEL ---
    WorldRectangleRigid(obstacles_gr, pos=[0, 500], size=[8192, 64])
    WorldRectangleRigid(obstacles_gr, pos=[850, 700], size=[200, 200])
    a = WorldRectangleRigid(obstacles_gr, pos=[-500, 575], size=[800, 50])
    a.bfriction = 0.0
    #
    # WorldRectangleRigid(obstacles_gr, pos=[1600, 1200], size=[50, 900])
    # WorldRectangleRigid(obstacles_gr, pos=[2000, 1000], size=[50, 900])
    #
    # WorldRectangleSensor(obstacles_gr, pos=[-500, 575], size=[2000, 2000], texture='LevelOne/r_tile_grey_1', layer=0.7)
    #
    MetalCrate(obstacles_gr, pos=[700, 800])
    # WorldRectangleSensor(front_gr, pos=[0, 640], size=[128, 256], texture='LevelOne/glass', layer=1)
    WorldRectangleSensor(background_near_gr, pos=[100, 600], size=[32, 32], texture='LevelOne/glass', layer=4)

    WorldRectangleSensor(background_near_gr, (1300, 600), (900, 256), layer=6)
    add_light([1400, 700], 10, 'round_smooth', layer=1, color='fire')
    add_light([1000, 700], 18, 'round_smooth', 1)
    add_light([600, 700], 18, 'round_smooth', 1)
    add_light([900, 700], 18, 'round_smooth', 1)
    # --- TEST LEVEL ---

    hero = MainHero(player_gr, pos=[256, 800])
    # GUIHeroHealthBar(gui_gr, [256, 800], layer=0)


def close():
    obstacles_gr.delete_all()
