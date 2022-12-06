from core.Constants import FLOAT32, LIGHT_POWER_UNIT
from typing import Union, List, Tuple

from OpenGL.GL import *
import numpy as np

__all__ = [
    "makeGLTexture",
    "bufferize",
    "drawDataFullScreen",
    "drawData",
    "splitDrawData",
    "zFromLayer",
    "drawDataLightSource"
]


def makeGLTexture(image_data: np.ndarray, w: int, h: int, repeat=False) -> int:
    """Loading pygame.Surface as OpenGL texture
    :return New Texture key"""

    # getting data from pygame.Surface

    # bind new texture
    key = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, key)

    # SETTING UP
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)  # настройка сжатия
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)  # настройка растяжения

    if repeat:
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)

    glTexImage2D(GL_TEXTURE_2D, GL_ZERO, GL_RGBA, w, h, GL_ZERO, GL_RGBA, GL_UNSIGNED_BYTE, image_data)
    #

    # unbind new texture
    glBindTexture(GL_TEXTURE_2D, 0)

    return key


def bufferize(data: np.ndarray, vbo=None) -> int:
    """Generating Buffer to store this object's vertex data,
    necessary for drawing"""
    if vbo is None:
        vbo = glGenBuffers(1)

    glBindBuffer(GL_ARRAY_BUFFER, vbo)
    glBufferData(GL_ARRAY_BUFFER, data.nbytes, data, GL_STATIC_DRAW)

    return vbo


def drawData(size: tuple, colors: Union[List, Tuple, np.ndarray], rotation=1, layer=5) -> np.ndarray:
    # ::arg layer - value from 0 to 10
    # lower it is, nearer object to a camera
    assert 0 <= layer <= 10 and isinstance(layer, int), f'Wrong layer param: {layer}. ' \
                                                        f'Should be integer from 1 to 10'
    z = zFromLayer(layer)

    w_t, h_t = 1, 1
    w_o, h_o = size[0] / 2, size[1] / 2

    # right (base)
    if rotation == 1:
        data = np.array([
            # obj cords    # color       # tex cords
            -w_o, -h_o, z, *colors[0],   0.0, h_t,
            +w_o, -h_o, z, *colors[1],   w_t, h_t,
            +w_o, +h_o, z, *colors[2],   w_t, 0.0,
            -w_o, +h_o, z, *colors[3],   0.0, 0.0,
        ], dtype=FLOAT32)

    # left (mirrored)
    else:
        data = np.array([
            # obj cords    # color       # tex cords
            -w_o, -h_o, z, *colors[0],   w_t, h_t,
            +w_o, -h_o, z, *colors[1],   0.0, h_t,
            +w_o, +h_o, z, *colors[2],   0.0, 0.0,
            -w_o, +h_o, z, *colors[3],   w_t, 0.0,
        ], dtype=FLOAT32)

    return data


def drawDataLightSource():
    w_t, h_t = 1, 1
    w_o, h_o = LIGHT_POWER_UNIT, LIGHT_POWER_UNIT

    data = np.array([
        # obj cords     # tex cords
        -w_o, -h_o, 0,  0.0, h_t,
        +w_o, -h_o, 0,  w_t, h_t,
        +w_o, +h_o, 0,  w_t, 0.0,
        -w_o, +h_o, 0,  0.0, 0.0,
    ], dtype=FLOAT32)

    return data


def zFromLayer(layer: int):
    return (5 - layer) / 10


def drawDataFullScreen(colors: Union[List, Tuple, np.ndarray]) -> np.ndarray:
    layer = 1
    w_t, h_t = 1.0, 1.0
    w_o, h_o = 1.0, 1.0

    data_base = np.array([
        # obj cords         # color       # texture
        -w_o, -h_o, layer, *colors[0], 0.0, h_t,
        +w_o, -h_o, layer, *colors[1], w_t, h_t,
        +w_o, +h_o, layer, *colors[2], w_t, 0.0,
        -w_o, +h_o, layer, *colors[3], 0.0, 0.0,
    ], dtype=FLOAT32)

    return data_base


def splitDrawData(data: np.array) -> tuple:
    yield [list(data[h * 8: h * 8 + 2]) for h in range(4)]
    yield [list(data[h * 8 + 6: h * 8 + 8]) for h in range(4)]


def bindTexture(key):
    pass
