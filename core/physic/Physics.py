# import numpy as np
# from core.physic.Vector import *
from core.rendering.PyOGL import *


AIR_FRICTION = 1


class Hitbox:
    __slots__ = ['offset', 'size', ]

    def __init__(self, offset, size):
        self.offset = offset
        self.size = size

    def check_collide(self, actor_pos, group):
        posX, posY = actor_pos[0] + self.offset[0], actor_pos[1] + self.offset[1]

        for obj in group:
            pass


def is_colliding(rect1, rect2):
    return


class GameObjectFixed(GLObjectGUI):
    hitbox: Hitbox = None
    size: list = None

    friction: float = None
    bouncy: float = None

    def __init__(self, group, pos, size='default', rotation=1, tex_offset=(0, 0), texture=0, hitbox='default'):
        self.texture = texture

        if size == 'default':
            size = self.__class__.size

        if hitbox == 'default':
            hitbox = self.__class__.hitbox

        super().__init__(group, [*pos, *size], rotation, tex_offset)

        self.hitbox = hitbox
        self.friction = self.__class__.friction
        self.bouncy = self.__class__.bouncy

    def draw(self, color=None):
        super().draw(color)


class GameObjectDynamic(GameObjectFixed):
    mass: int = 0

    def __init__(self, group, pos, size, rotation=1, tex_offset=(0, 0)):
        super().__init__(group, pos, size, rotation, tex_offset)

        self.mass = self.__class__.mass

    def draw(self, color=None):
        pass


# Main physics loop
def applyPhysics():
    pass
