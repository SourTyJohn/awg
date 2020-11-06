from core.physic.Physics import GLObjectGroup, applyPhysics, Vector2f
from core.rendering.PyOGL import focus_camera_to, draw_line
from core.objects.GameObjects import *
from user.KeyMapping import *
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
    exit_code = user_events()
    if exit_code:
        return exit_code

    update_hero_movement()
    applyPhysics(1)
    update_and_draw()

    focus_camera_to(*hero.rect.getPos())


def user_events():
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return 'Quit'

        elif event.type == pygame.KEYDOWN:
            key = event.key

            if key in holding_keys.keys():
                holding_keys[key] = True

            elif key == K_MOVE_JUMP:
                hero.addVelocity([0, 36])

            elif key == K_CLOSE:
                close()
                return 'menu'

        elif event.type == pygame.KEYUP:
            key = event.key

            if key in holding_keys.keys():
                holding_keys[key] = False

    return None


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


def update_hero_movement():
    if holding_keys[K_MOVE_RIGHT]:
        hero.walk(Vector2f.xy(2, 0))

    if holding_keys[K_MOVE_LEFT]:
        hero.walk(Vector2f.xy(-2, 0))


def init_screen(hero_life=False, first_load=False):
    global hero, hero_inited

    WorldRectangle(obstacles_gr, [-200, 100], [2500, 200])
    WorldRectangle(obstacles_gr, [800, 300], [80, 400])
    WorldRectangle(obstacles_gr, [500, 500], [800, 40])

    WoodenCrate(obstacles_gr, [600, 700])
    WoodenCrate(obstacles_gr, [600, 800])
    WoodenCrate(obstacles_gr, [600, 900])
    WoodenCrate(obstacles_gr, [600, 600])

    if not hero_inited:
        hero = MainHero(player_gr, [250, 400])
        hero.addVelocity([50, 0])
        hero_inited = True


def close():
    background_gr.empty()
    obstacles_gr.empty()
    characters_gr.empty()
    player_gr.empty()
    triggers_gr.empty()
