from core.physic.Physics import objects
from core.Constants import COLL_TYPES
import pymunk


"""This module include only pymunk collision handlers.
Imported in World class constructor from Physics.py"""
__all__ = ('setup', )


def setup(space: pymunk.Space):
    """Main function of this module
    Setting up all collision handlers"""

    # all collision types from Constants module
    ct = COLL_TYPES

    # OBSTACLES
    # coll = space.add_collision_handler(ct['mortal'], ct['obstacle'])
    # coll.begin = collision_mortal_vs_obstacle

    # TRIGGERS
    coll = space.add_collision_handler(ct['obstacle'], ct['trigger_obstacle'])
    coll.begin = trigger_enter
    coll = space.add_collision_handler(ct['mortal'], ct['trigger_obstacle'])
    coll.begin = trigger_enter

    coll = space.add_collision_handler(ct['obstacle'], ct['trigger_obstacle'])
    coll.separate = trigger_leave
    coll = space.add_collision_handler(ct['mortal'], ct['trigger_obstacle'])
    coll.separate = trigger_leave


def from_shape(arbiter: pymunk.Arbiter, i=0):
    # Get physic object by it's shape from pymunk.Arbiter
    # len(Arbiter.shapes) == 2. i must be 0 or 1
    return objects[arbiter.shapes[i].body.__hash__()]
    # objects is a dict from Physics.py


def collision_player_vs_item(space, arbiter):
    pass


def collision_mortal_vs_obstacle(arbiter: pymunk.Arbiter, space, data):
    if arbiter.is_first_contact:
        from_shape(arbiter).fall(arbiter.total_impulse)

    return True


def trigger_enter(arbiter: pymunk.Arbiter, space, data):
    if arbiter.is_first_contact:
        actor = from_shape(arbiter, i=0)
        from_shape(arbiter, i=1).enter(actor, arbiter)

    return False


def trigger_leave(arbiter, space, data):
    actor = from_shape(arbiter, i=0)
    from_shape(arbiter, i=1).leave(actor, arbiter)

    return False
