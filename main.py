from core.Constants import FPS_LOCK, TITLE, FPS_SHOW, WINDOW_RESOLUTION
import pygame as pg
from core.rendering.PyOGL import initDisplay
from core.audio.PyOAL import AudioManager
# from cProfile import Profile
# Profile = Profile()


clock: pg.time.Clock


def _main():
    initDisplay(WINDOW_RESOLUTION)
    global clock

    pg.init()
    pg.display.set_caption(TITLE)
    pg.mouse.set_visible(False)
    pg.event.set_allowed((pg.QUIT, pg.KEYDOWN, pg.KEYUP, pg.MOUSEBUTTONDOWN, ))
    clock = pg.time.Clock()


running = True
screen_type = 'menu'
start_time = 0.0
seconds = 0.0


def gameLoop():
    global running, screen_type, start_time, seconds

    #  Focus selected screen
    scr = screens[screen_type]

    # Visualization
    scr.render()

    # Update screen
    dt = clock.tick(FPS_LOCK) / 1000
    exit_code = scr.update(dt)

    seconds += dt
    if seconds >= 1.0:
        seconds = 0.0
        AudioManager.clear_empty_sources()
        # Profile.disable()
        # Profile.print_stats('cumtime')
        # running = False

    AudioManager.update_streams(dt)

    # Screen feedback
    if exit_code in {'menu', 'game', 'Quit'}:
        # if exit_code == 'game':
        #     seconds = 0.0
        #     Profile.enable()

        if exit_code == 'Quit':
            running = False

        elif exit_code != screen_type:
            screen_type = exit_code
            screens[exit_code].initScreen()

    # End phase
    pg.display.flip()
    if FPS_SHOW:
        print(f'\rFPS: {clock.get_fps() // 1}', end='')


if __name__ == '__main__':
    _main()

    import core.screens.menu as rmenu
    import core.screens.game as rgame
    screens = {'menu': rmenu, 'game': rgame}
    screens[screen_type].initScreen(first_load=True)

    while running:
        gameLoop()

    # finally
    AudioManager.destroy()
