from core.physic.Vector import Vector2f
from core.Constants import BOUNCE, DLL_USE
import numpy as np

from data.DLLs.DLL import dll_collision as dll


def CheckAABB(rect1, rect2):
    #  simple AABB collision test
    return rect1[0] < rect2[0] + rect2[2] and rect1[0] + rect1[2] > rect2[0] and \
            rect1[1] < rect2[1] + rect2[3] and rect1[1] + rect1[3] > rect2[1]


def getMinkovskiDifference(r1, r2):
    #  get minkowski difference for two rectangles
    return [
        r1[0] - (r2[0] + r2[2]),
        (r1[0] + r1[2]) - r2[0],
        r1[1] - (r2[1] + r2[3]),
        (r1[1] + r1[3]) - r2[1]
    ]


def Check(r1, r2):
    d = getMinkovskiDifference(r1, r2)

    if d[0] <= 0 <= d[1] and d[2] <= 0 <= d[3]:
        return True, d
    return False, None


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


def ResolutionObject(obj, move_vector, obj2, dt):
    obj.move_by(move_vector)
    vel = obj.velocity

    if move_vector[1]:
        if move_vector[1] > 0:
            obj.fell()
        vel.set_y(-vel[1] * BOUNCE)

    elif move_vector[0]:
        vel.set_x(-vel[0] * BOUNCE)

    obj.friction_apply(dt, k=obj2.friction)


def FixedVsDynamic(r2, obj2, fixes_axises, r1, obj1, dt):
    f, difference = Check(r1, r2)
    if not f:
        return -1

    # penetration vector
    vector = Vector2f.xy(*ResolutionVector(difference))

    v = vector.values
    x, y = v[0], v[1]
    if x:
        if x > 0:
            vector_direction = 0
            v[0] -= 1
        else:
            vector_direction = 1
            v[0] += 1
    else:
        if y > 0:
            vector_direction = 3
            v[1] -= 1
        else:
            vector_direction = 2
            v[1] += 1

    if fixes_axises[vector_direction]:
        ResolutionObject(obj1, vector, obj2, dt)
        return vector_direction

    else:
        mass = obj1.mass + obj2.mass
        ResolutionObject(obj1, vector * (obj2.mass / mass), obj2, dt)
        ResolutionObject(obj2, -vector * (obj1.mass / mass), obj1, dt)
        return -2


def Step(f_objs, d_objs, dt):

    #  Broad Phase. Walls and Flours collisions
    fixedAxises = {}
    coll = FixedVsDynamic

    for x in d_objs:
        fixedAxises[x] = np.array([False, False, False, False], dtype=np.bool)

    for obj1 in f_objs:
        for obj2 in d_objs:

            res = coll(obj1.rect, obj1, (True, True, True, True), obj2.rect, obj2, dt)
            if res > -1:
                fixedAxises[obj2][res] = True

    #  Main Phase.  Dynamic Objects collisions
    s = sorted(d_objs, key=lambda j: -sum(fixedAxises[j]))
    n = len(s)

    for o1 in range(n):
        for o2 in range(o1 + 1, n):

            obj1, obj2 = s[o1], s[o2]
            res = coll(obj1.rect, obj1, fixedAxises[obj1], obj2.rect, obj2, dt)

            if res > -1:
                fixedAxises[obj2][res] = True

    fixedAxises.clear()
