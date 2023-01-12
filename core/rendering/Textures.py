from OpenGL.GL import *

from core.rendering.PyOGL_utils import makeGLTexture, drawData
from core.Constants import *

from utils.files import get_full_path, load_image
from utils.debug import dprint

from os import listdir
import numpy as np


def loadTexturePack(_name):
    print(f'\n-- loading Texture Pack: {_name}')

    path = get_full_path(_name, file_type='tex')
    directories = listdir(path)

    pack = []
    for dr in directories:
        textures = listdir(f'data/Textures/{_name}/{dr}')

        for tex in textures:
            if not tex.endswith(".png"): continue
            t = GlTexture.load_file(f'{dr}/{tex}')
            pack.append(t)

    dprint(f'-- Done.\n')
    return pack


class TextureStorage:
    def __init__(self):
        self.textures = {}
        self.error_tex = None

    def __getitem__(self, item):
        if item in self.textures.keys():
            return self.textures[item]

        if not self.error_tex:
            self.error_tex = GlTexture.load_file('Devs/r_error.png')
        return self.error_tex

    def __repr__(self):
        return f'<TextureStorage. Size: {len(self.textures)}\n{self.textures}>'

    def load(self, pack):
        for tex in pack:
            self.textures[tex.name] = tex

    def empty(self):
        for t in self.textures.keys():
            self.textures[t].delete_from_physic()
        self.textures.clear()

    def keys(self):
        return self.textures.keys()


class GlTexture:
    __slots__ = ('size', 'key', 'name', 'normals')

    def __init__(self, data: np.ndarray, size, tex_name):
        self.size = size  # units
        self.key = makeGLTexture(data, *self.size)
        self.name = tex_name.replace('.png', '')
        dprint( self )

    def __repr__(self):
        return f'<GLTexture[{self.key}] \t size: {self.size[0]}x{self.size[1]}px. \t name: "{self.name}">'

    @classmethod
    def load_file(cls, image_name):
        data, size = load_image(image_name, STN_TEXTURE_PACK)

        if data is None:
            print(f'texture: {image_name} error. Not loaded')
        return GlTexture(data, size, image_name)

    @classmethod
    def load_image(cls, image_name, image):
        data = np.fromstring(image.tobytes(), np.uint8)
        size = image.size
        return GlTexture(data, size, image_name)

    def make_draw_data(self, layer, colors=None):
        """Make drawTexture data with size of this texture
        Usually GlObjects have their own drawData, but you can calculate drawData,
        which will perfectly match this texture"""
        if colors is None:
            colors = ((1.0, 1.0, 1.0, 1.0), ) * 4

        drawData(self.size, colors, layer=layer)
        return drawData(self.size, colors, layer=layer)

    """Deleting texture from memory"""
    def delete(self):
        glDeleteTextures(1, [self.key, ])
        del self


EssentialTextureStorage = TextureStorage()
DynamicTextureStorage = TextureStorage()


def loadTextures():
    pack = loadTexturePack(STN_TEXTURE_PACK)
    EssentialTextureStorage.load(pack)
