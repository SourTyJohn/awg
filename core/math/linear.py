import numpy as np
from math import atan2, pi, sin, cos, radians, sqrt
from pymunk.vec2d import Vec2d
from functools import lru_cache


# VECTOR
def vec_dot(blue, red) -> float:
    return blue.x * red.x + blue.y * red.y


def vec_cross(blue, red) -> float:
    return blue.x * red.y - blue.y * red.x


def vec_orthogonal(vec) -> Vec2d:
    return Vec2d(vec.x, -vec.y)


def vec_unit_to_degree(vec) -> float:
    return atan2(*vec) * 180 / pi


def vec_magnitude(v: np.ndarray):
    return sqrt((v ** 2).sum())


def vec_normalize(v):
    m = vec_magnitude(v)
    if m == 0:
        return v
    return v / m
#


def sincos(a):
    a = radians(a)
    return sin(a), cos(a)


# CAMERA
def ortho(l_, r, b, t, n=-1, f=1):
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
def translate(x, y, z=0):
    return np.asfortranarray([[1, 0, 0, x],
                              [0, 1, 0, y],
                              [0, 0, 1, z],
                              [0, 0, 0, 1]])


# SCALING
def scale(x, y, z=1):
    return np.asfortranarray([[x, 0, 0, 0], [0, y, 0, 0], [0, 0, z, 0], [0, 0, 0, 1]])


# ROTATION
def rotate(a, xyz):
    x, y, z = vec_normalize(xyz)
    s, c = sincos(a)
    nc = 1 - c
    return np.asfortranarray([[x * x * nc + c,       x * y * nc - z * s, x * z * nc + y * s,    0],
                              [y * x * nc + z * s,   y * y * nc + c,     y * z * nc - x * s,    0],
                              [x * z * nc - y * s,   y * z * nc + x * s, z * z * nc + c,        0],
                              [0,                    0,                  0,                     1]])


def rotx(a):
    s, c = sincos(a)
    return np.asfortranarray([[1, 0,  0, 0],
                              [0, c, -s, 0],
                              [0, s,  c, 0],
                              [0, 0,  0, 1]])


def roty(a):
    s, c = sincos(a)
    return np.asfortranarray([[+c, 0, s, 0],
                              [+0, 1, 0, 0],
                              [-s, 0, c, 0],
                              [+0, 0, 0, 1]])


def reflectY():
    return np.asfortranarray([[-1,  0, 0, 0],
                              [+0,  1, 0, 0],
                              [+0,  0, 1, 0],
                              [+0,  0, 0, 1]])


@lru_cache
def rotz(a):
    s, c = sincos(a)
    return np.asfortranarray([[c, -s, 0, 0],
                              [s,  c, 0, 0],
                              [0,  0, 1, 0],
                              [0,  0, 0, 1]])


# FULL TRANSFORM -> POSITION, CAMERA AND ROTATION IN ONE MATRIX
def FullTransformMat(x, y, camera, z_rotation):
    t = translate(x, y)
    o = camera.get_matrix()
    r = rotz(z_rotation)
    return np.matmul(np.matmul(o, t), r)
