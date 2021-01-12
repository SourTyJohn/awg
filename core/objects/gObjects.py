"""
THIS MODUlE CONTAINS ALL GAME OBJECTS THAT CAN BE USED IN GAME (screens.game)
"""

from core.objects.gObjectTools import *
from core.physic.physics import triggers

from core.rendering.Textures import EssentialTextureStorage as Ets
from core.Constants import *

from pymunk.vec2d import Vec2d
from pymunk import moment_for_poly
inf = float('inf')

import numpy as np


# WORLD GEOMETRY
class WorldRectangleRigid(image, phys, direct):
    # This class represents base level geometry with rigid body
    shape_filter = shape_filter(('obstacle', ), )

    TEXTURES = Ets
    body_type = 'static'
    collision_type = 'obstacle'

    def __init__(self, gr, pos, size, tex_offset=(0, 0), texture='Devs/r_devs_1', shape_f=None, layer=0.6):
        # IMAGE
        self.texture = texture
        super().__init__(gr, pos, size, tex_offset=tex_offset, layer=layer)

        # PHYSIC
        points = rect_points(*size)
        phys.__init__(self, pos, points=points)
        if shape_f:
            self.shape.filter = shape_f


class WorldRectangleSensor(WorldRectangleRigid):
    shape_filter = shape_filter(('no_collision', ), collide_with=())


class WorldGeometry(image, phys, direct):
    shape_filter = shape_filter(('obstacle', ), )
    collision_type = 'obstacle'
    body_type = 'static'

    # All textures
    TEXTURES = Ets

    def __init__(self, gr, pos, points):
        pass


class BackgroundColor(image):
    # Texture is not actually visible. Only color
    TEXTURES = (Ets['Devs/error'], )

    # BackgroundColor
    color: np.array = [0.35, 0.35, 0.5, 1.0]
    color2: np.array = [1.0, 0.35, 0.5, 1.0]

    # Singleton
    __instance = None

    def __init__(self, gr):
        self.texture = 0
        self.colors = [
            BackgroundColor.color,
            BackgroundColor.color2,
            BackgroundColor.color2,
            BackgroundColor.color
        ]
        super().__init__(gr, pos=(0, 0), size=WINDOW_SIZE, layer=0)

    def __new__(cls, *args, **kwargs):
        cls.__instance = super(BackgroundColor, cls).__new__(cls)
        return cls.__instance

    def update(self, *args, **kwargs) -> None:
        # args[1] - camera
        self.rect.pos = args[1].pos


# TRIGGERS
class Trigger(phys):
    shape_filter = shape_filter(('trigger', ), )
    body_type = 'kinematic'

    """Area that will call given function if something intersects it and/or leaves it"""
    __slots__ = (
        'function_enter', 'function_leave', 'collision_type', 'triggers_by',
        'ignore', 'pos', 'bound_to', 'offset', 'size', 'entities'
    )

    def __init__(self, function_enter, collision_type, function_leave=None, triggers_by=(), ignore=(),
                 pos=(0, 0), bound_to=None, offset=(0, 0), size=None):
        super().__init__(pos, points=rect_points(*size), collision_type=collision_type)

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

        ::arg collision_type - pymunk collision type key from Constants.COLL_TYPES

        ::arg triggers_by - tuple of classes from gObjects.py,
        that can activate this trigger
        If empty, than trigger can be activated by every object of given collision type

        ::arg ignore - tuple of classes from GameObject.py,
        that can not activate this trigger
        If empty, than there is no ignored objects

        ::arg entities - list of body.__hash__ of all objects that entered
        and d'nt leave Trigger"""

        # Checking errors
        if pos != (0, 0) and bound_to:
            raise ValueError('Trigger requires only one of provided args: pos, bound_to')
        if not pos and not bound_to:
            raise ValueError('Trigger requires one of provided args: pos, bounded_to')
        if bound_to and not hasattr(bound_to, 'pos'):
            raise ValueError('Wrong arg: bound_to object must have .pos() method')
        if collision_type not in COLL_TYPES.keys():
            raise ValueError(f'Wrong collision type: {collision_type}.\nSelect from {list(COLL_TYPES.keys())}')

        # Attrs
        self.function_leave, self.function_enter = function_leave, function_enter
        self.triggers_by, self.ignore = triggers_by, ignore
        self.bound_to, self.offset = bound_to, offset
        self.collision_type = collision_type
        self.entities = set()

        # Add to new triggers. Check core.screens.game.update() for more info
        triggers.append(self)

        #
        if bound_to:
            bound_to.triggers.add(self)

    def __repr__(self):
        return f'<Trigger Pos: {self.body.pos}. Bounded to: {self.bound_to}>'

    def delete(self):
        self.bound_to.triggers.remove(self)
        super().delete()

    def update(self, *args, **kwargs):
        # Trigger static and won't move
        if not self.bound_to:
            return

        # Trigger bounded to object
        self.body.pos = self.bound_to.pos + self.offset

    # ---
    def enter(self, actor, key, arbiter):
        if actor is self.bound_to or actor in self.ignore:
            return
        if self.triggers_by:
            if actor.__class__ in self.triggers_by:
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
        if self.triggers_by:
            if actor.__class__ in self.triggers_by:
                self.entities.discard(key)
                if self.function_leave:
                    return self.function_leave(actor, self.bound_to, None, arbiter)
        else:
            self.entities.discard(key)
            if self.function_leave:
                return self.function_leave(actor, self.bound_to, None, arbiter)


# LIGHT
class LightSourceStatic:
    def __init__(self, pos, power):
        self.body = 0

    def update(self):
        pass


#
class Character(image, phys):
    body_type = 'dynamic'
    collision_type = 'mortal'
    shape_filter = shape_filter(('character', 'mortal'), )

    MAX_JUMPS = 2
    WALKING_VEC = 0
    JUMP_VECTOR = Vec2d(0, 0)
    MAX_WALKING_SPEED = 0
    IN_AIR_MOVE = 0.8  # sec
    THROW_POWER = Vec2d(4000, 500)

    __grabbed_filter: ShapeFilter

    def __init__(self, group, pos, *args, **kwargs):
        super().__init__(group, pos, *args, **kwargs)
        phys.__init__(self, pos, )

        # Walking, Running
        self.walk_direction = 0  # may be -1 - move to  the left, 0 - standing, 1 - move to the right
        self.walking_vec = self.__class__.WALKING_VEC
        self.max_walking_speed = self.__class__.MAX_WALKING_SPEED

        # Jumping
        self.jumps = 0
        self.jump_delay_current = 0
        self.max_jumps = self.__class__.MAX_JUMPS
        self.jump_vec = self.__class__.JUMP_VECTOR

        # Grab
        self.grab_distance = 60
        self.grabbed_object = None
        self.grab_trigger = Trigger(None, 't_mortal',
                                    bound_to=self, size=(80, 80), triggers_by=[WoodenCrate, ])
        self.__grabbedFilter = None

        # Blocks rotation. Characters stand on their feet
        self.body.moment = inf

        # Standing on ground trigger
        self.on_ground_trigger = Trigger(self.touch_ground, 't_obstacle&&mortal', self.untouch_ground,
                                         bound_to=self, offset=(0, -self.size[1] // 2),
                                         size=(self.size[0] - 2, 6))
        self.on_ground = False  # is Character standing on solid floor
        self.in_air = 0  # How long din't Character touch solid flour

        # If False, unlocks velocity limits and ignores walking_direction, jump()
        self.can_move = True

    def update(self, *args, **kwargs) -> None:
        super().update(*args, **kwargs)
        dt = args[0]

        # Grabbed object update
        if self.grabbed_object:
            self.grabbed_object.pos = self.pos + np.array([70 * self.y_Rotation, 0])
            self.grabbed_object.body.velocity = (0, 0)

        if not self.on_ground:
            self.in_air += dt

        # Walking
        self.walk(dt)

    # Moving around
    def walk(self, dt):
        if not self.walk_direction:
            return

        if not self.can_move:
            return

        if self.on_ground:
            vel = self.walking_vec * self.walk_direction * dt
        elif self.in_air < self.IN_AIR_MOVE:
            vel = self.walking_vec * self.walk_direction * dt * 0.2
        else:
            return

        body = self.body
        body.apply_force_at_local_point(vel, body.center_of_gravity)
        self.rotY(self.walk_direction)

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
            self.body.apply_impulse_at_local_point(self.jump_vec)
            self.jumps += 1
            return True
        return False

    # Grabbed object
    def grab_nearest_put(self, objects):
        self.put_grabbed()

        e = self.grab_trigger.entities
        if e:
            nearest = objects[e.pop()]
            self.grab(nearest)

    def grab(self, target):
        """Object won't rotate and has no collision
        Rotation and velocity to 0"""
        b = target.body
        b.moment = inf
        b.angular_velocity = 0
        b.angle = 0

        self.__grabbedFilter = target.shape.filter
        target.shape.filter = add_ignore(target.shape_filter, self.shape.filter.categories)

        self.grabbed_object = target

    def put_grabbed(self):
        obj = self.grabbed_object
        if not obj:
            return

        obj.body.moment = moment_for_poly(obj.bmass, obj.shape.get_vertices(), (0, 0))
        obj.body.velocity = self.body.velocity
        obj.shape.filter = self.__grabbedFilter

        self.__grabbedFilter = None
        self.grabbed_object = None

        return obj

    def throw_grabbed(self):
        obj = self.put_grabbed()
        if obj:
            obj.body.apply_impulse_at_local_point(self.THROW_POWER * self.y_Rotation)

    # Legs Trigger
    def touch_ground(self, *args):
        # actor - ground, owner - self, world - world
        if 1.0 >= abs(args[3].normal[1]) >= 0.3:
            self.jumps = 0
            self.on_ground = True
            self.in_air = 0

    def untouch_ground(self, *args):
        if len(self.on_ground_trigger.entities) == 0:
            self.on_ground = False
            if self.jumps == 0:
                self.jumps = 1


# vvv INSERT YOUR CLASSES HERE vvv #

class MainHero(Character, direct, mortal):
    # RENDER
    TEXTURES = [Ets['LevelOne/r_pebble_grass_1'], ]
    size = (64, 144)

    # PHYSIC
    shape_filter = shape_filter(('player', 'character', 'mortal'), )
    points = rect_points(*size)
    friction = 2
    mass = 10.0

    # character
    JUMP_VECTOR = Vec2d(0, 700 * mass)
    WALKING_VEC = Vec2d(384_000 * mass, 0)
    MAX_WALKING_SPEED = 80 * mass

    # unique
    MANY_JUMPS_DELAY = 0.2

    #  mortal
    max_health = 200
    lethal_fall_velocity = 256

    def __init__(self, gr, pos):
        Character.__init__(self, gr, pos, MainHero.size)
        self.init_mortal(self.__class__)

    def update(self, *args, **kwargs):
        # args[0] - delta time
        super().update(*args, **kwargs)

        # jump delay update
        if self.jump_delay_current < MainHero.MANY_JUMPS_DELAY:
            self.jump_delay_current += args[0]

    def jump(self):
        if self.jump_delay_current >= MainHero.MANY_JUMPS_DELAY:
            if super().jump():
                self.jump_delay_current = 0


class WoodenCrate(image, phys, direct, mortal):
    body_type = 'dynamic'
    collision_type = 'mortal'
    shape_filter = shape_filter(('mortal', 'obstacle'), )

    # static
    TEXTURES = (Ets['LevelOne/crate'], )
    size = (64, 64)
    points = rect_points(*size)

    # shape_filter = shape_filter('player', )

    # dynamic
    mass = 8.0

    # mortal
    max_health = 10
    lethal_fall_velocity = 64

    def __init__(self, gr, pos):
        super().__init__(gr, pos, size=self.__class__.size)
        phys.__init__(self, pos)
        self.init_mortal(self.__class__)


class MetalCrate(WoodenCrate, direct, mortal):
    # static
    TEXTURES = (Ets['LevelOne/r_orange_bricks_1'], )
    size = (128, 128)
    points = rect_points(*size)

    # dynamic
    mass = 60.0

    # mortal
    max_health = 32

# ^^^ INSERT YOUR CLASSES HERE ^^^ #


"""Storage of all Direct objects. 
Can be accessed by WorldEditor, LevelLoader and create_object() function"""
allObjects = {}
for x in DirectAccessObject.__subclasses__():
    allObjects[x.__name__] = x


def summon(entity_type, *args, **kwargs):
    """Create object of given type with given args"""
    new = allObjects[entity_type](*args, **kwargs)
    print(f'+object: {new}\nbhash:{new.bhash if hasattr(new, "bhash") else None}')
    return new
