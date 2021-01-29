from core.rendering.PyOGL import RenderObjectStatic, RenderGroup, FrameBuffer, clear_display, unbind_framebuff
from core.rendering.Textures import EssentialTextureStorage as Ets
from core.Constants import TILE_SIZE


lights_gr = RenderGroup(shader='LightShader', )
lightBuffer = FrameBuffer()


class LightSource(RenderObjectStatic):
    __slots__ = ('texture', )
    TEXTURES = {
        'round': Ets['Light/round_light'],
        'round_smooth': Ets['Light/round_smooth_light']
    }

    def __init__(self, pos, power, layer=1, form='round', smooth=1.5):
        self.texture = form
        self.smooth = smooth
        super().__init__(lights_gr, pos, (power, power), layer=layer)

    def draw(self, shader, z_rotation=0):
        if self.visible:
            self.curr_image.draw(self.rect.pos, self.vbo, shader, z_rotation=z_rotation, smooth=self.smooth)


class PulstatingLightSource(LightSource):
    __slots__ = ('bound_to', )

    def __init__(self, pos, power, layer=1, form='round', smooth=1.5):
        super().__init__(pos, power, layer, form, smooth)


def add_light(pos, power, light_form, layer=1):
    power *= TILE_SIZE
    return LightSource(pos, power, layer, light_form)


def renderLights():
    lightBuffer.bind()

    clear_display()
    lights_gr.draw_all(True, )

    unbind_framebuff()
