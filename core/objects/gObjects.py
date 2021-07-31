"""
THIS MODUlE CONTAINS ALL GAME OBJECTS THAT CAN BE USED IN GAME (screens.game)
"""

from core.objects.gObjectTools import *
from core.physic.physics import triggers, inf
from core.rendering.Textures import EssentialTextureStorage as Ets
from core.Constants import *
from core.audio.PyOAL import AudioManager
from core.objects.gItems import InventoryAndItemsManager

from pymunk.vec2d import Vec2d
from pymunk import moment_for_poly, ShapeFilter
import numpy as np


# DROPPED ITEMS
class DroppedItem(composite):
    class DIF(image):
        TEXTURES = [Ets['Item/item_frame'], ]
        texture = 0
        size = (72, 72)

        def __init__(self, pos):
            color = np.array([1.0, 0.2, 1.0, 0.3], dtype=np.float32)
            self.colors = [
                color, color, color, color
            ]
            super().__init__(None, pos, layer=4,)

    class DI(image):
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

    def update(self, *args, **kwargs) -> None:
        super(DroppedItem, self).update(*args, **kwargs)

        dt = args[0]
        self.move_by(np.array([0, dt * 8], dtype=np.float32) * self.moving_to)

        pos_y = self.objects[0].rect.pos[1]
        if pos_y >= self.max_y:
            self.moving_to = -1
        elif pos_y <= self.min_y:
            self.moving_to = 1


# WORLD GEOMETRY
class WorldRectangleRigid(image, phys, direct):
    # This class represents base level geometry with rigid body
    shape_filter = shapeFilter('obstacle', )
    body_type = 'static'

    TEXTURES = Ets

    def __init__(self, gr, pos, size, tex_offset=(0, 0), texture='Devs/r_devs_1', shape_f=None, layer=4):
        # IMAGE
        self.texture = texture
        super().__init__(gr, pos, size, tex_offset=tex_offset, layer=layer)

        # PHYSIC
        points = rectPoints(*size)
        phys.__init__(self, pos, points=points)
        if shape_f:
            self.shape.filter = shape_f


class WorldRectangleSensor(WorldRectangleRigid):
    shape_filter = shapeFilter('no_collision', collide_with=())


class BackgroundColor(image):
    # Texture is not actually visible. Only color
    TEXTURES = (Ets['Devs/error'], )

    # BackgroundColor
    color: np.array = [0.35, 0.35, 0.5, 1.0]
    color2: np.array = [1.0, 0.35, 0.5, 1.0]

    # Singleton
    __instance = None

    shader = 'BackgroundShader'

    def __init__(self, gr):
        self.texture = 0
        self.colors = [
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
class Trigger(phys):
    shape_filter = shapeFilter('trigger', )
    body_type = 'kinematic'

    """Area that will call given function if something intersects it and/or leaves it"""
    __slots__ = (
        'function_enter', 'function_leave', 'collision_type', 'triggers_by',
        'ignore', 'pos', 'bound_to', 'offset', 'size', 'entities'
    )

    def __init__(self, function_enter, categories, function_leave=None, triggers_by=(), ignore=(),
                 pos=(0, 0), bound_to=None, offset=(0, 0), size=None):
        super().__init__(pos, points=rectPoints(*size), )
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
        and d'nt leave Trigger"""

        # Checking errors
        if pos != (0, 0) and bound_to:
            raise ValueError('Trigger requires only one of provided args: pos, bound_to')
        if not pos and not bound_to:
            raise ValueError('Trigger requires one of provided args: pos, bounded_to')
        if bound_to and not hasattr(bound_to, 'pos'):
            raise ValueError('Wrong arg: bound_to object must have .pos() method')
        for category in categories:
            if category not in COLLISION_CATEGORIES:
                raise ValueError(f'Category {category} does not exist\n'
                                 f'Chose from {COLLISION_CATEGORIES.keys()}')

        # Attrs
        self.function_leave, self.function_enter = function_leave, function_enter
        self.triggers_by, self.ignore = triggers_by, ignore
        self.bound_to, self.offset = bound_to, offset
        self.entities = set()

        # Add to new triggers. Check core.screens.game.update() for more info
        triggers.append(self)

    def __repr__(self):
        return f'<Trigger Pos: {self.body.pos}. Bounded to: {self.bound_to}>'

    def delete_physic(self):
        triggers.remove(self)
        super().delete_from_physic()

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
class Character(image, phys):
    body_type = 'dynamic'

    MAX_JUMPS = 2
    WALKING_VEC = 0
    JUMP_VECTOR = Vec2d(0, 0)
    MAX_WALKING_SPEED = 0
    IN_AIR_MOVE = 0.8  # sec
    THROW_POWER = Vec2d(4000, 500)

    __grabbed_filter: ShapeFilter
    grabbed_item_offset = np.array([70, 0], dtype=np.float32)

    __previous_pos: np.array

    def __init__(self, group, pos, *args, **kwargs):
        super().__init__(group, pos, *args, **kwargs)
        phys.__init__(self, pos, )

        # Walking, Running
        self.walk_direction = 0  # may be -1 - move to  the left, 0 - standing, 1 - move to the right
        self.walking_vec = self.__class__.WALKING_VEC
        self.max_walking_speed = self.__class__.MAX_WALKING_SPEED
        self.__previous_pos = self.pos

        # Jumping
        self.jumps = 0
        self.jump_delay_current = 0
        self.max_jumps = self.__class__.MAX_JUMPS
        self.jump_vec = self.__class__.JUMP_VECTOR

        # Grab
        self.grab_distance = 60
        self.grabbed_object = None
        self.grab_trigger = Trigger(None, bound_to=self,
                                    size=(80, 80), triggers_by=['WoodenCrate', ])
        self.__grabbedFilter = None

        # Blocks rotation. Characters stand on their feet
        self.can_rotate(False)

        self.on_ground = False  # is Character standing on solid floor
        self.in_air = 0  # How long din't Character touch solid flour

        # If False, unlocks velocity limits and ignores walking_direction, jump()
        self.can_move = True

    def update(self, *args, **kwargs) -> None:
        super().update(*args, **kwargs)
        dt = args[0]

        # Grabbed object update
        if self.grabbed_object:
            self.grabbed_object.pos = self.pos + self.grabbed_item_offset * self.y_Rotation
            self.grabbed_object.body.velocity = (0, 0)

        #
        if not self.check_on_ground():
            self.in_air += dt

        # Walking
        self.walk(dt)
        self.__previous_pos = self.pos

    def check_on_ground(self):
        if (self.pos[1] == self.__previous_pos[1]) or (self.body.velocity[1] == 0):
            self.touch_ground()
            return True
        self.untouch_ground()
        return False

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
        self.set_rotation_y(self.walk_direction)

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
        target.shape.filter = filterAddIgnore(target.shape_filter, self.shape.filter.categories)

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
    def touch_ground(self):
        self.jumps = 0
        self.on_ground = True
        self.in_air = 0

    def untouch_ground(self):
        self.on_ground = False
        if self.jumps == 0:
            self.jumps = 1


# vvv DEFINE YOUR CLASSES HERE vvv #

class MainHero(Character, direct, mortal):
    # RENDER
    TEXTURES = [Ets['LevelOne/r_pebble_grass_1'], ]
    size = (64, 144)

    # PHYSIC
    shape_filter = shapeFilter('player', ignore=('particle', 'bg_obstacle'))
    points = rectPoints(*size)
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

    def __init__(self, gr, pos, layer=4):
        Character.__init__(self, gr, pos, MainHero.size, layer=layer)
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
    shape_filter = shapeFilter('bg_obstacle', ignore=('player', 'enemy', 'particle'))

    # static
    TEXTURES = (Ets['LevelOne/crate'], )
    size = (72, 72)
    points = rectPoints(*size)

    # dynamic
    mass = 20.0

    # mortal
    max_health = 10
    lethal_fall_velocity = 64

    def __init__(self, gr, pos):
        super().__init__(gr, pos, size=self.__class__.size)
        phys.__init__(self, pos)
        self.init_mortal(self.__class__)

    def post_collision_handle(self, impulse, **data):
        impulse = impulse.length
        if impulse > 4000:
            AudioManager.play_sound('crate_wood_hit', self.pos, self.body.velocity, volume=impulse / 20000)


# ^^^ DEFINE YOUR CLASSES HERE ^^^ #


"""Storage of all Direct objects. 
Can be accessed by WorldEditor, LevelLoader and create_object() function"""
allObjects = {}
for x in direct.__subclasses__():
    allObjects[x.__name__] = x


def summon(entity_type, *args, **kwargs):
    """Create object of given type with given args"""
    new = allObjects[entity_type](*args, **kwargs)
    print(f'+object: {new}\nbhash:{new.bhash if hasattr(new, "bhash") else None}')
    return new
