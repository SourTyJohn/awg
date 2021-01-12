from core.physic.physics import objects
from core.Constants import COLL_TYPES
import pymunk


"""This module include only pymunk collision handlers.
Imported in World class constructor from Physics.py"""
__all__ = ('setup', )


def setup(space: pymunk.Space):
    """Main function of this module
    Setting up all collision handlers"""

    # all collision types from Constants module

    # === OBSTACLES ===

    # === TRIGGERS ===
    triggers_setup(space)


def triggers_setup(space):
    ct = COLL_TYPES
    """Setting up trigger collision types based on their names
    All Trigger collision types will detect collision with types specified in their names
    For example: 't_mortal' will collide with 'mortal' """

    for trigger_name in ct:
        if trigger_name.startswith('t_'):
            if trigger_name[2] == '*':
                types = filter(lambda x: not x.startswith('t_'), ct)
            else:
                types = trigger_name[2:].split('&&')

            for c in types:
                handler = space.add_collision_handler(ct[c], ct[trigger_name])
                handler.begin = trigger_enter
                handler.separate = trigger_leave


def from_shape(arbiter: pymunk.Arbiter, i=0):
    # Get physic object by it's shape from pymunk.Arbiter
    # len(Arbiter.shapes) == 2. i must be 0 or 1
    key = arbiter.shapes[i].body.get_key
    return objects[key], key
    # objects is a dict from Physics.py


def collision_mortal_vs_obstacle(arbiter: pymunk.Arbiter, space, data):
    if arbiter.is_first_contact:
        from_shape(arbiter)[0].fall(arbiter.total_impulse)
    return True


def trigger_enter(arbiter, space, data):
    if arbiter.is_first_contact:
        actor, key = from_shape(arbiter, i=0)
        trigger, _ = from_shape(arbiter, i=1)
        trigger.enter(actor, key, arbiter)
    return False


def trigger_leave(arbiter, space, data):
    actor, key = from_shape(arbiter, i=0)
    trigger, _ = from_shape(arbiter, i=1)
    trigger.leave(actor, key, arbiter)
    return False
