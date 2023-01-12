"""
THIS MODULE CONTAINS ALL DATA DIRECTORIES OF THE GAME
AND ALLOWS EASY ACCESS TO IT
"""

from os.path import join, dirname
from typing import Union

from PIL import ImageFont
import pygame as pg
import json

import os
import shutil
import glob

MAIN_DIRECTORY = dirname(dirname(__file__))
TEXTURES_DIRECTORY = join(MAIN_DIRECTORY, 'data/Textures')
ANIMATIONS_DIRECTORY = join(MAIN_DIRECTORY, 'data/Animations')
SHADERS_DIRECTORY = join(MAIN_DIRECTORY, 'data/Shaders')
DLLS_DIRECTORY = join(MAIN_DIRECTORY, 'data/DLLs')
FONTS_DIRECTORY = join(MAIN_DIRECTORY, 'data/Fonts')
TEXT_LOC_DIRECTORY = join(MAIN_DIRECTORY, 'data/TextLoc')
SOUNDS_DIRECTORY = join(MAIN_DIRECTORY, 'data/Sounds')
SETTINGS_FILE = join(MAIN_DIRECTORY, 'data/settings.json')
MAPS_DIRECTORY = join(MAIN_DIRECTORY, 'data/Maps')
MATERIALS_DIRECTORY = join(MAIN_DIRECTORY, 'data/Materials')


DIRECTORIES = {'main': MAIN_DIRECTORY,
               'tex': TEXTURES_DIRECTORY,
               'anm': ANIMATIONS_DIRECTORY,
               'shd': SHADERS_DIRECTORY,
               'dll': DLLS_DIRECTORY,
               'font': FONTS_DIRECTORY,
               'snd': SOUNDS_DIRECTORY,
               'maps': MAPS_DIRECTORY,
               'mat': MATERIALS_DIRECTORY}


def get_full_path(*path, file_type='main'):
    return join(DIRECTORIES[file_type], *path)


def copy_files(source, where):
    source = os.path.join('data', source)
    where = os.path.join('data', where)

    if os.path.exists(where):
        shutil.rmtree(where)

    os.mkdir(where)

    if os.path.isdir(source):
        for filePath in glob.glob(source + '/*'):
            shutil.copy(filePath, where)


def load_sound(name, ):
    fullname = get_full_path(name, file_type='snd')
    if os.path.exists(fullname):
        return fullname
    raise FileExistsError(f'Not Found: {fullname}')


def load_image(name, pack):
    if pack:
        fullname = get_full_path(pack, name, file_type='tex')
    else:
        fullname = get_full_path(name, file_type='tex')

    if os.path.exists(fullname):
        image = pg.image.load(fullname)
        data = pg.image.tostring(image, 'RGBA')
        return data, image.get_size()
    else:
        return None, ()


def load_font(name, size, index) -> Union[ImageFont.FreeTypeFont, ImageFont.ImageFont]:
    fullname = get_full_path(name, file_type='font')

    if os.path.exists(fullname):
        return ImageFont.truetype(fullname, size, index)
    else:
        return ImageFont.load_default()


def load_text_localization(file: str = None, key: str = None):
    #  file_name of .json localization file or key of language
    if file:
        with open(file) as file:
            data = json.load(file)
            file.close()
            return data['tokens']

    elif key:
        files = os.listdir(TEXT_LOC_DIRECTORY)
        files = [join(TEXT_LOC_DIRECTORY, file) for file in files]
        for file in files:
            with open(file) as file:
                data = json.load(file)
                if not data['key'] == key:
                    file.close()
                    continue

                file.close()
                return data['tokens']

    else:
        raise ValueError('Provide only one of given args: file, key')


def load_map(name):
    fullname = get_full_path(name, file_type='maps')
    if os.path.exists(fullname):
        # TODO: MAPS SHOULD BE COMPRESSED AS FILES
        # HERE YOU SHOULD DECOMPRESS THEM

        with open(fullname, mode="r") as file:
            return file.readlines()

    raise FileExistsError(f'Not Found: {fullname}')


def load_material_preset(name: str, pack: str = None):
    if pack:
        fullname = get_full_path(pack, "presets", name, file_type='mat')
    else:
        fullname = get_full_path(name, "presets", file_type='mat')

    if os.path.exists(fullname) and fullname.endswith(".json"):
        with open(fullname, mode="r") as file:
            return json.load(file)
    else:
        return None


def load_material_texture(name: str, pack: str = None):
    if pack:
        fullname = get_full_path(pack, "textures", name, file_type='mat')
    else:
        fullname = get_full_path(name, "textures", file_type='mat')

    if os.path.exists(fullname):
        image = pg.image.load(fullname)
        data = pg.image.tostring(image, 'RGBA')
        return data, image.get_size()
    else:
        return None, ()
