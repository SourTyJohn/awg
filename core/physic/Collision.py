from core.Math.DataTypes import Vector2f
import numpy as np


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

        vel.set_y(-vel[1] * ((obj.bouncy + obj2.bouncy) / 2))

    elif move_vector[0]:
        vel.set_x(-vel[0] * ((obj.bouncy + obj2.bouncy) / 2))

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
    # f_objs - fixed objects,  d_objects - dynamic objects

    fixedDirections = {}
    """fixedDirections stores directions in witch dynamic objects can not be moved in this Step()
    At the beginning all directions are unlocked"""
    for x in d_objs:
        """key - DynamicObject
        value[0] - array of bool representing directions that locked for this object  
        value[1] - amount of locked directions (amount of True in array)"""
        fixedDirections[x] = [np.array([False, False, False, False], dtype=np.bool), 0]

    """ --FIRST PHASE
    Collision of Dynamic Objects with Fixed and start filling fixedDirections with True"""
    coll = FixedVsDynamic

    for obj1 in f_objs:
        for obj2 in d_objs:
            f_axis = coll(obj1.hitrect, obj1, (True, True, True, True), obj2.hitrect, obj2, dt)
            #  f_axis - direction that must be locked for this object
            if f_axis > -1:
                tmp = fixedDirections[obj2]
                if not tmp[0][f_axis]:
                    tmp[0][f_axis] = True
                    tmp[1] += 1

    """ --SECOND PHASE
    Collision of Dynamic Objects vs Dynamic"""

    """key - amount of fixed directions
     value - set of dynamic objects with that amount of fixed directions"""
    objectsWithFixed = {
        0: set(),
        1: set(),
        2: set(),
        3: set(),
        4: set()
    }

    # filling  objectsWithFixed
    for obj in fixedDirections.keys():
        objectsWithFixed[fixedDirections[obj][1]].add(obj)

    # maxx_fixed - shows what key of objectsWithFixed should be used
    maxx_fixed = 4

    # checked - set of object that were already checked by collision
    checked = set()
    add = checked.add

    while maxx_fixed:

        current = objectsWithFixed[maxx_fixed]
        if current:

            obj1 = current.pop()
            add(obj1)

            for obj2 in d_objs:

                if obj2 in checked:
                    continue

                f_axis = coll(obj1.hitrect, obj1, fixedDirections[obj1][0], obj2.hitrect, obj2, dt)
                #  f_axis - direction that must be locked for this object

                if f_axis > -1:
                    tmp = fixedDirections[obj2]

                    if not tmp[0][f_axis]:
                        tmp[0][f_axis] = True
                        tmp[1] += 1
                        k = tmp[1]

                        objectsWithFixed[k - 1].discard(obj2)
                        objectsWithFixed[k].add(obj2)

                        if k > maxx_fixed:
                            maxx_fixed = k
        else:
            # if all of objects with maxx_fixed fixed directions where already checked,
            # than it lowers maxx_fixed
            maxx_fixed -= 1

    # clearing all temporary data
    fixedDirections.clear()
    objectsWithFixed.clear()
    checked.clear()
