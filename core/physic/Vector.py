import numpy as np


class Vector2f:
    __slots__ = ['values', ]

    def __init__(self, array):
        self.values = array

    @classmethod
    def xy(cls, x, y):
        return cls(np.array([x, y], dtype=np.float16))

    ###

    def __add__(self, other):
        assert type(other) in (Vector2f, LimitedVector2f)
        return Vector2f(self.values + other.values)

    def __sub__(self, other):
        assert type(other) in (int, float)
        if self.values[0]:
            self.values[0] -= other
        if self.values[1]:
            self.values[1] -= other
        return self

    # Vector2f + Vector2f
    def sum(self, other):
        return Vector2f(self.values + other.values)

    # Vector2f += Vector2f
    def add(self, other):
        self.values += other.values

    # Vector2f * int
    def __mul__(self, other):
        return Vector2f(self.values * other)

    def __floordiv__(self, other):
        return Vector2f(self.values // 2)

    def __truediv__(self, other):
        return Vector2f(self.values / 2)

    # Vector2f - Vector2f
    def difference(self, other):
        return Vector2f(self.values - other.values)

    # Vector2f -= Vector2f
    def sub(self, other):
        self.values -= other.values

    # Length of this Vector
    def get_length(self):
        return (self[0]**2 + self[1] ** 2) ** 0.5

    def sub_length(self, value):
        if self[0] == 0:
            self.set_x(0)
            self.set_y(operation_module(self[1], value, -1))

        elif self[1] == 0:
            self.set_x(operation_module(self[0], value, -1))
            self.set_y(0)

        else:
            delta = self[1] / self[0]

            x = abs((value ** 2 / (delta ** 2 + 1)) ** 0.5)
            y = abs(x * delta)

            self.set_x(int(operation_module(self[0], x, -1)))
            self.set_y(int(operation_module(self[1], y, -1)))

    # set
    def set_values_from(self, vec):
        self.values = vec.values

    def set_x(self, x):
        self.values[0] = x

    def set_y(self, y):
        self.values[1] = y

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
        if amount > self.get_length():
            self.zero()
        else:
            self.sub_length(amount)


class LimitedVector2f(Vector2f):
    __slots__ = ['limit', ]

    def __init__(self, x, y, limit):
        super().__init__(np.array([x, y], dtype=np.float16))
        self.limit = limit

    def copy(self):
        return LimitedVector2f(*self.values, self.limit)

    def add(self, other):
        summ = self.sum(other)
        if summ.get_length() >= self.limit:
            summ.values *= self.limit / summ.get_length()
        self.values = summ.values


def operation_module(x, y, operation=1):
    if operation == 1:
        if x >= 0:
            x += y
        else:
            x -= y

    elif operation == -1:
        if x >= 0:
            x -= y
        else:
            x += y

    return x


def distance(rect1, rect2):
    return (rect1.getCenter() ** 2 + rect2.getCenter() ** 2) ** 0.5
