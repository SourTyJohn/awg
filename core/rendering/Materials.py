from core.Constants import STN_MATERIAL_PACK, MAX_TEXTURE_3D_LAYERS, MATERIAL_SIZE
from utils.debug import dprint
from utils.files import get_full_path, load_material_texture, load_material_preset
from core.Exceptions import MaterialRuntimeError

from os import listdir
from os.path import join

from OpenGL.GL import *


def loadMaterialPack(_name):
    print(f'\n-- loading Material Pack: {_name}')

    path = get_full_path(_name, file_type='mat')
    presets = listdir( join( path, "presets" ) )
    textures = listdir( join( path, "textures" ) )

    data_presets = {}
    data_textures = {}

    for p in presets:
        data = load_material_preset(p, _name)
        if data is None: continue
        p_name = ''.join(p.split('.')[:-1])
        data_presets[p_name] = data
        dprint(p)

    for p in textures:
        data, size = load_material_texture(p, _name)
        if data is None: continue
        p_name = ''.join(p.split('.')[:-1])
        data_textures[p_name] = ( data, size )
        dprint(p)

    dprint(f'-- Done.\n')
    return data_presets, data_textures


class MaterialStorage:
    #  TODO: ALLOW SCALE BEYOND 2048 TEXTURES

    def __init__(self, size=( MATERIAL_SIZE, MATERIAL_SIZE )):
        self.__presets = {}  # name: preset
        self.__textures = {}  # name: depth
        self.__size = size
        self.__key = 0

    def initialize(self):
        self.__key = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D_ARRAY, self.__key)
        glTexImage3D(
            GL_TEXTURE_2D_ARRAY, 0, GL_RGBA, self.__size[0], self.__size[1],
            MAX_TEXTURE_3D_LAYERS, 0, GL_RGBA, GL_UNSIGNED_BYTE, None
        )
        glTexParameteri(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexParameterf(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameterf(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glBindTexture(GL_TEXTURE_2D_ARRAY, 0)

    def load(self, presets, textures):
        if self.__key == 0: self.initialize()

        self.__presets = presets

        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D_ARRAY, self.__key)

        for i, ( key, (data, size) ) in enumerate( textures.items() ):
            self.__textures[key] = i

            glTexSubImage3D(
                GL_TEXTURE_2D_ARRAY, 0, 0, 0, i, self.__size[0], self.__size[1], 1, GL_RGBA, GL_UNSIGNED_BYTE, data
            )

        glBindTexture(GL_TEXTURE_2D_ARRAY, 0)

    def get(self, preset: str, texture: str):
        try:
            if preset is None:
                yield None
            else:
                yield self.__presets[preset]
            yield self.__textures[texture]
        except KeyError:
            raise MaterialRuntimeError(f"No such material: PRESET:{preset} TEX:{texture}")

    def bind(self):
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D_ARRAY, self.__key)


EssentialMaterialStorage = MaterialStorage()


def loadMaterials():
    preset, texture = loadMaterialPack(STN_MATERIAL_PACK)
    EssentialMaterialStorage.load(preset, texture)
