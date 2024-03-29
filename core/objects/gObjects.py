"""
THIS MODUlE CONTAINS ALL GAME OBJECTS THAT CAN BE USED IN GAME (screens.game)
"""

from core.objects.gObjectTools import *
from core.physic.physics import triggers, reyCastFirst
from pymunk import PinJoint
from core.rendering.Textures import EssentialTextureStorage as Ets
from core.Constants import *
from core.Typing import FLOAT32, TYPE_MATERIAL, PhysicProperties
from core.audio.PyOAL import AudioManagerSingleton
from core.objects.gItems import InventoryAndItemsManager
from core.math.linear import projectedMovement, degreesFromNormal
from core.rendering.Particles import ParticleManager

from pymunk.vec2d import Vec2d
from beartype import beartype
import numpy as np


# DROPPED ITEMS
class DroppedItem(RC_Composite):
    class DIF(RC_Static):
        TEXTURES = [Ets['Item/item_frame'], ]
        texture = 0
        size = (72, 72)

        def __init__(self, pos):
            color = np.array([1.0, 0.2, 1.0, 0.3], dtype=np.float32)
            self.colors = [
                color, color, color, color
            ]
            super().__init__(None, pos, layer=4,)

    class DI(RC_Static):
        TEXTURES = Ets
        __slots__ = ("item", "item_name")

        size = (48, 48)

        def __init__(self, pos, item):
            self.item = item
            item_class = InventoryAndItemsManager.itemClass(item)
            self.texture = item_class.icon
            self.item_name = item_class.name
            super().__init__(None, pos, layer=3)

    def __init__(self, gr, pos, item):
        objs = [
            DroppedItem.DI(pos, item),
            DroppedItem.DIF(pos)
        ]
        super().__init__(gr, *objs)
        self.min_y = pos[1] - 8
        self.max_y = pos[1] + 8
        self.moving_to = -1  # -1 down, 1 up

    def update(self, dt, *args) -> None:
        super(DroppedItem, self).update(dt)

        self.move_by(np.array([0, dt * 8], dtype=np.float32) * self.moving_to)

        pos_y = self.objects[0].rect.pos[1]
        if pos_y >= self.max_y:
            self.moving_to = -1
        elif pos_y <= self.min_y:
            self.moving_to = 1


# WORLD GEOMETRY
class WorldRectangleRigid(RO_Physic, RC_Material, PhysObject, Direct):
    # This class represents base level geometry with rigid body
    physic_data = PhysicProperties('static', shapeFilter('level', ))

    def __init__(self, gr, pos, size, material: TYPE_MATERIAL, shape_f=None, layer=4):
        # IMAGE
        self.initialize(*material)
        super().__init__(gr, (TILE_SIZE, TILE_SIZE), layer=layer, instanced=True)
        self.scale = [ s / TILE_SIZE for s in size ]

        # PHYSIC
        points = rectPoints(*size)
        PhysObject.Polygon(self, pos, points=points)
        if shape_f:
            self.shape.filter = shape_f


class WorldRectangleRigidTrue:
    """Level Rectangle with no friction on side parts"""

    def __init__(self, gr, pos, size, material: TYPE_MATERIAL, shape_f=None, layer=4):
        xp, yp = pos
        w, h = size
        main = WorldRectangleRigid(
            gr, pos=[xp, yp - 4], size=[w, h - 8],
            material=material, shape_f=shape_f, layer=layer)
        main.friction = 0.0
        top_ = WorldRectangleRigid(
            gr, pos=[xp, yp + h / 2 - 4], size=[w, 8],
            material=material, shape_f=shape_f, layer=layer)
        top_.visible = True


class WorldRectangleSensor(WorldRectangleRigid):
    shape_filter = shapeFilter('no_collision', collide_with=())


class BackgroundColor(Direct, RO_Placed, RC_Static):
    # BackgroundColor
    color: np.array = [0.35, 0.35, 0.5, 1.0]
    color2: np.array = [1.0, 0.35, 0.5, 1.0]

    # Singleton
    __instance = None

    shader = 'BackgroundShader'

    def __init__(self, gr):
        self.texture = 'Devs/error'
        self._colors = [
            BackgroundColor.color,
            BackgroundColor.color2,
            BackgroundColor.color2,
            BackgroundColor.color
        ]
        super().__init__(gr, pos=(0, 0), size=WINDOW_SIZE, layer=10)

    def __new__(cls, *args, **kwargs):
        cls.__instance = super(BackgroundColor, cls).__new__(cls)
        return cls.__instance

    def update(self, *args, **kwargs) -> None:
        # args[1] - camera
        self.rect.pos = args[1].pos


# TRIGGERS
class Trigger(PhysObject):
    physic_data = PhysicProperties('kinematic', shapeFilter('trigger', ))

    """Area that will call given function if something intersects it and/or leaves it"""
    __slots__ = (
        'function_enter', 'function_leave', 'categories', 'triggers_by',
        'ignore', 'pos', 'bound_to', 'offset', 'size', 'entities'
    )

    def __init__(self, function_enter, categories, function_leave=None, triggers_by=(), ignore=(),
                 pos=(0, 0), bound_to=None, offset=(0, 0), size=None):
        PhysObject.Polygon(self, pos, points=rectPoints(*size), )
        self.shape.sensor = True

        """Trigger requires one of provided args: pos, bounded_to.
        If pos, than Trigger static in given position==pos
        If bound_to, than Trigger will follow given object with getPos() method with given offset

        ::arg function_enter - function, that will be called when Trigger intersected
        ::arg function_leave - function, that will be called when Trigger is not intersected any more 
        Functions args (4):
        actor - object, that activated this trigger
        owner - bounded_to object if Trigger has it
        world - World object
        arbiter - pymunk.Arbiter object to provide full info about collision

        ::arg categories - pymunk collision types from gObjectTools

        ::arg triggers_by - tuple of classes from gObjects.py,
        that can activate this trigger
        If empty, than trigger can be activated by every object of given collision type

        ::arg ignore - tuple of classes from GameObject.py,
        that can not activate this trigger
        If empty, than there is no ignored objects

        ::arg entities - list of body.__hash__ of all objects that entered
        and did not leave Trigger"""

        # Checking errors
        if pos != (0, 0) and bound_to:
            raise ValueError('Trigger requires only one of provided args: pos, bound_to')
        if not pos and not bound_to:
            raise ValueError('Trigger requires one of provided args: pos, bounded_to')
        if bound_to and not hasattr(bound_to, 'pos'):
            raise ValueError('Wrong arg: bound_to object must have .pos() method')

        # Attrs
        self.function_leave, self.function_enter = function_leave, function_enter

        try:
            self.categories = {COLLISION_CATEGORIES[c] for c in categories}
        except KeyError:
            raise ValueError(f'Category does not exist\n'
                             f'Chose from {COLLISION_CATEGORIES.keys()}')

        self.triggers_by, self.ignore = triggers_by, ignore
        self.bound_to, self.offset = bound_to, np.array(offset, dtype=FLOAT32)
        self.entities = set()

        # Add to new triggers. Check core.screens.game.update() for more info
        triggers.append(self)

    def __repr__(self):
        return f'<Trigger Pos: {self.body.pos}. Bounded to: {self.bound_to}>'

    def delete_physic(self):
        triggers.remove(self)
        super().delete_from_physic()

    @beartype
    def update(self, dt: float):
        # Trigger static and won't move
        if not self.bound_to:
            return

        # Trigger bounded to object
        self.body.pos = self.bound_to.body.pos + self.offset

    # ---
    def enter(self, actor, key, arbiter):
        if actor is self.bound_to or actor in self.ignore:
            return

        if actor.shape.collision_type not in self.categories:
            return

        if self.triggers_by:
            if actor.__class__.__name__ in self.triggers_by:
                self.entities.add(key)
                if self.function_enter:
                    return self.function_enter(actor, self.bound_to, None, arbiter)
        else:
            self.entities.add(key)
            if self.function_enter:
                return self.function_enter(actor, self.bound_to, None, arbiter)

    def leave(self, actor, key, arbiter):
        if actor is self.bound_to or actor in self.ignore:
            return

        self.entities.discard(key)
        if self.function_leave:
            return self.function_leave(actor, self.bound_to, None, arbiter)


#
class Character(RO_Physic, RC_Static, PhysObject):
    _DEFAULTS = {
        "MAX_JUMPS": 2,
        "JUMP_VECTOR": Vec2d(0, 0),

        "WALKING_VEC": 0,
        "MAX_WALKING_SPEED": 0,

        "IN_AIR_MOVE": 0.0,
        "THROW_POWER": Vec2d(58_000, 16_000),

        "FRICTION": 2.0
    }

    grabbed_item_offset = np.array([80, 0], dtype=np.float32)
    grabbed_object_joint: PinJoint

    __previous_pos: np.array

    def __init__(self, group, pos, size, points, *args, **kwargs):
        super().__init__(group, size, *args, **kwargs)
        PhysObject.Polygon(self, pos, points)

        # Walking, Running
        self.walk_direction = 0  # may be -1 - move to  the left, 0 - standing, 1 - move to the right
        self.walking_vec = self["WALKING_VEC"]
        self.max_walking_speed = self["MAX_WALKING_SPEED"]
        self.__previous_pos = self.pos

        # Jumping
        self.jumps = 0
        self.jump_delay_current = 0
        self.max_jumps = self["MAX_JUMPS"]
        self.jump_vec = self["JUMP_VECTOR"]

        # Grab
        self.grab_distance = 60
        self.grabbed_object = None
        self.grab_trigger = Trigger(None, categories=('bg_obstacle', 'obstacle'), bound_to=self,
                                    size=(80, 80), triggers_by=['WoodenCrate', ])
        self.__grabbedFilter = None

        # Blocks orientation. Characters stand on their feet
        self.can_rotate(False)

        self.on_ground = False  # is Character standing on solid floor
        self.in_air = 0  # How long didn't Character touch solid flour

        # If False, unlocks velocity limits and ignores walking_direction, jump()
        self.can_move = True

    def __getitem__(self, item):
        return self._DEFAULTS[item]

    @beartype
    def update(self, dt: float) -> None:
        if self.body.is_sleeping:
            self.body.activate()

        #
        if not self.on_ground:
            self.shape.friction = 0.0
            self.in_air += dt

        go = self.grabbed_object
        if go:
            go.pos = self.pos + self.grabbed_item_offset * self.orientation
            go.velocity = Vec2d(0, 0)

        # Walking
        self.walk(dt)
        self.__previous_pos = self.pos
        self.on_ground = False

    # Moving around
    def walk(self, dt):
        direction = self.walk_direction
        if not (direction and self.can_move):
            self.friction = self["FRICTION"]
            return

        bb = self.BB
        end_for_rey = Vec2d( bb.center()[0], bb.bottom - 8 )

        arbiter = reyCastFirst(self.pos, end_for_rey, self.shape_filter)
        normal = arbiter.normal if arbiter else Vec2d(0, 1 * direction)
        vec = self.walking_vec * direction * dt
        vecFinal = projectedMovement(vec, normal, 1.0 - (self.in_air > self["IN_AIR_MOVE"]) * 0.3)

        if self.velocity[0] * direction >= 0:
            self.friction = 0.0

        body = self.body
        body.apply_force_at_local_point(vecFinal, body.center_of_gravity)
        self.orientation = direction

        if body.velocity[0] > 0:
            body.velocity = Vec2d(
                min(self.max_walking_speed, body.velocity[0]),
                body.velocity[1]
            )
        else:
            body.velocity = Vec2d(
                max(-self.max_walking_speed, body.velocity[0]),
                body.velocity[1]
            )

    def jump(self):
        if self.can_move and self.jumps < self.max_jumps:
            self.velocity = Vec2d(self.velocity[0], self.jump_vec[1])
            self.jumps += 1
            self.on_ground = False

    # Grabbed object
    def grab_nearest_put(self, objects):
        if self.put_grabbed():
            return

        if e := self.grab_trigger.entities:
            nearest = objects[e.pop()]
            self.grab(nearest)

    def grab(self, target: "PhysicObjectThrowable"):
        target.grabbed_Throwable(self)
        self.grabbed_object = target
        target.pos = self.pos + self.grabbed_item_offset

    def put_grabbed(self):
        obj = self.grabbed_object
        if not obj:
            return None

        obj.putted_Throwable(self)
        self.grabbed_object = None
        self.max_walking_speed = self["MAX_WALKING_SPEED"]
        return obj

    def throw_grabbed(self):
        if obj := self.put_grabbed():
            vec = Vec2d( self["THROW_POWER"][0] * self.orientation, self["THROW_POWER"][1] )
            obj.thrown_Throwable(self, vec)
            obj.velocity = Vec2d(0, 0)
            obj.body.apply_impulse_at_local_point(vec)

    # Collision
    def touch_ground(self):
        self.jumps = 0
        self.on_ground = True
        self.in_air = 0
        self.friction = self["FRICTION"]

    def post_collision_handle(self, arbiter, space) -> bool:
        if arbiter.normal[1] > 0.7:
            self.touch_ground()
        return True


# vvv DEFINE YOUR CLASSES HERE vvv #

class MainHero(Character, Direct, Mortal):
    # RENDER
    _size = (64, 144)

    # PHYSIC
    physic_data = PhysicProperties(
        'dynamic',
        shapeFilter('player', ignore=('player', 'particle', 'bg_obstacle')),
        mass=100,
        friction=2,
    )

    # character
    _DEFAULTS = {
        "MAX_JUMPS": 2,
        "JUMP_VECTOR": Vec2d(0, 700),
        "MANY_JUMPS_DELAY": 0.2,

        "WALKING_VEC": Vec2d(100_000_00, 0),
        "MAX_WALKING_SPEED": 800,

        "IN_AIR_MOVE": 0.0,
        "THROW_POWER": Vec2d(58_000, 16_000),

        "FRICTION": 2.0,
    }

    #  mortal
    max_health = 200
    lethal_fall_velocity = 256

    def __init__(self, gr, pos, size=None, layer=4):
        self.texture = 'LevelOne/r_pebble_grass_1'

        cls = self.__class__
        size = cls._size if size is None else size
        super(MainHero, self).__init__(gr, pos, size, rectPoints(*size), layer=layer)
        self.init_Mortal(cls, [cls.max_health, ] * 2)

        self.tracer = Tracer(self, 0.17, 10)

    @beartype
    def update(self, dt: float):
        # args[0] - delta time
        super().update(dt)

        # jump delay update
        if self.jump_delay_current < self["MANY_JUMPS_DELAY"]:
            self.jump_delay_current += dt

    def jump(self):
        if self.jump_delay_current >= self["MANY_JUMPS_DELAY"]:
            if super().jump():
                self.jump_delay_current = 0

    def post_collision_handle(self, arbiter, space) -> bool:
        if not super(MainHero, self).post_collision_handle(arbiter, space):
            return True
        # Particles when landing
        if arbiter.total_impulse.length > self.mass * 1000:
            angles = (10, 30, 150, 170)
            pos = Vec2d( self.pos[0], self.pos[1] - self._size[1] / 2 + 16 )

            ParticleManager.create_physic(
                0, pos, (16, 24), (200, 600), (1.0, 3.0),
                (0.15, 0.1, 0.1, 1.0), (4, 6), None, angles, elasticity=0.5)
        return True


class WoodenCrate(RO_Physic, RC_Static, PhysThrowable, Direct, Mortal):
    physic_data = PhysicProperties(
        'dynamic',
        shapeFilter('obstacle', ignore=('enemy', 'particle')),
        mass=40
    )

    # static
    _size = (72, 72)
    points = rectPoints(*_size)

    # mortal
    max_health = 10
    lethal_fall_velocity = 64

    def __init__(self, gr, pos, texture='LevelOne/crate'):
        self.texture = texture
        cls = self.__class__

        super().__init__(gr, instanced=True)
        PhysThrowable.Polygon(self, pos, WoodenCrate.points)
        self.init_Mortal(cls, [cls.max_health, ] * 2)

    def post_collision_handle(self, arbiter, space):
        if arbiter.is_first_contact:
            impulse = arbiter.total_impulse.length
            if impulse > 4000:
                AudioManagerSingleton.play_sound('crate_wood_hit', self.pos, self.body.velocity,
                                                 volume=impulse / 20000, pitch=(0.8, 1.0))
            if impulse > 25_000:
                angle = int(degreesFromNormal(arbiter.normal))
                amount = int((impulse - 25_000) // 3_000)
                size_y = (12, 24)
                size_x = (8, 12)
                if 45 < abs(angle) < 135:
                    size_x, size_y = size_y, size_x
                ParticleManager.create_simple(0, arbiter.contact_point_set.points[0].point_a,
                                              (amount, amount), (16, 96), (0.5, 1.0), (0.5, 0.5, 0.5, 1.0),
                                              size_x, size_y,
                                              (angle - 90, angle - 90, angle + 90, angle + 90))
            self.throw_hit_Throwable()

    def update(self, dt: float) -> None:
        if self.update_Throwable(dt):
            ParticleManager.create_simple(
                0, self.pos, (4, 4), (6, 12), (0.5, 1.0), (0.8, 0.0, 0.0, 0.6), (4, 4), None
            )


class Dummy(Character, Direct, Mortal):
    pass

# ^^^ DEFINE YOUR CLASSES HERE ^^^ #


"""Storage of all Direct objects. 
Can be accessed by WorldEditor, LevelLoader and create_object() function"""
allObjects = {}
for x in Direct.__subclasses__():
    allObjects[x.__name__] = x


def summon(entity_type, *args, **kwargs):
    """Create object of given type with given args"""
    new = allObjects[entity_type](*args, **kwargs)
    print(f'+object: {new}\nbhash:{new.bhash if hasattr(new, "bhash") else None}')
    return new
