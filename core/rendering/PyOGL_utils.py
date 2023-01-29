from core.Constants import LIGHT_POWER_UNIT
from core.Typing import FLOAT32
from typing import Union, List, Tuple

from OpenGL.GL import *
import numpy as np

__all__ = [
    "makeGLTexture",
    "bufferize",
    "bufferizeVAO",
    "drawDataFullScreen",
    "DrawData",
    "splitDrawData",
    "zFromLayer",
    "drawDataLightSource"
]


class DrawData:
    __slots__ = (
        "_vertexes", "_colors", "_uv_map", "_indices", "_layer", "_drawdata"
    )
    
    _vertexes: list
    _colors: list
    _uv_map: list

    _indices: list
    _layer: int

    _drawdata: np.ndarray

    def __init__(self, vertexes, colors, uv_map, indices, layer):
        assert 0 <= layer <= 10 and isinstance(layer, int), \
            f'Wrong layer param: {layer}. Should be integer from 1 to 10'

        self._vertexes = vertexes
        self._colors = colors
        self._indices = indices
        self._layer = layer
        self._uv_map = uv_map

        self.__update()

    @classmethod
    def Rectangle(cls, w, h, colors: list = None, layer: int = 5):
        if colors is None:
            colors = [[1.0, 1.0, 1.0, 1.0], [1.0, 1.0, 1.0, 1.0], [1.0, 1.0, 1.0, 1.0], [1.0, 1.0, 1.0, 1.0]]

        z = zFromLayer(layer)
        w /= 2
        h /= 2

        _vertexes = [[-w, -h, z], [+w, -h, z], [+w, +h, z], [-w, +h, z]]
        _colors = colors
        _uv_map = [[0, 1], [1, 1], [1, 0], [0, 0]]
        _indices = [0, 1, 2, 2, 3, 0]

        return DrawData(_vertexes, _colors, _uv_map, _indices, layer)

    def __update(self):
        _drawdata = []
        for v in range(4):
            _drawdata += [*self._vertexes[v], *self._colors[v], *self._uv_map[v]]
        self._drawdata = np.array( _drawdata, dtype=FLOAT32 )

    # def bufferize(self, shader, vao=None, vbo=None, ibo=None):
    #     return bufferizeVAO( self._drawdata, self._indices, shader, vao, vbo, ibo )

    def bufferize(self, shader, vbo):
        return bufferize(self._drawdata, vbo)


def makeGLTexture(image_data: np.ndarray, w: int, h: int) -> int:
    """Loading pygame.Surface as OpenGL texture
    :return New Texture key"""

    # getting data from pygame.Surface

    # bind new texture
    key = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, key)

    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_R, GL_CLAMP_TO_BORDER)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_BORDER)

    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)  # настройка сжатия
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)  # настройка растяжения

    glTexImage2D(
        GL_TEXTURE_2D, GL_ZERO, GL_RGBA, w, h, GL_ZERO, GL_RGBA, GL_UNSIGNED_BYTE, image_data
    )
    #

    # unbind new texture
    glBindTexture(GL_TEXTURE_2D, 0)

    return key


def bufferize(data: np.ndarray, vbo=None) -> int:
    """Generating Buffer to store this object's vertex data,
    necessary for drawing"""
    if not vbo:
        vbo = glGenBuffers(1)

    glBindBuffer(GL_ARRAY_BUFFER, vbo)
    glBufferData(GL_ARRAY_BUFFER, data.nbytes, data, GL_STATIC_DRAW)

    return vbo


def bufferizeVAO(vertex_data: np.ndarray, indices, shader, vao: int = None, vbo: int = None, ibo: int = None):
    if vao is None:
        vao = glGenVertexArrays(1)

    if vbo is None:
        vbo = glGenBuffers(1)

    if ibo is None:
        ibo = glGenBuffers(1)

    glBindVertexArray(vao)
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ibo)
    glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices, GL_STATIC_DRAW)
    glBindBuffer(GL_ARRAY_BUFFER, vbo)
    glBufferData(GL_ARRAY_BUFFER, vertex_data, GL_STATIC_DRAW)

    shader.setupVAO()

    glBindVertexArray(0)
    return vao, vbo, ibo


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
