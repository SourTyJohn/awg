from core.physic.physics import objects
from core.objects.gObjectTools import COLLISION_CATEGORIES
import pymunk


"""This module include only pymunk collision handlers.
Imported in World class constructor from Physics.py"""
__all__ = (
    'setup',
)


def setup(space: pymunk.Space):
    # === COLLISIONS ===
    handleCollisionSetup(space)

    # === TRIGGERS ===
    triggersSetup(space)


def handleCollisionSetup(spc: pymunk.Space):
    handler = spc.add_default_collision_handler()

    def collisionHandlerPre(arbiter: pymunk.Arbiter, space, data):
        for s in range(len(arbiter.shapes)):
            obj = objectFromShape(arbiter, s)[0]
            obj.pre_collision_handle(arbiter, space)
        return True

    def collisionHandlerPost(arbiter: pymunk.Arbiter, space, data):
        for s in range(len(arbiter.shapes)):
            obj = objectFromShape(arbiter, s)[0]
            obj.post_collision_handle(arbiter, space)
        return True

    handler.post_solve = collisionHandlerPost
    handler.pre_solve = collisionHandlerPre


def triggersSetup(spc: pymunk.Space):
    handler = spc.add_wildcard_collision_handler(COLLISION_CATEGORIES['trigger'])

    def triggerEnter(arbiter, space, data):
        if arbiter.is_first_contact:
            actor, key = objectFromShape(arbiter, i=1)
            trigger, _ = objectFromShape(arbiter, i=0)
            trigger.enter(actor, key, arbiter)
        return False

    def triggerLeave(arbiter, space, data):
        actor, key = objectFromShape(arbiter, i=1)
        trigger, _ = objectFromShape(arbiter, i=0)

        if actor and trigger:
            trigger.leave(actor, key, arbiter)
        return False

    handler.begin = triggerEnter
    handler.separate = triggerLeave


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
