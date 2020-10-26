import pygame as pg
import core.rendering.PyOGL as GL
from core.Constants import WINDOW_RESOLUTION, GAME_FPS, TITLE


version = '0.0.1'

clock: pg.time.Clock = None


def main():
    global clock

    pg.init()
    pg.display.set_caption(TITLE)
    pg.mixer.init(channels=3)
    pg.mouse.set_visible(False)
    clock = pg.time.Clock()


running = True
screen_type = 'menu'


def game_loop():
    global running, screen_type

    GL.clear_display()

    exit_code = screens[screen_type].render()

    if exit_code in ('menu', 'game'):
        if exit_code != screen_type:
            screen_type = exit_code
            screens[exit_code].init_screen()

    elif exit_code == 'Quit':
        running = False

    clock.tick(GAME_FPS)
    pg.display.flip()


if __name__ == '__main__':
    GL.init_display(WINDOW_RESOLUTION)

    main()

    import core.screens.menu as rmenu
    import core.screens.game as rgame

    rmenu.init_screen()

    screens = {'menu': rmenu, 'game': rgame}

    while running:
        game_loop()
