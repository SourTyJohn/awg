from core.physic.Vector import Vector2f, LimitedVector2f

import core.physic.Collision as Cll

from core.rendering.PyOGL import *

from core.Constants import GRAVITY_VECTOR, AIR_FRICTION, RENDER_RECT_FOR_DYNAMIC, RENDER_RECT_FOR_FIXED
render_rect_d, render_rect_f = Rect(*RENDER_RECT_FOR_DYNAMIC), Rect(*RENDER_RECT_FOR_FIXED)


#  storage for all game objects {id: object, }
#  all the dynamic objects have odd int as id, all fixed have even int id's
#  empty ids store ids of objects that were vanished. Those ids can be reused
dynamicObjects = {}
empty_ids_dynamic = set()

fixedObjects = {}
empty_ids_fixed = set()


#  get hitbox from every object dynamic, fixed objects lists
def get_all_hitboxes(dynamic: list, fixed: list) -> list:
    hitboxes = []
    add = hitboxes.append

    for obj in dynamic:
        add(obj.hitbox.getRect(obj.rect.getPos()))

    for obj in fixed:
        add(obj.hitbox.getRect(obj.rect.getPos()))

    return hitboxes


#  fully delete object
def vanish_objects(*obj_ids) -> None:
    for obj_id in obj_ids:
        if obj_id % 2 == 0:
            fixedObjects[obj_id].vanish()
            empty_ids_fixed.add(obj_id)
        else:
            dynamicObjects[obj_id].vanish()
            empty_ids_dynamic.add(obj_id)


#  adds object to dynamicObjects or fixedObjects
def add_object_to_physic(obj):
    if obj.typeof() == 0:  # fixed
        eif = empty_ids_fixed

        if eif:
            this_id = eif.pop()
        else:
            this_id = len(fixedObjects) * 2

        fixedObjects[this_id] = obj

    else:  # dynamic
        eid = empty_ids_dynamic

        if eid:
            this_id = eid.pop()
        else:
            this_id = len(dynamicObjects) * 2 + 1

        dynamicObjects[this_id] = obj

    #  sets id of object
    obj.id = this_id


class Hitbox:
    """Hitbox class for detecting collision.
    Can be bounded to dynamic or fixed object"""
    __slots__ = ['offset', 'size', ]

    def __init__(self, offset, size):
        self.offset = offset
        self.size = size

    def getRect(self, self_pos):
        return [self_pos[0] + self.offset[0], self_pos[1] + self.offset[1], *self.size]


class GameObjectFixed(GLObjectBase):
    id: int  # hash for storing in hash tables

    hitbox: Hitbox = None
    size: list = None

    friction: float = 0.0
    bouncy: float = 0.0

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

        add_object_to_physic(self)

    @staticmethod
    def typeof():
        return 0

    def connect(self):
        self.id = len(fixedObjects) * 2
        fixedObjects[self.id] = self
        return self.id

    def draw(self, color=None):
        super().draw(color)

    def getHitboxRect(self):
        return self.hitbox.getRect(self.rect[:2])

    def vanish(self):
        for j in self.groups():
            j.remove(self)
        del fixedObjects[self.id]


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
        self.id = len(dynamicObjects) * 2 + 1
        dynamicObjects[self.id] = self
        return self.id

    def vanish(self):
        self.kill()
        del dynamicObjects[self.id]

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


#  Decides should object be rendered at this frame and returns lists of rendered objects
def startPhysics(hero):
    #  setup render rectangle by moving it to player
    center = hero.rect.getCenter()
    re_f = render_rect_f
    re_f.setCenter(center)
    re_d = render_rect_d
    re_d.setCenter(center)

    check = Cll.CheckAABB

    #  Testing if dynamic object in render zone
    dynamic = []
    add = dynamic.append
    for ido in dynamicObjects:
        obj = dynamicObjects[ido]

        if check(obj.rect, re_d):
            add(obj)
            obj.visible = True
        else:
            obj.visible = False

    #  Testing if fixed object in render zone
    fixed = []
    add = fixed.append
    for ido in fixedObjects:
        obj = fixedObjects[ido]

        if check(obj.rect, re_f):
            add(obj)
            obj.visible = True
        else:
            obj.visible = False

    return fixed, dynamic


# Main physics loop
def physicsStep(f, d, hero, times=1):
    hero.update(times)

    #  do physics for every dynamic object in render distance
    for obj in d:
        obj.physic(times)

    #  collision loop from Collision.py
    Cll.Step(f, d, times)
