from core.physic.physics import MainPhysicSpace, objects
from user.KeyMapping import *
from core.objects.gObjects import *
from core.rendering.PyOGL import RenderGroup, camera, preRender, postRender, Shaders, drawGroupsFinally
from core.rendering.PyOGL_line import renderAllLines, drawLine
from core.rendering.Lighting import addLight, LightSource, FireLight, clearLights, lights_gr
from core.rendering.Particles import ParticleManager
from core.rendering.TextRender import TextObject, DefaultFont
from core.audio.PyOAL import AudioManager

import pygame
from beartype import beartype


# GROUPS
background_gr = RenderGroup()
background_near_gr = RenderGroup()
obstacles_gr = RenderGroup()
items_gr = RenderGroup(use_depth=False)
characters_gr = RenderGroup()
player_gr = RenderGroup()
front_gr = RenderGroup()
gui_gr = RenderGroup()


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
    camera.focus_to(*hero.pos)
    background_gr.update(1, camera)

    preRender()
    drawGroups()
    renderAllLines()
    ParticleManager.draw(hero.pos, camera)
    postRender(Shaders.shaders['ScreenShaderGame'], )


def drawGroups():
    # drawing all GLSprite groups
    drawGroupsFinally(None, characters_gr, player_gr, obstacles_gr,
                      front_gr, background_near_gr, background_gr, items_gr, gui_gr)
    pass


def update(dt):
    # USER EVENTS
    exit_code = userInput()
    if exit_code:
        return exit_code

    # PHYSIC AND UPDATE [!!! PHYSICS UPDATE FIXED AND NOT BASED ON FPS !!!]
    # TODO: JUST WARNING ^
    updateGroups(dt)
    MainPhysicSpace.step(dt)
    ParticleManager.update(dt)

    # SOUND
    AudioManager.update_listener(hero.pos, hero.body.velocity)


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

            elif key == pygame.K_q:
                summon('WoodenCrate', obstacles_gr, hero.pos)
                # addLight(hero.pos, 12, 'round_smooth')

            elif key == pygame.K_p:
                ParticleManager.create(0, hero.pos, (10, 24), (600, 1200), (1, 2),
                                       (1.0, 1.0, 0.0, 1.0), (10, 24), None, angle=(80, 100), gravity=1000.0)

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
    # updating all GLSprite groups
    player_gr.update(dt)
    obstacles_gr.update(dt)
    background_gr.update(dt, camera)
    lights_gr.update(dt)
    items_gr.update(dt)


def initScreen(hero_life=False, first_load=False):
    global hero, hero_inited, render_zone
    BackgroundColor(background_gr)

    #
    # #
    # # #

    WorldRectangleRigid(obstacles_gr, pos=[0, 500], size=[8192, 64])
    WorldRectangleRigidTrue(obstacles_gr, pos=[850, 500], size=[200, 200])
    # a = WorldRectangleRigid(obstacles_gr, pos=[500, 900], size=[64, 64])
    # b = WoodenCrate(obstacles_gr, pos=[400, 900])

    """This VVV is a way to the bright future"""
    WorldRectangleRigidTrue(obstacles_gr, pos=[-400, 660], size=[512, 256])

    for r in range(4):
        WoodenCrate(obstacles_gr, pos=[700, 800 + r*20])
    WoodenCrate(obstacles_gr, pos=[760, 800])
    WoodenCrate(obstacles_gr, pos=[600, 800])
    DroppedItem(items_gr, pos=[700, 900], item="RustySword")

    WorldRectangleSensor(background_near_gr, (1300, 600), (2600, 900), layer=6)
    addLight(FireLight, [1400, 700], 16, 'RoundFlat', layer=1, color='fire')

    addLight(LightSource, [800, 700], 32, 'Round', 1)
    addLight(LightSource, [600, 700], 18, 'Round', 1)
    addLight(LightSource, [900, 700], 18, 'Round', 1)

    # # #
    # #
    #

    hero = MainHero(player_gr, pos=[256, 800])
    TextObject(background_gr, [256, 800], ['text?', 'text indeed...'], DefaultFont, layer=6, depth_mask=True)

    # GUIHeroHealthBar(gui_gr, [256, 800], layer=0)

    # audio_manager.play_sound('test.ogg')


def close():

    # Stop sounds
    # audio_manager.stop_all_sounds()

    # Delete images
    background_gr.delete_all()
    background_near_gr.delete_all()
    obstacles_gr.delete_all()
    characters_gr.delete_all()
    player_gr.delete_all()
    front_gr.delete_all()
    gui_gr.delete_all()
    items_gr.delete_all()

    # Delete physic bodies
    MainPhysicSpace.clear()

    # Delete light sources
    clearLights()
