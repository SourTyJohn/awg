import numpy as np
from math import atan2, pi, sin, cos, radians
from pymunk.vec2d import Vec2d
from functools import lru_cache
from beartype import beartype
from core.Constants import FLOAT32, INT64, ZERO_FLOAT32


@lru_cache()
def sincos(a: float):
    a = radians(a)
    return sin(a), cos(a)


# VECTOR
@beartype
def normalized_to_degree(vec: Vec2d) -> INT64:
    return INT64(atan2(*vec) * 180 / pi - 90)


# CAMERA
@beartype
def ortho(l_: INT64, r: INT64, b: INT64, t: INT64, n: INT64 = - 1, f: INT64 = 1):
    dx = r - l_
    dy = t - b
    dz = f - n
    rx = -(r + l_) / (r - l_)
    ry = -(t + b) / (t - b)
    rz = -(f + n) / (f - n)

    return np.asfortranarray([[2.0 / dx, 0.0, 0.0, rx],
                              [0.0, 2.0 / dy, 0.0, ry],
                              [0.0, 0.0, -2.0 / dz, rz],
                              [0.0, 0.0, 0.0, 1.0]])


# MOVING
@lru_cache()
def translate(x: FLOAT32, y: FLOAT32, z: FLOAT32 = ZERO_FLOAT32):
    return np.asfortranarray([[1, 0, 0, x],
                              [0, 1, 0, y],
                              [0, 0, 1, z],
                              [0, 0, 0, 1]])


# SCALING
def scale(x, y, z=1):
    return np.asfortranarray([[x, 0, 0, 0], [0, y, 0, 0], [0, 0, z, 0], [0, 0, 0, 1]])


# ROTATION
@lru_cache()
def rotx(a):
    s, c = sincos(a)
    return np.asfortranarray([[1, 0,  0, 0],
                              [0, c, -s, 0],
                              [0, s,  c, 0],
                              [0, 0,  0, 1]])


@lru_cache()
def roty(a):
    s, c = sincos(a)
    return np.asfortranarray([[+c, 0, s, 0],
                              [+0, 1, 0, 0],
                              [-s, 0, c, 0],
                              [+0, 0, 0, 1]])


@lru_cache()
def rotz(a):
    s, c = sincos(a)
    return np.asfortranarray([[c, -s, 0, 0],
                              [s,  c, 0, 0],
                              [0,  0, 1, 0],
                              [0,  0, 0, 1]])


def reflectY():
    return np.asfortranarray([[-1,  0, 0, 0],
                              [+0,  1, 0, 0],
                              [+0,  0, 1, 0],
                              [+0,  0, 0, 1]])


# FULL TRANSFORM -> POSITION, CAMERA AND ROTATION IN ONE MATRIX
@beartype
def FullTransformMat(x: FLOAT32, y: FLOAT32, camera_matrix, z_rotation: FLOAT32):
    t = translate(x, y)
    r = rotz(z_rotation)
    return np.matmul(np.matmul(camera_matrix, t), r)
