from core.Constants import FPS_LOCK, TITLE, FPS_SHOW, STN_WINDOW_RESOLUTION
from core.rendering.PyOGL import initDisplay
from core.audio.PyOAL import AudioManagerSingleton
from core.rendering.TextRender import loadText
from core.rendering.Textures import loadTextures
from core.rendering.Materials import loadMaterials

import pygame as pg


from cProfile import Profile
Profile = Profile()

clock: pg.time.Clock


def _main():
    initDisplay(STN_WINDOW_RESOLUTION)
    loadText()
    loadTextures()
    loadMaterials()

    global clock

    pg.init()
    pg.display.set_caption(TITLE)
    pg.mouse.set_visible(False)
    pg.event.set_allowed((pg.QUIT, pg.KEYDOWN, pg.KEYUP, pg.MOUSEBUTTONDOWN, ))
    clock = pg.time.Clock()


running = True
screen_type = 'game'
start_time = 0.0
seconds = 0.0


def gameLoop():
    global running, screen_type, start_time, seconds

    #  Focus selected screen
    scr = screens[screen_type]

    # Visualization
    scr.render()
    pg.display.flip()

    # Update screen
    dt = clock.tick(FPS_LOCK) / 1000
    exit_code = scr.update(dt)

    seconds += dt
    AudioManagerSingleton.clear_empty_sources()
    if seconds >= 10:
        seconds = 0.0
        Profile.disable()
        Profile.print_stats('cumtime', )
        running = False

    AudioManagerSingleton.update_streams(dt)

    # Screen feedback
    if exit_code in {'menu', 'game', 'Quit'}:
        if exit_code == 'game':
            seconds = 0.0

        if exit_code == 'Quit':
            running = False

        elif exit_code != screen_type:
            screen_type = exit_code
            screens[exit_code].initScreen()

    # End phase
    if FPS_SHOW:
        print(f'\rFPS: {clock.get_fps() // 1}', end='')


if __name__ == '__main__':
    _main()
    Profile.enable()

    import core.screens.menu as rmenu
    import core.screens.game as rgame
    screens = {'menu': rmenu, 'game': rgame}
    screens[screen_type].initScreen(first_load=True)

    while running:
        gameLoop()

    # finally
    AudioManagerSingleton.destroy()
