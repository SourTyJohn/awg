from core.rendering.PyOGL import GlTexture
from utils.files import load_font, load_text_localization
from core.Constants import FONT_SETTINGS, settings
from PIL import Image, ImageDraw
from core.rendering.PyOGL import RenderObjectStatic, bufferize, drawData
from OpenGL.GL import glEnable, glDisable, GL_DEPTH_TEST
import numpy as np


MAX_FONTS = 256  # System max is 256
EssentialFontsStorage = [0, ] * MAX_FONTS
efs_free_ids = set(range(0, MAX_FONTS + 1))


def newFont(family, size, key: int = None):
    if key is None:
        try:
            key: int = efs_free_ids.pop()
        except KeyError:
            raise OSError("EssentialFontsStorage overloaded. Max font's count is 256")

    font = load_font(family, size, 0)
    EssentialFontsStorage[key] = font
    return font


def deleteFont(font=None, key: int = None):
    try:
        assert font is not None and key is None
        assert font is None and key is not None
    except AssertionError:
        raise ValueError('Provide one of the given arguments: font, key')
    else:
        if font is not None:
            try:
                key = EssentialFontsStorage.index(font)
            except ValueError:
                raise ValueError(f'There is no such font:{font}')

            EssentialFontsStorage[key] = 0
            efs_free_ids.add(key)
        else:
            EssentialFontsStorage[key] = 0
            efs_free_ids.add(key)


DefaultFont = newFont(*FONT_SETTINGS)
MenuFont = newFont(FONT_SETTINGS[0], 64)


LocalizedTextsStorage = {}


def loadText():
    global LocalizedTextsStorage
    lts = load_text_localization(key=settings['Language'])
    LocalizedTextsStorage = {f'txt_{key}': lts[key] for key in lts.keys()}


loadText()


class LocalizedText:
    __slots__ = ("token", )

    def __init__(self, token, ):
        self.token = token

    def __call__(self):
        return LocalizedTextsStorage[self.token]


class GlText(GlTexture):
    __slots__ = ()

    def __init__(self, text='', font=DefaultFont):
        if isinstance(text, LocalizedText):
            name = text.token
            text = text()
        else:
            name = f'txt_{text}'

        """text can be set as list of lines"""
        if isinstance(text, list):
            width = 0
            height = 0

            for line in text:
                size = font.getsize(line)
                if size[0] > width:
                    width = size[0]
                height += size[1]

            size = (width, height)
            text = '\n'.join(text)

        else:
            size = font.getsize(text)

        image = Image.new("RGBA", size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)

        draw.text((0, 0), text, fill=(0, 0, 0, 255), font=font)
        image = image.crop(image.getbbox())
        data = np.fromstring(image.tobytes(), np.uint8)
        super().__init__(data, image.size, tex_name=name)


TextTextures = {}


class TextObject(RenderObjectStatic):
    TEXTURES = TextTextures

    shader = 'GUIShader'

    def __init__(self, gr, pos, text, font, colors=None, layer=5, depth_mask=False):
        self.depth_mask = depth_mask
        """If you set depth_mask to true, than this object will take part in GL_DEPTH_TEST
        and you should set text's layer same with the object, overlapped by this text,
        otherwise it can cause lighting bugs"""

        if colors:
            self.colors = colors

        """For each text new texture is created and added to TextTextures dictionary"""
        texture = GlText(text, font)
        self.texture = texture.key
        TextTextures[self.texture] = texture
        super().__init__(gr, pos, texture.size, layer=layer, )

    def draw(self, shader, z_rotation=0):
        if self.depth_mask:
            super().draw(shader, z_rotation)
        else:
            glDisable(GL_DEPTH_TEST)
            super().draw(shader, z_rotation)
            glEnable(GL_DEPTH_TEST)

    def clear(self):
        TextTextures[self.texture].delete()
        del TextTextures[self.texture]
        self.texture = None
        self.visible = False

    def set_text(self, text, font, colors=None, rotation=1, make_visible=True):
        self.clear()

        texture = GlText(text, font)
        self.texture = texture.key
        TextTextures[self.texture] = texture

        if colors is None:
            colors = [(1.0, 1.0, 1.0, 1.0), (1.0, 1.0, 1.0, 1.0), (1.0, 1.0, 1.0, 1.0), (1.0, 1.0, 1.0, 1.0)]

        bufferize(
            drawData(texture.size, colors, rotation=rotation, layer=self._layer), self.vbo
        )

        if make_visible:
            self.visible = True
