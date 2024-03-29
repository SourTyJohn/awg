from user.KeyMapping import K_MOVE_UP, K_MOVE_DOWN, K_MENU_PRESS

from core.rendering.PyOGL import *
from core.rendering.Textures import EssentialTextureStorage as Ets


decoration = RenderUpdateGroup()
back = RenderUpdateGroup()
buttons_group = RenderUpdateGroup()

buttons_count = 4
selected_button = 0
buttons = []  # list of all buttons

# only on first load
first = True

# You cant Save when you dead
hero_is_alive = True


def init_screen(hero_life=True, first_load=False):
    global buttons, selected_button
    selected_button = 0

    camera.setField(WINDOW_RECT)

    global first, exit_code, hero_is_alive
    exit_code, first, hero_is_alive = None, first_load, hero_is_alive

    MainFrame()

    buttons = [FullButton(700 - x * 100, x) for x in range(5)]
    Button.hover(0, -1)


def close_menu():
    decoration.delete_all()
    back.delete_all()
    buttons_group.delete_all()


exit_code = None


def render():
    pre_render(do_depth_test=False)
    drawGroups(None, back, decoration, buttons_group)
    post_render(Shaders.shaders['ScreenShaderMenu'], )


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
            exit_code = 'menu'

        if event.type == pygame.KEYDOWN:
            if event.key == K_MOVE_UP and 0 < selected_button:
                selected_button -= 1
                Button.hover(selected_button, selected_button + 1)

            elif event.key == K_MOVE_DOWN and selected_button < buttons_count:
                selected_button += 1
                Button.hover(selected_button, selected_button - 1)

            elif event.key == K_MENU_PRESS:
                buttons[selected_button].pressed()


class MainFrame(StaticRenderComponent):
    TEXTURES = (Ets['GUI/menu_frame'], )
    size = WINDOW_SIZE

    def __init__(self):
        super().__init__(back, WINDOW_MIDDLE)


# ---- BUTTONS----
class ButtonText(StaticRenderComponent):
    TEXTURES = [Ets[x] for x in [
        'txt_settings_brightness', 'txt_settings_resolution', 'txt_settings_volume', 'txt_settings_language', 'txt_settings_menu'
    ]]
    size = (960, 96)

    def __init__(self, number):
        self.texture = number

        drawData = ButtonText.TEXTURES[number].makeDrawData(layer=0)
        super().__init__(None, (0, 0), drawdata=drawData, layer=0)
        self.rect.size = ButtonText.TEXTURES[number].size


class Button(StaticRenderComponent):
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
    def exitPressed(cls):
        global exit_code
        exit_code = 'menu'


Bf = ButtonFunctions
functions = [
    Bf.nullPressed,
    Bf.nullPressed,
    Bf.nullPressed,
    Bf.nullPressed,
    Bf.exitPressed
]
