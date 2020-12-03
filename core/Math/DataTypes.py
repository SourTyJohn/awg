import numpy as np
from math import cos, sin, radians

"""
Some self-made data types commonly used in engine
- Vectors and vector math (used for Physics)
- Rect (used for Collision, Drawing)
"""


######################
# ####  VECTOR  #### #
######################


class Vector2f:
    """Array of two floats representing vector"""
    __slots__ = ('values', )

    # Init class from np.array
    def __init__(self, array):
        self.values = array

    # Init class from two numbers
    @classmethod
    def xy(cls, x, y):
        return cls(np.array([x, y], dtype=np.float32))

    # Vector + Vector
    def __add__(self, other):
        assert isinstance(other, (Vector2f, LimitedVector2f))
        return Vector2f(self.values + other.values)

    # Vector - Vector
    def __sub__(self, other):
        assert isinstance(other, (Vector2f, LimitedVector2f))
        return Vector2f(self.values - other.values)

    # self += Vector
    def add(self, other):
        assert isinstance(other, (Vector2f, LimitedVector2f))
        self.values += other.values

    # self -= Vector
    def sub(self, other):
        assert isinstance(other, (Vector2f, LimitedVector2f))
        self.values -= other.values

    # Vector * int
    def __mul__(self, other):
        assert isinstance(other, (int, float))
        return Vector2f(self.values * other)

    # Vector // int
    def __floordiv__(self, other):
        assert isinstance(other, (int, float))
        return Vector2f(self.values // 2)

    # Vector / int
    def __truediv__(self, other):
        assert isinstance(other, (int, float))
        return Vector2f(self.values / 2)

    # Length of this Vector
    def length(self):
        return (self[0]**2 + self[1] ** 2) ** 0.5

    # Shortens Vector by value
    def sub_length(self, value):
        length = self.length() - value
        vec = vec_normalize(self)
        self.values = vec.values * length

    # Replace self.values with values of other Vector
    def set_values_from(self, vec):
        self.values = vec.values

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
    ###

    def zero(self):
        self.values -= self.values

    def __getitem__(self, item):
        return self.values[item]

    def __repr__(self):
        return f'<Vector2f [{self[0]}; {self[1]}] >'

    def __neg__(self):
        return Vector2f.xy(-self[0], -self[1])

    def __bool__(self):
        return any(self.values)

    def copy(self):
        return Vector2f(self.values)

    # physic
    def friction(self, amount):
        if amount > self.length():
            self.zero()
        else:
            self.sub_length(amount)

    def rotate(self, theta):
        theta = radians(theta)
        dc, ds = cos(theta), sin(theta)
        x, y = dc * self.x - ds * self.y, ds * self.x + dc * self.y
        return self.__class__(x, y)


class LimitedVector2f(Vector2f):
    """Vector2f with limited length"""
    __slots__ = ('limit', )

    def __init__(self, x, y, limit):
        super().__init__(np.array([x, y], dtype=np.float32))
        self.limit = limit

    def copy(self):
        return LimitedVector2f(*self.values, self.limit)

    def add(self, other):
        assert isinstance(other, (Vector2f, LimitedVector2f))

        summ = self + other
        if summ.length() >= self.limit:
            summ.values *= self.limit / summ.length()
        self.values = summ.values


def vec_normalize(vec):
    length = vec.length()
    return Vector2f.xy(vec.x / length, vec.y / length)


def vec_dot(blue, red):
    return blue.x * red.x + blue.y * red.y


def vec_cross(blue, red):
    return blue.x * red.y - blue.y * red.x


def vec_orthogonal(self):
    return self.__class__(self.x, -self.y)


######################
# #####  RECT  ##### #
######################


class Rect4f:
    """Array of four floats, representing pos and size of rectangle"""
    __slots__ = ['values', ]

    def __init__(self, x_: float, y_: float, w_: float, h_: float):
        self.values = np.array([x_, y_, w_, h_], dtype=np.float64)

    def __getitem__(self, item):
        return self.values[item]

    def __repr__(self):
        return f'<Rect4f: pos{self.values[:2]}. size: {self.values[2:]}>'

    def copy(self):
        return Rect4f(*self.values)

    # CENTER
    @property
    def center(self):
        return self.values[0] + self.values[2] / 2, self.values[1] + self.values[3] / 2

    @center.setter
    def center(self, value):
        self.values[0] = value[0] - self.values[2] / 2
        self.values[1] = value[1] - self.values[3] / 2

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

    # BORDERS
    @property
    def R(self):  # right
        return self[0] + self[2]

    @property
    def L(self):  # left
        return self[0]

    @property
    def T(self):  # top
        return self[1] + self[3]

    @property
    def B(self):  # bottom
        return self[1]

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


def distance(rect1, rect2):
    return (rect1.getCenter() ** 2 + rect2.getCenter() ** 2) ** 0.5
