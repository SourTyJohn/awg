"""
THIS MODULE CONTAINS ALL DATA DIRECTORIES OF THE GAME
AND ALLOWS EASY ACCESS TO IT
"""

from os.path import join, dirname
from core.Constants import *
import pygame as pg

import os
import shutil
import glob

MAIN_DIRECTORY = dirname(dirname(__file__))
TEXTURES_DIRECTORY = join(MAIN_DIRECTORY, 'data/Textures')
ANIMATIONS_DIRECTORY = join(MAIN_DIRECTORY, 'data/Animations')
SHADERS_DIRECTORY = join(MAIN_DIRECTORY, 'data/Shaders')
DLLS_DIRECTORY = join(MAIN_DIRECTORY, 'data/DLLs')


DIRECTORIES = {'main': MAIN_DIRECTORY,
               'tex': TEXTURES_DIRECTORY,
               'anm': ANIMATIONS_DIRECTORY,
               'shd': SHADERS_DIRECTORY,
               'dll': DLLS_DIRECTORY}


ERROR_TEXTURE_FILE = join(TEXTURES_DIRECTORY, 'error.png')


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


def load_sound(name, volume=None):
    if volume is None:
        volume = VOLUME
    fullname = get_full_path(f'data/Sounds/{name}')
    if os.path.exists(fullname):
        sound = pg.mixer.Sound(fullname)
    else:
        sound = pg.mixer.Sound(os.path.join('data', 'Defaults/bruh.wav'))

    sound.set_volume(volume)
    return sound


def load_image(name, pack=None):
    if pack:
        fullname = get_full_path(pack, name, file_type='tex')
    else:
        fullname = get_full_path(name, file_type='tex')

    if os.path.exists(fullname):
        image = pg.image.load(fullname).convert_alpha()
        return 0, image

    else:
        # Default ERROR texture
        image = load_image(ERROR_TEXTURE_FILE)[1].convert()
        return 404, image
