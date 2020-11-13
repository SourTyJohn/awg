from core.physic.Vector import Vector2f
from core.Constants import BOUNCE, G


def getMinkovskiDifference(r1, r2):
    difference = [
        r1[0] - (r2[0] + r2[2]),
        (r1[0] + r1[2]) - r2[0],
        r1[1] - (r2[1] + r2[3]),
        (r1[1] + r1[3]) - r2[1]
    ]

    return difference


def collideCheck(r1, r2):
    d = getMinkovskiDifference(r1, r2)

    if d[0] <= 0 <= d[1] and d[2] <= 0 <= d[3]:
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

    if obj2.typeof() == 0:  # if obj2 is Fixed Object
        collideResolutionObject(obj1, vector, 1, obj2, dt)

    else:
        delta = obj1.mass / obj2.mass

        # impulse_all = obj1.mass * obj1.velocity.get_length() + obj2.mass * obj2.velocity.get_length()
        # impulse_unit = impulse_all / (obj1.mass + obj2.mass)
        #
        # impulse1 = impulse_unit * obj2.mass / obj1.mass
        # impulse2 = impulse_unit * obj1.mass / obj2.mass

        collideResolutionObject(obj1, vector, delta, obj2, dt)
        collideResolutionObject(obj2, -vector, 1 / delta, obj1, dt)


def collideResolutionObject(obj, vector, delta, obj2, dt):
    obj.move_by(vector)
    vel = obj.velocity

    if vector[1]:
        if vector[1] > 0:
            obj.fell()
        vel.set_y(-vel[1] * delta * BOUNCE)

    if vector[0]:
        vel.set_x(-vel[0] * delta * BOUNCE)

    obj.friction_apply(dt, k=obj2.friction)
