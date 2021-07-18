import numpy as np


class Rect4f:
    """Array of four floats, representing center's pos and size of rectangle"""
    __slots__ = ('values', )

    def __init__(self, x_center: float, y_center: float, width: float, height: float):
        # init with center position and size
        self.values = np.array([x_center, y_center, width, height], dtype=np.float32)

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
