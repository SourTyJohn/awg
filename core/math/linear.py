import numpy as np
from math import atan2, pi, sin, cos, radians, sqrt, tan
from pymunk.vec2d import Vec2d


# VECTOR
def vec_normalize(vec) -> Vec2d:
    length = vec.length()
    return Vec2d(vec.x / length, vec.y / length)


def vec_dot(blue, red) -> float:
    return blue.x * red.x + blue.y * red.y


def vec_cross(blue, red) -> float:
    return blue.x * red.y - blue.y * red.x


def vec_orthogonal(vec) -> Vec2d:
    return Vec2d(vec.x, -vec.y)


def vec_unit_to_degree(vec) -> float:
    return atan2(*vec) * 180 / pi
#


# unused
def transform(m, v):
    return np.asarray(m * np.asmatrix(v).T)[:, 0]


def magnitude(v: np.ndarray):
    return sqrt((v ** 2).sum())


def normalize(v):
    m = magnitude(v)
    if m == 0:
        return v
    return v / m


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


# unused
def perspective(fovy, aspect, n, f):
    s = 1.0 / tan(radians(fovy) / 2.0)
    sx, sy = s / aspect, s
    zz = (f + n) / (n - f)
    zw = 2 * f * n / (n - f)
    return np.array([[sx, 0, 0, 0],
                     [0, sy, 0, 0],
                     [0, 0, zz, zw],
                     [0, 0, -1, 0]])


# unused
def frustum(x0, x1, y0, y1, z0, z1):
    a = (x1 + x0) / (x1 - x0)
    b = (y1 + y0) / (y1 - y0)
    c = -(z1 + z0) / (z1 - z0)
    d = -2 * z1 * z0 / (z1 - z0)
    sx = 2 * z0 / (x1 - x0)
    sy = 2 * z0 / (y1 - y0)
    return np.array([[sx, 0, a, 0],
                     [0, sy, b, 0],
                     [0, 0, c, d],
                     [0, 0, -1, 0]])


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
    x, y, z = normalize(xyz)
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


def rotz(a):
    s, c = sincos(a)
    return np.asfortranarray([[c, -s, 0, 0],
                              [s,  c, 0, 0],
                              [0,  0, 1, 0],
                              [0,  0, 0, 1]])


# unused
def lookAt(eye, target, up):
    F = target[:3] - eye[:3]
    f = normalize(F)
    U = normalize(up[:3])
    s = np.cross(f, U)
    u = np.cross(s, f)
    M = np.array(np.identity(4))
    M[:3, :3] = np.vstack([s, u, -f])
    T = translate(*-eye)

    return M * T


# unused
def viewport(x, y, w, h):
    x, y, w, h = map(float, (x, y, w, h))
    return np.array([[w / 2, 0, 0, x + w / 2],
                     [0, h / 2, 0, y + h / 2],
                     [0, 0, 1, 0],
                     [0, 0, 0, 1]])


def FullTransformMat(x, y, camera, z_rotation):
    t = translate(x, y)
    o = camera.getMatrix()
    r = rotz(z_rotation)
    return np.matmul(np.matmul(o, t), r)
