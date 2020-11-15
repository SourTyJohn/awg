# import numpy as np
from core.physic.Vector import Vector2f, LimitedVector2f
from core.rendering.PyOGL import *
from core.physic.Collision import collideResolutionFull, collideCheckAABB

from core.Constants import GRAVITY_VECTOR, AIR_FRICTION, RENDER_RECT_FOR_DYNAMIC, RENDER_RECT_FOR_FIXED
render_rect_d, render_rect_f = Rect(*RENDER_RECT_FOR_DYNAMIC), Rect(*RENDER_RECT_FOR_FIXED)

dynamicObjects = []
fixedObjects = []


class Hitbox:
    __slots__ = ['offset', 'size', ]

    def __init__(self, offset, size):
        self.offset = offset
        self.size = size

    def getRect(self, self_pos):
        return [self_pos[0] + self.offset[0], self_pos[1] + self.offset[1], *self.size]


class GameObjectFixed(GLObjectBase):
    hitbox: Hitbox = None
    size: list = None

    friction: float = 0
    bouncy: float = None

    def __init__(self, group, pos, size='default', rotation=1, tex_offset=(0, 0), texture=0, hitbox='default'):
        """
        group - sprite group
        size - size of a texture, not hitbox
        If hitbox is None, object has no collision
        """

        self.texture = texture

        if size == 'default':
            size = self.__class__.size

        if hitbox == 'default':
            hitbox = self.__class__.hitbox

        super().__init__(group, [*pos, *size], rotation, tex_offset)

        self.hitbox = hitbox
        self.friction = self.__class__.friction
        self.bouncy = self.__class__.bouncy

        self.connect()

    @staticmethod
    def typeof():
        return 0

    def connect(self):
        fixedObjects.append(self)

    def draw(self, color=None):
        super().draw(color)

    def getHitboxRect(self):
        return self.hitbox.getRect(self.rect[:2])


class GameObjectDynamic(GameObjectFixed):
    mass: int = 0

    def __init__(self, group, pos, size, rotation=1, tex_offset=(0, 0), max_velocity=None):
        super().__init__(group, pos, size, rotation, tex_offset)

        self.mass = self.__class__.mass
        if max_velocity:
            self.velocity = LimitedVector2f(0, 0, max_velocity)
        else:
            self.velocity = Vector2f.xy(0, 0)

        # if False, object wont .update() and .physic()
        self.updating = True

    @staticmethod
    def typeof():
        return 1

    def connect(self):
        dynamicObjects.append(self)

    def draw(self, color=None):
        super().draw(color)

    # physic
    def physic(self, dt):  # dt - delta time from last call
        self._gravitation(dt=dt)
        self.friction_apply(dt=dt, k=AIR_FRICTION)
        self._doMove(dt=dt)

    def _gravitation(self, dt, g=GRAVITY_VECTOR):
        self.velocity.add(g * dt)

    def friction_apply(self, dt, k):
        self.velocity.friction(k * dt)

    def collision(self, other, dt):
        collideResolutionFull(self.getHitboxRect(), self, other.getHitboxRect(), other, dt)

    def fell(self):  # Called when object hitting the obstacle after falling
        pass

    # movement
    def _doMove(self, dt):
        self.move_by(self.velocity * dt)

    def addVelocity(self, vector):
        if type(vector) != Vector2f:
            vector = Vector2f.xy(*vector)
        self.velocity.add(vector)

    def getVelocity(self):
        return self.velocity


def startPhysics(hero):
    center = hero.rect.getCenter()
    re_f = render_rect_f
    re_f.setCenter(center)
    re_d = render_rect_d
    re_d.setCenter(center)

    dynamic = []
    add = dynamic.append

    for obj in dynamicObjects:
        if collideCheckAABB(obj.rect, re_d):
            add(obj)
            obj.visible = True
        else:
            obj.visible = False

    fixed = []
    add = fixed.append

    for obj in fixedObjects:
        if collideCheckAABB(obj.rect, re_f):
            add(obj)
            obj.visible = True
        else:
            obj.visible = False

    return fixed, dynamic


# Main physics loop
def applyPhysics(f, d, hero, times=1):
    hero.update(times)
    for obj in d:
        obj.physic(times)
    checkCollision(f, d, times)


def checkCollision(f, d, delta_time):
    checked = set()
    check = checked.add

    all_objects = d + f

    for obj1 in d:
        check(obj1)
        coll = obj1.collision

        for obj2 in all_objects:

            if obj2 not in checked:
                coll(obj2, delta_time)