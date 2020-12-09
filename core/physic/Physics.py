from core.rendering.PyOGL import GLObjectBase, Sprite
import pymunk
from core.Math.DataTypes import vec_unit_to_degree
from core.Constants import GRAVITY_VECTOR, COLL_TYPES, BODY_TYPES


objects = {}
"""Includes all physic objects and triggers
::key       obj.body.__hash__()
::value     obj

CollisionHandlers can only get object's shape and body,
so I need this dict to getting real PhysicObject from it's body hash
"""

new_triggers = set()
"""recently added Triggers. Check core.screens.game.update() for more info"""


class PhysicObject(GLObjectBase):
    __slots__ = ('shape', 'body', )
    """Main class of game object with physic body powered by pymunk
    Recommended to specify object's params in it's class attributes.
    """

    size: list
    """Size of texture. Does not affect physic
    Must define in subclasses, except WorldRectangle objects"""

    hitbox_data: tuple
    """Size of physic body (pymunk.Body)
    Must define in subclasses, except WorldRectangle objects"""

    mass: float = 1.0
    density: float = 1.0
    friction: float = 1.0
    """Physic body params.
    Can be changed in subclasses."""

    def __init__(self, group, pos, collision_type='prop', size=None,
                 hitbox=None, body_type=0, tex_offset=(0, 0), texture=0):

        """If no data given, than take it from class. Usually it is not given.
        Only exception is WorldRectangles"""
        cls = self.__class__
        hitbox = cls.hitbox_data if hitbox is None else hitbox
        size = cls.size if size is None else size

        #
        self.texture = texture
        super().__init__(group, rect=[*pos, *size], tex_offset=tex_offset)

        # Make points of shape from hitbox_data
        points = rect_points(hitbox[2] / 2, hitbox[3] / 2, hitbox[0], hitbox[1])

        # Pymunk things. Make Shape and Body
        mass = cls.mass
        moment = pymunk.moment_for_poly(mass, points, (0, 0))
        self.body = pymunk.Body(mass, moment, body_type=BODY_TYPES[body_type])
        self.body.position = pos
        self.shape = pymunk.Poly(self.body, points)
        self.shape.friction = cls.friction

        # Collision type
        if collision_type not in COLL_TYPES.keys():
            raise ValueError(f'Wrong collision type: {collision_type}.\n'
                             f'Select from {list(COLL_TYPES.keys())}')
        self.shape.collision_type = COLL_TYPES[collision_type]

        # Add to world (Physic simulation)
        world.add(self.body, self.shape)

        # Add to objects dictionary
        objects[self.bhash] = self

    @property
    def bhash(self):
        return self.body.__hash__()

    def update(self, *args, **kwargs) -> None:
        pass

    def getPos(self):
        """.rect object of Physic body used only for getting size of texture
        position taken from physic body"""
        return self.body.position

    def delete(self):
        # Fully deleting object from physic world
        world.vanish(self)

        #
        super().delete()

    def draw(self, shader):
        """Drawing of PhysicObject uses rotation of own pymunk.body
        vec_unit_to_degree from DataTypes module"""

        if self.visible:
            rotation = vec_unit_to_degree(self.body.rotation_vector) - 90

            self.__class__.TEXTURES[self.texture].draw(
                self.body.position, self.vbo, shader, z_rotation=rotation
            )

    # physic
    @property
    def bmass(self):
        return self.body.mass

    @bmass.setter
    def bmass(self, value):
        self.bmass = value

    @property
    def bfriction(self):
        return self.shape.friction

    @bfriction.setter
    def bfriction(self, value):
        self.shape.friction = value


class DynamicObject(PhysicObject):
    """Movable physic object"""
    def __init__(self, group, pos, collision_type, size=None,
                 tex_offset=(0, 0), texture=0, hitbox=None):
        super().__init__(group, pos, collision_type,  size=size, body_type=1,
                         hitbox=hitbox, tex_offset=tex_offset, texture=texture)


class StaticObject(PhysicObject):
    """Unmovable physic object"""
    def __init__(self, group, pos, collision_type, size=None,
                 tex_offset=(0, 0), texture=0, hitbox=None):
        super().__init__(group, pos, collision_type, size=size, body_type=0,
                         hitbox=hitbox, tex_offset=tex_offset, texture=texture)


class World:
    __instance = None
    """Pymunk.World singleton abstraction"""

    def __init__(self):

        # setting up space
        self.space = pymunk.Space()
        self.space.gravity = GRAVITY_VECTOR
        self.space.sleep_time_threshold = 0.3

        # setting up collision handlers
        from core.physic.CollisionHandlers import setup
        setup(self.space)

    def vanish(self, obj):
        # Delete object from world
        self.space.remove(obj.body, obj.shape)

    def add(self, *args):
        # Add object to world
        self.space.add(*args)

    def step(self, dt):
        self.space.step(dt)


class Trigger(Sprite):
    """Area that will call given function if something intersects it and/or leaves it"""
    __slots__ = (
        'function_enter', 'function_leave', 'collision_type', 'triggers_by',
        'ignore', 'pos', 'bound_to', 'offset', 'size', 'entities'
    )

    def __init__(self, function_enter, collision_type, function_leave=None, triggers_by=(), ignore=(),
                 pos=(), bound_to=None, offset=(0, 0), size=None):
        super().__init__()

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

        ::arg triggers_by - tuple of classes from GameObjects.py,
        that can activate this trigger
        If empty, than trigger can be activated by every object of given collision type
        
        ::arg ignore - tuple of classes from GameObject.py,
        that can not activate this trigger
        If empty, than there is no ignored objects
        
        ::arg entities - list of body.__hash__ of all objects that entered
        and d'nt leave Trigger"""

        # Checking errors
        if pos and bound_to:
            raise ValueError('Trigger requires only one of provided args: pos, bound_to')
        if not pos and not bound_to:
            raise ValueError('Trigger requires one of provided args: pos, bounded_to')
        if bound_to and not hasattr(bound_to, 'getPos'):
            raise ValueError('Wrong arg: bound_to object must have .getPos() method')
        if collision_type not in COLL_TYPES.keys():
            raise ValueError(f'Wrong collision type: {collision_type}.\nSelect from {list(COLL_TYPES.keys())}')

        # Attrs
        self.function_leave, self.function_enter = function_leave, function_enter
        self.triggers_by, self.ignore = triggers_by, ignore
        self.bound_to, self.offset = bound_to, offset
        self.collision_type = collision_type
        self.entities = set()

        # Static body and shape
        self.body = pymunk.Body(0, 0, body_type=BODY_TYPES[2])
        self.body.position = pos if pos else (0, 0)
        self.shape = pymunk.Poly(self.body, rect_points(size[0], size[1]))
        self.shape.collision_type = COLL_TYPES[collision_type]
        self.shape.sensor = True

        # Add to world (Physic simulation)
        world.add(self.body, self.shape)

        # Add to new triggers. Check core.screens.game.update() for more info
        new_triggers.add(self)

        # Adding Trigger to objects dict
        objects[self.bhash] = self

    def delete(self):
        world.vanish(self)
        self.kill()

    @property
    def bhash(self):
        return self.body.__hash__()

    def __repr__(self):
        return f'<Trigger Pos: {self.body.position}. Bounded to: {self.bound_to}>'

    def draw(self, *args):
        pass

    def update(self, *args, **kwargs):

        # Trigger static and won't move
        if not self.bound_to:
            return

        # Trigger bounded to object
        self.body.position = self.bound_to.getPos() + self.offset

    def enter(self, actor, arbiter):
        if actor is self.bound_to or actor in self.ignore or not self.function_enter:
            return

        self.entities.add(actor.bhash)

        if self.triggers_by:
            if actor.__class__ in self.triggers_by:
                return self.function_enter(actor, self.bound_to, world, arbiter)
        else:
            return self.function_enter(actor, self.bound_to, world, arbiter)

    def leave(self, actor, arbiter):
        if actor is self.bound_to or actor in self.ignore or not self.function_leave:
            return

        self.entities.remove(actor.bhash)

        if self.triggers_by:
            if actor.__class__ in self.triggers_by:
                return self.function_leave(actor, self.bound_to, world, arbiter)
        else:
            return self.function_leave(actor, self.bound_to, world, arbiter)


def rect_points(w, h, x_=0, y_=0):
    """
    ::args      width height offset_x offset_y
    ::returns   tuple of rect vertexes with given params
    """

    return (
        (-w + x_, -h + y_),
        (-w + x_, +h + y_),
        (+w + x_, +h + y_),
        (+w + x_, -h + y_)
    )


world = World()
