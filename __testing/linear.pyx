import numpy as np
from math import atan2, pi, sin, cos, radians
from pymunk.vec2d import Vec2d


def sincos(float a):
    cdef float r = radians(a)
    return sin(r), cos(r)


def degreesFromNormal(vec):
    return int(atan2(*vec) * 180 / pi - 90)


def ortho(int l_, int r, int b, int t, int n = - 1, int f = 1):
    cdef int dx = r - l_
    cdef int dy = t - b
    cdef int dz = f - n
    cdef float rx = -(r + l_) / (r - l_)
    cdef float ry = -(t + b) / (t - b)
    cdef float rz = -(f + n) / (f - n)

    return np.asfortranarray([[2.0 / dx, 0.0, 0.0, rx], [0.0, 2.0 / dy, 0.0, ry], [0.0, 0.0, -2.0 / dz, rz], [0.0, 0.0, 0.0, 1.0]])


def translate(float x, float y, float z = 0.0):
    return np.asfortranarray([[1, 0, 0, x],
                              [0, 1, 0, y],
                              [0, 0, 1, z],
                              [0, 0, 0, 1]])


def rotx(float a):
    cdef float s, c
    s, c = sincos(a)
    return np.asfortranarray([[1, 0,  0, 0],
                              [0, c, -s, 0],
                              [0, s,  c, 0],
                              [0, 0,  0, 1]])


def roty(float a):
    cdef float s, c
    s, c = sincos(a)
    return np.asfortranarray([[+c, 0, s, 0],
                              [+0, 1, 0, 0],
                              [-s, 0, c, 0],
                              [+0, 0, 0, 1]])


def rotz(float a):
    cdef float s, c
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


def FullTransformMat(float x, float y, camera_matrix, float z_rotation):
    print(camera_matrix[0], camera_matrix[1], camera_matrix[2])
    t = translate(x, y)
    r = rotz(z_rotation)
    return np.matmul(np.matmul(camera_matrix, t), r)
