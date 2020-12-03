from core.Math.DataTypes import Vector2f, Rect4f
import numpy as np


# MINKOWSKI
def MinkovskiDifference(a: Rect4f, b: Rect4f):
    #  get Minkowski difference for two rectangles
    return a[0] - (b[0] + b[2]), a[0] + a[2] - b[0], a[1] - (b[1] + b[3]), a[1] + a[3] - b[1]


def check(a: Rect4f, b: Rect4f):
    d = MinkovskiDifference(a, b)

    if d[0] <= 0 <= d[1] and d[2] <= 0 <= d[3]:
        return d

    return None


def ResolutionVector(d):
    minn, minn_side = None, 'None'
    """minn - penetration value, minn_side - penetration side"""

    for side in range(4):
        x = abs(d[side]) + 1
        if minn is None or x <= minn:
            minn = x
            minn_side = side

    """resolution vector"""
    vector = [0, 0]
    if minn_side % 2:
        vector[minn_side // 2] = -minn
    else:
        vector[minn_side // 2] = minn

    return vector


# CLASSIC AABB
def AABBvsAABB(a: Rect4f, b: Rect4f):
    pass


def Step(f_objs, d_objs, dt):
    # f_objs - fixed objects,  d_objects - dynamic objects

    for red in f_objs:
        for blue in d_objs:
            FixedVsDynamic(red, blue)

    checked = set()
    add = checked.add

    for red in d_objs:
        add(red)
        for blue in d_objs:
            if blue not in checked:
                DynamicVsDynamic(red, blue)


def DynamicVsDynamic(red, blue):

    # relative velocity
    rv = red.getVelocity() - blue.getVelocity()

    pass


def FixedVsDynamic(red, blue):
    pass
