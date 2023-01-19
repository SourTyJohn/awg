from core.physic.physics import MainPhysicSpace, objects
from user.KeyMapping import *
from core.objects.gObjects import *
from core.rendering.PyOGL import camera, LightingManager

from core.rendering.Particles import ParticleManager
# from core.rendering.TextRender import TextObject, DefaultFont
from core.audio.PyOAL import AudioManagerSingleton
from core.logic.game_logic import GameContext


import pygame
from beartype import beartype


# GROUPS
game_context = GameContext( )


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
    game_context.render(1)


def update(dt):
    # USER EVENTS
    exit_code = userInput()
    if exit_code:
        return exit_code

    # PHYSIC AND UPDATE [!!! PHYSICS UPDATE FIXED AND NOT BASED ON FPS !!!]
    # TODO: JUST WARNING ^
    dt = MainPhysicSpace.step(dt)

    LightingManager.update(dt)
    updateGroups(dt)
    ParticleManager.update(dt)

    MainPhysicSpace.post_step()

    # SOUND
    AudioManagerSingleton.update_listener(hero.pos, hero.body.velocity)


def userInput():
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

            # elif key == pygame.K_q:
            #     summon('WoodenCrate', obstacles_gr, hero.pos)

            elif key == pygame.K_p:
                LightingManager.newSource("Light/light_round", 0, pos=hero.pos, size=10.0, layer=1,
                                          color="default", brightness=0.6)

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

    updateHeroMovement()
    return None


def updateHeroMovement():
    # update direction hero's walking based on USER INPUT from user_events()
    if holding_keys[K_MOVE_RIGHT]:
        hero.walk_direction = 1
    elif holding_keys[K_MOVE_LEFT]:
        hero.walk_direction = -1
    else:
        hero.walk_direction = 0


@beartype
def updateGroups(dt: float):
    game_context.update(dt)


def initScreen(hero_life=False, first_load=False):
    global hero, hero_inited, render_zone
    game_context.add_single_level_obj( BackgroundColor() )

    #
    # #
    # # #

    game_context.add_single_level_obj(
        WorldRectangleRigid(pos=[0, 500], size=[8192, 64], material=("r_pebble_grass_1", None))
    )
    game_context.add_single_level_obj(
        WorldRectangleRigid(pos=[850, 500], size=[200, 200], material=("r_magma_1", None))
    )

    # """This VVV is a way to the bright future"""
    game_context.add_single_level_obj(
        WorldRectangleRigid(pos=[-400, 660], size=[512, 256], material=("r_devs_1", None))
    )

    for r in range(4):
        game_context.add_single_game_obj( WoodenCrate( pos=[700, 800 + r*20]) )
    #
    # WoodenCrate(obstacles_gr, pos=[760, 800], texture="LevelOne/crate_metal")
    # WoodenCrate(obstacles_gr, pos=[760, 800], texture="LevelOne/crate_metal")
    # WoodenCrate(obstacles_gr, pos=[760, 800], texture="LevelOne/crate_metal")
    # WoodenCrate(obstacles_gr, pos=[760, 800], texture="LevelOne/crate_metal")
    # WoodenCrate(obstacles_gr, pos=[760, 800])
    # WoodenCrate(obstacles_gr, pos=[600, 800])
    # WoodenCrate(obstacles_gr, pos=[650, 980])

    # WorldRectangleSensor(world_gr, (1300, 600), (2600, 900), layer=6)

    _x = 0
    LightingManager.newSource("Light/light_round", 0, pos=(600 + _x * 20, 700), size=40.0, layer=1,
                              color="default", brightness=0.6)
    LightingManager.newSource("Light/light_round", 0, pos=(800, 500), size=30.0, layer=1,
                              color="default", brightness=0.6)
    LightingManager.newSource("Light/light_round", 0, pos=(1000, 800), size=30.0, layer=1,
                              color="default", brightness=0.6)

    # LightingManager.newSource(0, (800, 700), 9, 1, color=(0.1, 0.1, 0.1), brightness=1.0)
    # LightingManager.newSource(0, (600, 900), 9, 1, color=(0.1, 0.1, 0.1), brightness=1.0)
    # LightingManager.newSource(0, (800, 900), 9, 1, color=(0.1, 0.1, 0.1), brightness=1.0)
    # LightingManager.newSource(0, (1000, 700), 9, 1, color=(0.1, 0.1, 0.1), brightness=1.0)
    # LightingManager.newSource(0, (1000, 900), 9, 1, color=(0.1, 0.1, 0.1), brightness=1.0)
    # LightingManager.newSource(0, (400, 700), 9, 1, color=(0.1, 0.1, 0.1), brightness=1.0)
    # LightingManager.newSource(0, (400, 900), 9, 1, color=(0.1, 0.1, 0.1), brightness=1.0)
    # LightingManager.newSource(0, (200, 700), 18, 1)
    #
    # # # #
    # # #
    # #

    hero = game_context.add_single_game_obj( MainHero( [256, 800] ) )
    camera.focused_obj = hero
    # TextObject(background_gr, [256, 800], ['text?', 'text indeed...'], DefaultFont, layer=6, depth_mask=True)

    # GUIHeroHealthBar(gui_gr, [256, 800], layer=0)

    # audio_manager.play_sound('test.ogg')


def close():

    # Stop sounds
    # audio_manager.stop_all_sounds()

    # Delete images
    game_context.clear()

    # Delete physic bodies
    MainPhysicSpace.clear()

    # Delete light sources
    LightingManager.clear()
