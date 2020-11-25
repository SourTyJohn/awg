import pygame as pg
import core.rendering.PyOGL as GL
from core.Constants import WINDOW_RESOLUTION, FPS_LOCK, TITLE, FPS_SHOW
from timeit import default_timer as timer


clock: pg.time.Clock


def _main():
    global clock

    pg.init()
    pg.display.set_caption(TITLE)
    pg.mixer.init(channels=3)
    pg.mouse.set_visible(False)
    pg.event.set_allowed([pg.QUIT, pg.KEYDOWN, pg.KEYUP])
    clock = pg.time.Clock()


running = True
screen_type = 'menu'


def game_loop():
    global running, screen_type
    start_time = timer()

    #  Clear screen
    GL.clear_display()

    scr = screens[screen_type]

    exit_code = scr.update(0.017)
    scr.render()

    if FPS_SHOW:  # current FPS display
        print(f'\rFPS: {1 / (timer() - start_time) // 1}', end='')

    if exit_code in ('menu', 'game'):
        if exit_code != screen_type:
            screen_type = exit_code
            screens[exit_code].init_screen()

    elif exit_code == 'Quit':
        running = False

    pg.display.flip()
    clock.tick(FPS_LOCK)


if __name__ == '__main__':
    GL.init_display(WINDOW_RESOLUTION)

    _main()

    import core.screens.menu as rmenu
    import core.screens.game as rgame

    rmenu.init_screen(first_load=True)

    screens = {'menu': rmenu, 'game': rgame}

    while running:
        game_loop()
