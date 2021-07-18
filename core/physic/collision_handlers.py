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
    triggersSetup(space)
    handleCollisionSetup(space)


def triggersSetup(space):
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
                handler.begin = triggerEnter
                handler.separate = triggerLeave


def handleCollisionSetup(spc: pymunk.Space):
    handler = spc.add_default_collision_handler()

    def collisionHandlerPre(arbiter: pymunk.Arbiter, space, data):
        if arbiter.is_first_contact:
            for s in range(len(arbiter.shapes)):
                obj = objectFromShape(arbiter, s)[0]
                obj.pre_collision_handle(arbiter.total_impulse)
        return True

    def collisionHandlerPost(arbiter: pymunk.Arbiter, space, data):
        if arbiter.is_first_contact:
            for s in range(len(arbiter.shapes)):
                obj = objectFromShape(arbiter, s)[0]
                obj.post_collision_handle(arbiter.total_impulse)
        return True

    handler.post_solve = collisionHandlerPost
    handler.pre_solve = collisionHandlerPre


class BlankObject:
    def post_collision_handle(self, *args):
        pass

    def pre_collision_handle(self, *args):
        pass

    def leave(self, *args):
        pass

    def enter(self, *args):
        pass


def objectFromShape(arbiter: pymunk.Arbiter, i=0):
    # Get physic object by it's shape from pymunk.Arbiter
    # len(Arbiter.shapes) == 2. i must be 0 or 1
    key = arbiter.shapes[i].body.get_hash_key
    if key not in objects.keys():
        return BlankObject, None
    return objects[key], key
    # objects is a dict from Physics.py


def collisionMortalVsObstacle(arbiter: pymunk.Arbiter, space, data):
    if arbiter.is_first_contact:
        objectFromShape(arbiter)[0].fall(arbiter.total_impulse)
    return True


def triggerEnter(arbiter, space, data):
    if arbiter.is_first_contact:
        actor, key = objectFromShape(arbiter, i=0)
        trigger, _ = objectFromShape(arbiter, i=1)
        trigger.enter(actor, key, arbiter)
    return False


def triggerLeave(arbiter, space, data):
    actor, key = objectFromShape(arbiter, i=0)
    trigger, _ = objectFromShape(arbiter, i=1)

    if actor and trigger:
        trigger.leave(actor, key, arbiter)
    return False
