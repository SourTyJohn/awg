from core.physic.Vector import Vector2f
from core.Constants import BOUNCE


def collideCheckAABB(rect1, rect2):
    #  simple AABB collision test. Used to choose should object be rendered and updated
    return rect1[0] < rect2[0] + rect2[2] and rect1[0] + rect1[2] > rect2[0] and\
           rect1[1] < rect2[1] + rect2[3] and rect1[1] + rect1[3] > rect2[1]


def getMinkovskiDifference(r1, r2):
    #  get minkowski difference for two rectangles
    difference = [
        r1[0] - (r2[0] + r2[2]),
        (r1[0] + r1[2]) - r2[0],
        r1[1] - (r2[1] + r2[3]),
        (r1[1] + r1[3]) - r2[1]
    ]

    return difference


def collideCheck(r1, r2):
    d = getMinkovskiDifference(r1, r2)

    if d[0] < 0 < d[1] and d[2] < 0 < d[3]:
        return d
    return False


def collideResolutionVector(d):
    minn, minn_side = None, 'None'
    """minn - penetration value, minn_side - penetration side"""

    for side in range(4):
        x = abs(d[side])
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


def collideResolutionFull(r1: list, obj1, r2: list, obj2, dt):
    """
    collide resolution with Minkowski difference

    r1, r2 - rect-lists, representing objects hitboxes

    obj1, obj2: core.physic.Physics.GameObjectFixed, Dynamic
    obj1 always Dynamic, obj2 can Fixed or Dynamic
    """

    difference = collideCheck(r1, r2)
    if not difference:
        return

    # penetration vector
    vector = Vector2f.xy(*collideResolutionVector(difference))

    if obj2.typeof() == 0:
        #  dynamic vs fixed collision
        collideResolutionObject(obj1, vector, obj2, dt)

    else:
        #  dynamic vs dynamic collision
        mass = obj1.mass + obj2.mass
        collideResolutionObject(obj1, vector * (obj2.mass / mass), obj2, dt)
        collideResolutionObject(obj2, -vector * (obj1.mass / mass), obj1, dt)


def collideResolutionObject(obj, move_vector, obj2, dt):
    obj.move_by(move_vector)
    vel = obj.velocity

    if move_vector[1]:
        if move_vector[1] > 0:
            obj.fell()
        vel.set_y(-vel[1] * BOUNCE)

    elif move_vector[0]:
        vel.set_x(-vel[0] * BOUNCE)

    obj.friction_apply(dt, k=obj2.friction)
