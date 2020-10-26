import numpy as np


class Vector2f:
    __slots__ = ['values', ]

    def __init__(self, array):
        self.values = array

    @classmethod
    def xy(cls, x, y):
        return cls(np.array([x, y], dtype=np.float32))

    ###

    # Vector2f + Vector2f
    def sum(self, other):
        assert other.__class__ == Vector2f
        return Vector2f(self.values + other.values)

    # Vector2f += Vector2f
    def add(self, other):
        assert other.__class__ == Vector2f
        self.values += other.values

    # Vector2f - Vector2f
    def difference(self, other):
        assert other.__class__ == Vector2f
        return Vector2f(self.values - other.values)

    # Vector2f -= Vector2f
    def sub(self, other):
        assert other.__class__ == Vector2f
        self.values -= other.values

    # Length of this Vector
    def get_length(self):
        return (self[0]**2 + self[1] ** 2) ** 0.5

    ###

    def __getitem__(self, item):
        return self.values[item]

    def __repr__(self):
        return f'<Vector2f [{self[0]}; {self[1]}] >'

    def zero(self):
        self.values -= self.values


class BaseMovementVector(Vector2f):
    __slots__ = ['limit', ]

    def __init__(self, x, y, limit):
        super().__init__(np.array([x, y], dtype=np.float16))
        self.limit = limit

    def sub_length(self, value):
        delta = self[1] / self[0]
        x = abs((value ** 2 / (delta ** 2 + 1)) ** 0.5)
        y = abs(x * delta)

        self.values[0] = (abs(self.values[0]) - x) * ((-1) ** (self.values[0] < 0))
        self.values[1] = (abs(self.values[1]) - y) * ((-1) ** (self.values[1] < 0))

    def add_length(self, value):
        length = self.get_length()

        if length + value > self.limit:
            value = self.limit - length

        delta = self[1] / self[0]
        x = abs((value ** 2 / (delta ** 2 + 1)) ** 0.5)
        y = abs(x * delta)

        self.values[0] = (abs(self.values[0]) + x) * ((-1) ** (self.values[0] < 0))
        self.values[1] = (abs(self.values[1]) + y) * ((-1) ** (self.values[1] < 0))

    def friction(self, amount):
        if amount > self.get_length():
            self.zero()
        else:
            self.sub_length(amount)
