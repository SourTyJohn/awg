from core.Constants import *
import pygame as pg

import os
import shutil
import glob

from utils.files import get_full_path


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
        fullname = get_full_path(f'data/Textures/{pack}/{name}')
    else:
        fullname = get_full_path(name)

    print(fullname)

    if os.path.exists(fullname):
        image = pg.image.load(fullname).convert_alpha()
        return 0, image

    else:
        # Default ERROR texture
        image = load_image('data/Textures/error.png')[1].convert()
        return 404, image


# def load_image_raw(name):
