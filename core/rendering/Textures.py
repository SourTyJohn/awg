from core.rendering import PyOGL as Gl

from os import listdir

from utils.files import get_full_path

from core.Constants import *
T_ERROR_TEXTURE = Gl.GlTexture.load_image('devs/error.png', repeat=True)


def loadTexturePack(name):
    print(f'\n-- loading Texture Pack: {name}')

    path = get_full_path(name, file_type='tex')
    directories = listdir(path)

    pack = []
    for dr in directories:
        textures = listdir(f'data/Textures/{name}/{dr}')

        for tex in textures:
            t = Gl.GlTexture.load_image(f'{dr}/{tex}', (tex[0] == 'r'))
            pack.append(t)

    print(f'-- Texture Pack: {name} loaded\n')
    return pack


class TextureStorage:
    def __init__(self):
        self.textures = {}

    def __getitem__(self, item):
        if item in self.textures.keys():
            return self.textures[item]
        return T_ERROR_TEXTURE

    def __repr__(self):
        return f'<TextureStorage. Size: {len(self.textures)}\n{self.textures}>'

    def load(self, pack):
        for tex in pack:
            self.textures[tex.name] = tex

    def empty(self):
        for x in self.textures.keys():
            self.textures[x].delete()
        self.textures.clear()

    def keys(self):
        return self.textures.keys()


EssentialTextureStorage = TextureStorage()
DynamicTextureStorage = TextureStorage()


def load_essential():
    pack = loadTexturePack(TEXTURE_PACK)
    EssentialTextureStorage.load(pack)

    buttons_text = [
        Gl.GlTexture.load_text('Новая игра', MENU_FONT_COLOR, FONT),
        Gl.GlTexture.load_text('Загрузить игру', MENU_FONT_COLOR, FONT),
        Gl.GlTexture.load_text('Сохранить игру', MENU_FONT_COLOR, FONT),
        Gl.GlTexture.load_text('Настройки', MENU_FONT_COLOR, FONT),
        Gl.GlTexture.load_text('Выйти', MENU_FONT_COLOR, FONT)
    ]

    EssentialTextureStorage.load(buttons_text)


load_essential()
