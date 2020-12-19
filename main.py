import pygame as pg
import core.rendering.PyOGL as GL
from core.Constants import WINDOW_RESOLUTION, DEDICATED_RESOLUTION, FPS_LOCK, TITLE, FPS_SHOW
from timeit import default_timer as timer
import sys

clock: pg.time.Clock

ClientLaunch: bool = True

def _main():
    global clock

    pg.init()
    pg.display.set_caption(TITLE)
    pg.mixer.init(channels=3)
    pg.mouse.set_visible(False)
    pg.event.set_allowed([pg.QUIT, pg.KEYDOWN, pg.KEYUP])


running = True
screen_type = 'menu'
start_time = None


def game_loop():
    global running, screen_type, start_time

    #  Clear screen
    GL.clear_display()

    #  Focus selected screen
    scr = screens[screen_type]

    # Update screen
    if start_time:
        exit_code = scr.update(timer() - start_time)
    else:
        exit_code = None

    # Visualization
    if ClientLaunch == True:
        scr.render()
    else:
        scr.render_dedicated()

    # Timer
    start_time = timer()

    # Current FPS display
    if FPS_SHOW:
        print(f'\rFPS: {1 / (timer() - start_time) // 1}', end='')

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
     for param in sys.argv:
        if param == "-server":
            GL.init_display(DEDICATED_RESOLUTION)
            import core.screens.game as rgame

            screens = {'game': rgame}

            screen_type = 'game'

            clock = pg.time.Clock()

            rgame.init_screen(is_dedicated=True)
            ClientLaunch = False
     
     if ClientLaunch == True:
        GL.init_display(WINDOW_RESOLUTION)

        import core.screens.menu as rmenu
        import core.screens.game as rgame

        screens = {'menu': rmenu, 'game': rgame}

        _main()
        clock = pg.time.Clock()

        rmenu.init_screen(first_load=True)

     while running:
        game_loop()