import pygame as pg
import core.rendering.PyOGL as GL
from core.Constants import WINDOW_RESOLUTION, FPS_LOCK, TITLE, FPS_SHOW
from timeit import default_timer as timer


clock: pg.time.Clock


def _main():
    global clock

    pg.init()
    pg.display.set_caption(TITLE)
    pg.mouse.set_visible(False)
    pg.event.set_allowed((pg.QUIT, pg.KEYDOWN, pg.KEYUP, pg.MOUSEBUTTONDOWN, ))
    clock = pg.time.Clock()


running = True
screen_type = 'menu'
start_time = None


def game_loop():
    global running, screen_type, start_time

    #  Focus selected screen
    scr = screens[screen_type]

    # Visualization
    scr.render()

    # Update screen
    if start_time:
        dt = timer() - start_time
        exit_code = scr.update(dt)
    else:
        dt = 1
        exit_code = None

    # Timer
    start_time = timer()

    # Current FPS display
    if FPS_SHOW:
        print(f'\rFPS: {1 / dt // 1}', end='')

    # Screen feedback
    if exit_code in ('menu', 'game'):
        if exit_code != screen_type:
            screen_type = exit_code
            screens[exit_code].init_screen()
    elif exit_code == 'Quit':
        running = False

    # End phase
    pg.display.flip()
    clock.tick(FPS_LOCK)


if __name__ == '__main__':
    GL.init_display(WINDOW_RESOLUTION)

    _main()

    import core.screens.menu as rmenu
    import core.screens.game as rgame

    screens = {'menu': rmenu, 'game': rgame}
    screens[screen_type].init_screen(first_load=True)

    while running:
        game_loop()
