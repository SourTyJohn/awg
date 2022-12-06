from user.KeyMapping import K_CLOSE, K_MOVE_UP, K_MOVE_DOWN, K_MENU_PRESS

from core.rendering.PyOGL import *
from core.rendering.Textures import EssentialTextureStorage as Ets

from core.audio.PyOAL import AudioManagerSingleton


decoration = RenderGroup()
back = RenderGroup()
buttons_group = RenderGroup()

buttons_count = 4
selected_button = 0
buttons = []  # list of all buttons

# only on first load
first = True

# You cant Save when you dead
hero_is_alive = True


def initScreen(hero_life=True, first_load=False):
    AudioManagerSingleton.reset_listener()
    AudioManagerSingleton.set_stream('music', 'main_menu', True, volume=0.2)

    global buttons, selected_button
    selected_button = 0

    camera.to_default_position()

    global first, exit_code, hero_is_alive
    exit_code, first, hero_is_alive = None, first_load, hero_is_alive

    MainFrame()

    buttons = [FullButton(700 - x * 100, x) for x in range(5)]
    Button.hover(0, -1)


def closeMenu():
    AudioManagerSingleton.fade_stream('music', 2)
    decoration.delete_all()
    back.delete_all()
    buttons_group.delete_all()


exit_code = None


def render():
    preRender(do_depth_test=False)
    drawGroupsFinally(None, back, decoration, buttons_group)
    postRender(Shaders.shaders['ScreenShaderMenu'], )


def update(dt):
    if exit_code:
        closeMenu()
        return exit_code

    userInput()

    buttons_group.update(dt)
    decoration.update(dt)


def userInput():
    global selected_button, exit_code

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            closeMenu()
            exit_code = 'Quit'

        if event.type == pygame.KEYDOWN:
            if event.key == K_CLOSE and not first:
                closeMenu()
                exit_code = 'game'

            elif event.key == K_MOVE_UP and 0 < selected_button:
                selected_button -= 1
                Button.hover(selected_button, selected_button + 1)

            elif event.key == K_MOVE_DOWN and selected_button < buttons_count:
                selected_button += 1
                Button.hover(selected_button, selected_button - 1)

            elif event.key == K_MENU_PRESS:
                buttons[selected_button].pressed()


class MainFrame(RenderObjectStatic):
    TEXTURES = (Ets['GUI/menu_frame'], )
    size = WINDOW_SIZE

    def __init__(self):
        super().__init__(back, WINDOW_MIDDLE)


# ---- BUTTONS----
class ButtonText(RenderObjectStatic):
    TEXTURES = [Ets[x] for x in [
        'txt_menu_newgame', 'txt_menu_loadgame', 'txt_menu_savegame', 'txt_menu_settings', 'txt_menu_exit'
    ]]
    size = (960, 96)

    def __init__(self, number):
        self.texture = number

        draw_data = ButtonText.TEXTURES[number].make_draw_data(layer=0)
        super().__init__(None, (0, 0), drawdata=draw_data, layer=0)
        self.rect.size = ButtonText.TEXTURES[number].size


class Button(RenderObjectStatic):
    # 0 - Non Selected Button, 1 - Selected
    TEXTURES = (Ets['GUI/button_menu_default'], Ets['GUI/button_menu_selected'])

    size = (960, 96)

    def __init__(self, y_pos):
        super().__init__(None, (WINDOW_MIDDLE[0], y_pos))

    @staticmethod
    def hover(this: int, prev: int):
        if -1 < prev <= buttons_count:
            buttons[prev].setTexture(0)
        buttons[this].setTexture(1)
        AudioManagerSingleton.play_sound('menu_button_select', [0, 0, 0], pitch=(0.9, 1.0))


class FullButton(RenderObjectComposite):
    """Button with text on it"""

    def __init__(self, y_pos, number):
        button = Button(y_pos)

        text = ButtonText(number)
        text.rect.pos = button.rect.pos

        super().__init__(buttons_group, button, text)
        self.number = number

    def setTexture(self, tex):
        self[0].texture = tex

    def pressed(self, *args):
        return functions[self.number](*args)


class ButtonFunctions:

    @classmethod
    def nullPressed(cls):
        pass

    @classmethod
    def continueGame(cls):
        global exit_code
        exit_code = 'game'

    @classmethod
    def exitPressed(cls):
        global exit_code
        exit_code = 'Quit'

    @classmethod
    def loadGame(cls):
        global exit_code
        buttons[selected_button].set_rotation_y(-buttons[selected_button][0].y_Rotation)

    @classmethod
    def openSettings(cls):
        global exit_code
        exit_code = 'settings'


Bf = ButtonFunctions
functions = [
    Bf.continueGame,
    Bf.nullPressed,
    Bf.loadGame,
    Bf.openSettings,
    Bf.exitPressed
]
