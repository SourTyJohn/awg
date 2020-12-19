from user.KeyMapping import K_CLOSE, K_MOVE_UP, K_MOVE_DOWN, K_MENU_PRESS

from core.rendering.Textures import *
from core.rendering.PyOGL import drawGroups
from core.rendering.Textures import EssentialTextureStorage as Ets


decoration = Gl.GLObjectGroupRender()
back = Gl.GLObjectGroupRender()
buttons_group = Gl.GLObjectGroupRender()

buttons_count = 4
selected_button = 0
buttons = []  # list of all buttons

# only on first load
first = True

# You cant Save when you dead
hero_is_alive = True


def init_screen(hero_life=True, first_load=False):
    global buttons, selected_button

    Gl.camera.setField(WINDOW_RECT)

    global first
    global exit_code
    global hero_is_alive

    exit_code = None
    first = first_load

    MainFrame()

    buttons = [FullButton(700 - x * 100, x) for x in range(5)]
    Button.hover(0, -1)
    selected_button = 0


def close_menu():
    decoration.delete_all()
    back.delete_all()
    buttons_group.delete_all()


exit_code = None


def render():
    drawGroups(decoration, buttons_group)


def update(dt):
    if exit_code:
        close_menu()
        return exit_code

    user_input()

    buttons_group.update()
    decoration.update()


def user_input():
    global selected_button, exit_code

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            close_menu()
            exit_code = 'Quit'

        if event.type == pygame.KEYDOWN:
            if event.key == K_CLOSE and not first:
                close_menu()
                exit_code = 'game'

            elif event.key == K_MOVE_UP and 0 < selected_button:
                selected_button -= 1
                Button.hover(selected_button, selected_button + 1)

            elif event.key == K_MOVE_DOWN and selected_button < buttons_count:
                selected_button += 1
                Button.hover(selected_button, selected_button - 1)

            elif event.key == K_MENU_PRESS:
                buttons[selected_button].pressed()


class MainFrame(Gl.GLObjectBase):
    TEXTURES = [Ets['GUI/menu_frame'], ]

    def __init__(self):
        super().__init__(decoration, WINDOW_RECT)


# ---- BUTTONS----
class ButtonText(Gl.GLObjectBase):
    TEXTURES = [Ets[x] for x in [
        'text:Новая игра', 'text:Загрузить игру', 'text:Сохранить игру', 'text:Настройки', 'text:Выйти'
    ]]

    def __init__(self, number):
        self.texture = number

        drawData = ButtonText.TEXTURES[number].makeDrawData()
        super().__init__(None, [0, 0, *Button.size], no_vbo=True)
        self.bindBuffer(drawData)

        self.rect.size = ButtonText.TEXTURES[number].size


class Button(Gl.GLObjectBase):
    # 0 - Non Selected Button, 1 - Selected
    TEXTURES = (Ets['GUI/button_menu_default'], Ets['GUI/button_menu_selected'])

    size = (960, 96)

    def __init__(self, y_pos):
        super().__init__(None, [WINDOW_MIDDLE[0], y_pos, *Button.size])

    @staticmethod
    def hover(this: int, prev: int):
        if -1 < prev <= buttons_count:
            buttons[prev].setTexture(0)
        buttons[this].setTexture(1)


class FullButton(Gl.GLObjectComposite):
    """Button with text on it"""

    def __init__(self, y_pos, number):
        button = Button(y_pos)

        text = ButtonText(number)
        text.rect.pos = button.rect.pos

        super().__init__(buttons_group, button, text)
        self.number = number

    def setTexture(self, tex):
        self[0].setTexture(tex)

    def pressed(self, *args):
        return functions[self.number](*args)


class ButtonFunctions:

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
        buttons[selected_button].rotY(-buttons[selected_button][0].y_Rotation)


Bf = ButtonFunctions
functions = [
    # Here buttons in sorted by up -> down
    Bf.continueGame,
    0,
    Bf.loadGame,
    0,
    Bf.exitPressed
]
