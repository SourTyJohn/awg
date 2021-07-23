from core.rendering import PyOGL as Gl
from core.rendering.TextRender import GlText, LocalizedText, MenuFont

from os import listdir

from utils.files import get_full_path

from core.Constants import *
T_ERROR_TEXTURE = Gl.GlTexture.load_file('Devs/r_error.png', repeat=True)


def loadTexturePack(name):
    print(f'\n-- loading Texture Pack: {name}')

    path = get_full_path(name, file_type='tex')
    directories = listdir(path)

    pack = []
    for dr in directories:
        textures = listdir(f'data/Textures/{name}/{dr}')

        for tex in textures:
            t = Gl.GlTexture.load_file(f'{dr}/{tex}', (tex[0] == 'r'))
            pack.append(t)

    print(f'-- Done.\n')
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
            self.textures[x].delete_physic()
        self.textures.clear()

    def keys(self):
        return self.textures.keys()


EssentialTextureStorage = TextureStorage()
DynamicTextureStorage = TextureStorage()


def load_essential():
    pack = loadTexturePack(TEXTURE_PACK)
    EssentialTextureStorage.load(pack)

    buttons_text = [
        GlText(LocalizedText('txt_menu_newgame'), font=MenuFont),
        GlText(LocalizedText('txt_menu_loadgame'), font=MenuFont),
        GlText(LocalizedText('txt_menu_savegame'), font=MenuFont),
        GlText(LocalizedText('txt_menu_settings'), font=MenuFont),
        GlText(LocalizedText('txt_menu_exit'), font=MenuFont),

        GlText(LocalizedText('txt_menu_settings_brightness'), font=MenuFont),
        GlText(LocalizedText('txt_menu_settings_resolution'), font=MenuFont),
        GlText(LocalizedText('txt_menu_settings_volume'), font=MenuFont),
        GlText(LocalizedText('txt_menu_settings_language'), font=MenuFont),
        GlText(LocalizedText('txt_menu_settings_menu'), font=MenuFont),
    ]

    EssentialTextureStorage.load(buttons_text)


load_essential()
