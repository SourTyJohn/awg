from user.KeyMapping import K_CLOSE, K_MOVE_UP, K_MOVE_DOWN, K_MENU_PRESS

from core.rendering.Textures import *
from core.rendering.Textures import EssentialTextureStorage as Ets


decoration = Gl.GLObjectGroup()
back = Gl.GLObjectGroup()

buttons_group = Gl.GLObjectGroup()
buttons_count = 4
selected_button = 0
buttons = []  # list of all buttons
text_group = Gl.GLObjectGroup()

# only on first load
first = True

# You cant Save when you dead
hero_is_alive = True


def init_screen(hero_life=True, first_load=False):
    global buttons

    Gl.camera_apply(WINDOW_RECT)

    global first
    global exit_code
    global hero_is_alive

    exit_code = None
    first = first_load

    MainFrame()

    buttons = [FullButton(730 - x * 120, x) for x in range(5)]
    Button.hover(0, -1)


def close_menu():
    decoration.empty()
    back.empty()
    buttons_group.empty()


exit_code = None


def render():
    global selected_button

    if exit_code:
        close_menu()
        return exit_code

    event = None

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            close_menu()
            return 'Quit'

        if event.type == pygame.KEYDOWN:
            if event.key == K_CLOSE and not first:
                close_menu()
                return 'INIT_game'

            elif event.key == K_MOVE_UP and 0 < selected_button:
                selected_button -= 1
                Button.hover(selected_button, selected_button + 1)

            elif event.key == K_MOVE_DOWN and selected_button < buttons_count:
                selected_button += 1
                Button.hover(selected_button, selected_button - 1)

            elif event.key == K_MENU_PRESS:
                buttons[selected_button].pressed()

    decoration.draw_all()
    buttons_group.draw_all()

    buttons_group.update(event)
    decoration.update()


class MainFrame(Gl.GLObjectBase):
    textures = [Ets['GUI/menu_frame'], ]

    def __init__(self):
        super().__init__(decoration, WINDOW_RECT)


# ---- Buttons ----
class ButtonText(Gl.GLObjectBase):
    textures = [Ets[x] for x in [
        'text:Новая игра', 'text:Загрузить игру', 'text:Сохранить игру', 'text:Настройки', 'text:Выйти'
    ]]

    def __init__(self, number):
        self.texture = number

        super().__init__(text_group, Button.rect.copy())

        self.vertexesObj = ButtonText.textures[number].makeVertexes()
        self.rect.setSize(*ButtonText.textures[number].size)


class Button(Gl.GLObjectBase):
    # 0 - Non Selected Button, 1 - Selected
    textures = [Ets['GUI/button_menu_default'], Ets['GUI/button_menu_selected']]

    size = [720, 80]
    center = WINDOW_MIDDLE[:]
    rect = None

    def __init__(self, y_pos):
        rect = Button.rect.copy()
        rect.setY(y_pos)
        super().__init__(buttons_group, rect)

    @staticmethod
    def hover(this: int, prev: int):
        if -1 < prev <= buttons_count:
            buttons[prev].setTexture(0)
        buttons[this].setTexture(1)


class FullButton(Gl.GLObjectComposite):
    def __init__(self, y_pos, number):
        button = Button(y_pos)
        text = ButtonText(number)
        text.align_center(button)
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
        buttons[selected_button].setRotation((buttons[selected_button][0].rotation + 1) % 2)


Bf = ButtonFunctions
functions = [
    Bf.continueGame,
    0,
    Bf.loadGame,
    0,
    Bf.exitPressed
]
