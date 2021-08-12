import numpy as np
from OpenGL.GL import *
from typing import Dict, Union
from beartype import beartype

from core.Constants import FLOAT32, ZERO_FLOAT32, TYPE_VEC, TYPE_NUM
from core.rendering.PyOGL_utils import zFromLayer, bufferize
from core.rendering.PyOGL import frameBuffer, camera, bindEBO
from core.rendering.Shaders import shaders, StraightLineShader
from core.math.linear import FullTransformMat


__all__ = [
    'drawLine',
    'renderAllLines'
]


Shader: StraightLineShader = shaders['StraightLineShader']
lines: Dict = {}


@beartype
def drawLine(points: Union[list, TYPE_VEC], layer: int, color: list, source, width: int = 1):
    z = zFromLayer(layer)
    pos = np.array(points[0], dtype=FLOAT32)
    dpos = np.array([*points[0], 0], dtype=FLOAT32)

    lenn = len(points) * 2 - 1
    points = [x for x in ( np.array([[*x, z] for x in points]) - dpos ).flatten()]
    data = np.array(points, dtype=FLOAT32)

    if source in lines.keys():
        key = bufferize(data, lines[source][0])
    else:
        key = bufferize(data)
    lines[source] = (key, pos, np.array(color, dtype=FLOAT32), width, lenn)


def drawLineBackend(vbo_key: TYPE_NUM, pos: TYPE_VEC, color: np.ndarray, width, amount):
    glBindBuffer(GL_ARRAY_BUFFER, vbo_key)

    x_, y_ = pos
    mat = FullTransformMat(x_, y_, camera.get_matrix(), ZERO_FLOAT32)
    Shader.prepareDraw(pos, transform=mat, fbuffer=frameBuffer, color=color, width=width)

    glDrawElements(GL_LINES, amount, GL_UNSIGNED_INT, None)


@beartype
def renderAllLines():
    Shader.use()
    bindEBO(1)
    for line in lines.values():
        drawLineBackend(*line)
    bindEBO()


def reBufferize(vbo, data):
    glBindBuffer(GL_ARRAY_BUFFER, vbo)
    glBufferSubData(GL_ARRAY_BUFFER, 0, data.nbytes, data)
    return vbo
