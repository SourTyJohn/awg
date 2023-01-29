from abc import ABC

import pyglet


class GLWindow(pyglet.window.Window, ABC):
    def __init__(self):
        super(GLWindow, self).__init__()

    def on_draw(self, dt):
        pass

    def on_key_press(self, symbol, modifiers):
        pass
