import numpy as np
from math import atan2, pi, sin, cos, radians
from pymunk.vec2d import Vec2d
from functools import lru_cache, reduce
from beartype import beartype
from core.Typing import FLOAT32, INT64, ZERO_FLOAT32, TYPE_VEC, TYPE_FLOAT, ONE_INT64, TYPE_MAT, ONE_FLOAT32


@lru_cache( maxsize=1024 )
def sincos(a: float):
    a = radians(a)
    return sin(a), cos(a)


# IN-GAME USAGE, PHYSICS
@beartype
def projectedMovement(vec: TYPE_VEC, normal: TYPE_VEC, m: TYPE_FLOAT = 1.0) -> TYPE_VEC:
    return (vec - np.vdot(vec, normal) * normal) * m


# VECTOR
@beartype
def degreesFromNormal(vec: Vec2d) -> FLOAT32:
    return FLOAT32(atan2(*vec) * 180 / pi - 90)


# CAMERA
@beartype
def ortho(l_: INT64, r: INT64, b: INT64, t: INT64, n: INT64 = - 1, f: INT64 = 1):
    dx = r - l_
    dy = t - b
    dz = f - n
    rx = -(r + l_) / (r - l_)
    ry = -(t + b) / (t - b)
    rz = -(f + n) / (f - n)

    return np.asfortranarray([[2.0 / dx, 0.0,       0.0,        rx],
                              [0.0,      2.0 / dy,  0.0,        ry],
                              [0.0,      0.0,       -2.0 / dz,  rz],
                              [0.0,      0.0,       0.0,        1.0]])


# MOVING
@beartype
def translate(x: FLOAT32, y: FLOAT32, z: FLOAT32 = ZERO_FLOAT32):
    return np.asfortranarray([[1, 0, 0, x],
                              [0, 1, 0, y],
                              [0, 0, 1, z],
                              [0, 0, 0, 1]])


# SCALING
@beartype
def scale(x, y, z=1):
    return np.asfortranarray([[x, 0, 0, 0], [0, y, 0, 0], [0, 0, z, 0], [0, 0, 0, 1]])


# ROTATION
@beartype
def rotz(a: FLOAT32):
    s, c = sincos(a)
    return np.asfortranarray([[c, -s, 0, 0],
                              [s,  c, 0, 0],
                              [0,  0, 1, 0],
                              [0,  0, 0, 1]])


@beartype
def reflectY(y: INT64):
    return np.asfortranarray([[y,  0,  0, 0],
                              [0,  1,  0, 0],
                              [0,  0,  1, 0],
                              [0,  0,  0, 1]])


# FULL TRANSFORM -> POSITION, CAMERA AND ROTATION IN ONE MATRIX
@beartype
def FullTransformMat(
        x: FLOAT32,
        y: FLOAT32,
        camera_matrix: TYPE_MAT,
        z_rotation: FLOAT32,
        y_reflect: INT64 = ONE_INT64,
        scale_x: FLOAT32 = ONE_FLOAT32,
        scale_y: FLOAT32 = ONE_FLOAT32
):
    return np.matmul( camera_matrix, CachedTransform(x, y, z_rotation, y_reflect, scale_x, scale_y) )


@lru_cache( maxsize=1024 )
def CachedTransform(
        x: FLOAT32,
        y: FLOAT32,
        z_rotation: FLOAT32,
        y_reflect: INT64 = ONE_INT64,
        scale_x: FLOAT32 = ONE_FLOAT32,
        scale_y: FLOAT32 = ONE_FLOAT32
):
    transM = translate(x, y)
    rot_xM = rotz( z_rotation )
    rot_yM = reflectY(y_reflect)
    scaleM = scale(scale_x, scale_y)

    return reduce( np.matmul, (transM, rot_xM, rot_yM, scaleM) )


@beartype
def TransformMatConstant(camera_matrix: TYPE_MAT, cached: TYPE_MAT) -> TYPE_MAT:
    return np.matmul(camera_matrix, cached)
