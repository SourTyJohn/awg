from core.rendering.PyOGL import *
from core.Constants import TILE_SIZE
from random import randint


lights_gr = RenderGroup()
lightBuffer = FrameBuffer()

light_colors_presets = {
    'fire': (1.0, 0.3, 0.0, 0.0)
}


do_render_light = True


class LightSource(RenderObjectStatic):
    __slots__ = ('texture', )

    def __init__(self, pos, power, layer=1, ltype='Round', color=(1.0, 1.0, 1.0, 1.0)):
        self.shader: Shaders.Shader = f'{ltype}LightShader'
        self.colors = [color, color, color, color]
        size = (power, power)
        super().__init__(lights_gr, pos, size, layer=layer)

    def draw(self):
        if self.visible:
            self.shader.use()
            drawTexture(0, self.rect.pos, self._vbo, self.shader, z_rotation=0)


class FireLight(LightSource):
    __slots__ = ('min_noise', 'max_noise', 'noise_frequency', 'time', 'noise')

    def __init__(self, pos, power, layer=1, ltype='Round', color=(1.0, 1.0, 1.0, 1.0)):
        super().__init__(pos, power, layer, ltype, color)

        self.min_noise = 50
        self.max_noise = 75

        self.noise_frequency = 0.1
        self.time = 0
        self.prev_noise = 0
        self.noise = randint(self.min_noise, self.max_noise) / 100

    def draw(self):
        if self.visible:
            self.shader.use()
            drawTexture(0, self.rect.pos, self._vbo, self.shader, z_rotation=0, noise=self.noise)

    def update(self, *args, **kwargs) -> None:
        self.time += args[0]
        if self.time >= self.noise_frequency:
            self.noise = randint(self.min_noise, self.max_noise) / 100
            self.time = 0


def addLight(ltype, pos, power, light_form, layer=1, color=(0.1, 0.1, 0.1, 0.1)):
    if isinstance(color, str):
        try:
            color = light_colors_presets[color]
        except KeyError:
            raise KeyError(f'No such color preset. Chose from {light_colors_presets.keys()}')

    power *= TILE_SIZE
    return ltype(pos, power, layer, light_form, color=color)


def renderLights():
    lightBuffer.bind()
    clearDisplay()

    # glBlendFuncSeparate(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA, GL_ONE, GL_ONE)

    if do_render_light:
        lights_gr.draw_all(True, )

    # glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    unbindFrameBuffer()


def clearLights():
    lights_gr.delete_all()
