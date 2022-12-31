from pymunk.vec2d import Vec2d
from numpy import ndarray, array, matrix
from typing import Union, Generator, List
from numpy import float64, float32, int64, uintc, int16, float16
from beartype import beartype


# DATA TYPES
FLOAT64 = float64
FLOAT32 = float32
FLOAT16 = float16
INT64 = int64
INT16 = int16
UINT = uintc
ARRAY = array

ZERO_FLOAT32 = FLOAT32(0)
ZERO_INT64 = INT64(0)

ONE_FLOAT32 = FLOAT32(1)
ONE_INT64 = INT64(1)

NEG_ONE_INT64 = INT64(-1)

INF = float('inf')

TYPE_FLOAT = Union[float, FLOAT32, FLOAT64]
TYPE_INT = Union[int, INT64]
TYPE_NUM = Union[float, FLOAT32, FLOAT64, int, INT64, uintc]
TYPE_VEC = Union[Vec2d, ndarray, Generator]
TYPE_MAT = Union[ndarray, matrix]


class Rect4f:
    """Array of four floats, representing center's pos and size of rectangle"""
    __slots__ = ('values', )

    def __init__(self, x_center: float, y_center: float, width: float, height: float):
        # init with center position and size
        self.values = array([x_center, y_center, width, height], dtype=FLOAT32)

    def __getitem__(self, item):
        return self.values[item]

    def __repr__(self):
        return f'<Rect4f: center{self.values[:2]}. size: {self.values[2:] * 2}>'

    def copy(self):
        return Rect4f(*self.values)

    # POSITION
    @property
    def pos(self):
        return self.values[:2]

    @pos.setter
    def pos(self, value):
        self.values[0] = value[0]
        self.values[1] = value[1]

    def move_by(self, vec):
        self.values[0] += vec[0]
        self.values[1] += vec[1]

    # SIZE
    @property
    def size(self):
        return self.values[2:4]

    @size.setter
    def size(self, value):
        self.values[2] = value[0]
        self.values[3] = value[1]

    # VALUES
    @property
    def x(self):
        return self[0]

    @x.setter
    def x(self, value):
        self.values[0] = value

    @property
    def y(self):
        return self[1]

    @y.setter
    def y(self, value):
        self.values[1] = value

    @property
    def w(self):
        return self[2]

    @w.setter
    def w(self, value):
        self.values[2] = value

    @property
    def h(self):
        return self[3]

    @h.setter
    def h(self, value):
        self.values[3] = value


COLOR_BASE = [1.0, 1.0, 1.0, 1.0]


class Color4f:
    """Class for describing Color of Vertex"""
    MAX_CHANNEL_VALUE = 1.0

    def __init__(self, r: TYPE_FLOAT, g: TYPE_FLOAT, b: TYPE_FLOAT, a: TYPE_FLOAT = ONE_FLOAT32):
        _v = [ self.clamp_value(v) for v in [r, g, b, a] ]
        self._value = array( _v, dtype=FLOAT32 )

    @classmethod
    def from_preset(cls, color_preset):
        return cls(color_preset)

    @staticmethod
    @beartype
    def clamp_value(v: TYPE_FLOAT):
        if v > 0:
            return min(Color4f.MAX_CHANNEL_VALUE, v)
        return 0

    @beartype
    def __getitem__(self, item: TYPE_INT):
        return self._value[item]

    @beartype
    def __setitem__(self, key: TYPE_INT, value: TYPE_FLOAT):
        self._value[key] = value

    def __len__(self):
        return 4

    @beartype
    def __add__(self, other: Union["Color4f", "TYPE_VEC"]):
        self._value += other

    @property
    def r(self):
        return self._value[0]

    @r.setter
    def r(self, value: TYPE_FLOAT):
        self._value[0] = self.clamp_value( value )

    @property
    def g(self):
        return self._value[1]

    @g.setter
    def g(self, value: TYPE_FLOAT):
        self._value[1] = self.clamp_value(value)

    @property
    def b(self):
        return self._value[2]

    @b.setter
    def b(self, value: TYPE_FLOAT):
        self._value[2] = self.clamp_value(value)

    @property
    def a(self):
        return self._value[3]

    @a.setter
    def a(self, value: TYPE_FLOAT):
        self._value[3] = self.clamp_value(value)
