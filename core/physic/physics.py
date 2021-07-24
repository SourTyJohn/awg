import pymunk
from core.math.linear import normalized_to_degree
from core.Constants import \
    GRAVITY_VECTOR, COLL_TYPES, BODY_TYPES, FLOAT32, SLEEP_TIME_THRESHOLD
inf = float('inf')
from beartype import beartype


objects = {}
"""Includes all physic objects and triggers
::keys       obj.body.__hash__()
::values     obj

CollisionHandlers can only get object's shape and body,
so I need this dict to getting real PhysicObject from it's body hash
"""
triggers = []


class Body(pymunk.Body):
    hash_key = None

    @property
    def get_hash_key(self):
        if not self.hash_key:
            self.hash_key = self.__hash__()
        return self.hash_key

    @property
    def pos(self):
        return self._get_position()

    @pos.setter
    def pos(self, value):
        self._set_position(value)

    @property
    def pos_FLOAT32(self):
        p = self.pos
        yield FLOAT32(p.x)
        yield FLOAT32(p.y)

    @property
    def angle(self):
        return self._get_angle()

    @angle.setter
    def angle(self, value):
        self._set_angle(value)


class PhysicObject:
    # __slots__ = ('shape', 'body', )
    """Main class of game object with physic body powered by pymunk
    Recommended to specify object's params in it's class attributes.
    """

    points: list
    """points of hitbox shape
    Must define in subclasses, except WorldRectangle objects"""

    mass: float = 1.0
    density: float = 1.0
    friction: float = 1.0
    """Physic body params.
    Can be changed in subclasses."""

    body_type = 'static'
    """
    'static': pymunk.Body.STATIC,       Level geometry
    'dynamic': pymunk.Body.DYNAMIC,     Moving objects
    'kinematic': pymunk.Body.KINEMATIC  Level objects, that can be moved by The Power of Code
    """
    collision_type = 'obstacle'
    shape_filter = None

    def __init__(self, pos, points=None, collision_type=None, shape_filter=None, radius=None, mass=None):
        """You can specify points for polygon shape or radius for circle shape
        Do not specify both of them"""
        """If no data given, than take it from class. Usually it is not given.
        Only exception is WorldRectangles"""
        cls = self.__class__
        points = (cls.points if points is None else points) if not radius else None
        collision_type = cls.collision_type if not collision_type else collision_type
        shape_filter = cls.shape_filter if not shape_filter else shape_filter
        mass = cls.mass if not mass else mass
        body_type = cls.body_type

        # Pymunk things. Make Shape and Body
        if radius:  # Circle
            self.body = makeBodyCircle(pos, radius, body_type, mass)
            self.shape = makeShapeCircle(self.body, radius, collision_type,
                                         cls.friction, shape_filter=shape_filter)
        else:       # Polygon
            self.body = makeBodyPolygon(pos, points, body_type, mass)
            self.shape = makeShapePolygon(self.body, points, collision_type,
                                          cls.friction, shape_filter=shape_filter)

        # Collision type
        if collision_type not in COLL_TYPES.keys():
            raise ValueError(f'Wrong collision type: {collision_type}.\n'
                             f'Select from {list(COLL_TYPES.keys())}')
        self.shape.collision_type = COLL_TYPES[collision_type]

        # Collision handler
        pass

        # Add to world (Physic simulation)
        MainPhysicSpace.add(self, self.body, self.shape)

        if hasattr(self, '_render_type'):
            self._render_type = 1

    @classmethod  # factory method
    def make_circle(cls, pos, radius, collision_type=None, shape_filter=None):
        return PhysicObject(pos, points=None, collision_type=collision_type,
                            shape_filter=shape_filter, radius=radius)

    def can_rotate(self, b):
        if b:
            pass
        else:
            self.body.moment = inf

    @property
    def bhash(self):
        return self.body.get_hash_key

    def update(self, *args, **kwargs) -> None:
        pass

    def delete_physic(self):
        # Fully deleting object from physic world
        MainPhysicSpace.vanish(self)

    # PHYSIC
    @property
    def z_rotation(self):
        return normalized_to_degree(self.body.rotation_vector)

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

    @property
    def pos(self):
        return self.body.pos

    @pos.setter
    def pos(self, value):
        self.body.pos = value

    def post_collision_handle(self, impulse, **data) -> bool:
        # rewrite in child-classes
        return True

    def pre_collision_handle(self, impulse, **data) -> bool:
        # rewrite in child-classes
        return True


class World:
    __instance = None
    """Pymunk.World singleton abstraction"""

    def __init__(self):
        # setting up space
        self.space = pymunk.Space()
        self.space.gravity = GRAVITY_VECTOR
        self.space.sleep_time_threshold = SLEEP_TIME_THRESHOLD

        # setting up collision handlers
        from core.physic.collision_handlers import setup
        setup(self.space)

    def vanish(self, obj):
        # Delete object from world
        del objects[obj.bhash]
        self.space.remove(obj.body, obj.shape)

    def vanish_by_key(self, key):
        # Same with vanish, but deletion is made by key
        obj = objects.pop(key)
        self.space.remove(obj.body, obj.shape)

    def add(self, obj, body, *shapes):
        # Add object to world
        self.space.add(body, *shapes)
        objects[body.get_hash_key] = obj

    def step(self, dt):
        self.space.step(dt)
        self.update_triggers(dt)

    @staticmethod
    @beartype
    def update_triggers(dt: float):
        for tr in triggers:
            tr.update(dt)

    @staticmethod
    def clear():
        # Clearing physic world
        while objects.values():
            obj = list(objects.values())[0]
            # Physically delete object
            obj.__class__.delete_physic(obj, )


def makeBodyPolygon(pos, points, body_type, mass=0.0, moment=0):
    if mass:
        moment = pymunk.moment_for_poly(mass, points, (0, 0))
    body = Body(mass, moment, body_type=BODY_TYPES[body_type])
    body.pos = pos if pos else (0, 0)
    return body


def makeShapePolygon(body, points, collision_type, friction=0.0, sensor=False, shape_filter=None):
    shape = pymunk.Poly(body, points)
    shape.collision_type = COLL_TYPES[collision_type]
    shape.friction = friction
    shape.sensor = sensor

    if shape_filter:
        shape.filter = shape_filter

    return shape


def makeBodyCircle(pos, radius, body_type, mass=0.0, moment=0):
    if mass:
        moment = pymunk.moment_for_circle(mass, radius, radius)
    body = Body(mass, moment, body_type=BODY_TYPES[body_type])
    body.pos = pos if pos else (0, 0)
    return body


def makeShapeCircle(body, radius, collision_type, friction=0.0, sensor=False, shape_filter=None):
    shape = pymunk.Circle(body, radius)
    shape.collision_type = COLL_TYPES[collision_type]
    shape.friction = friction
    shape.sensor = sensor

    if shape_filter:
        shape.filter = shape_filter

    return shape


def reyCast(start, end, shape_filter: pymunk.ShapeFilter = None, first_only=False, radius=1):
    if first_only:
        return MainPhysicSpace.space.segment_query_first(start, end, shape_filter=shape_filter, radius=radius)
    return MainPhysicSpace.space.segment_query(start, end, shape_filter=shape_filter, radius=radius)


MainPhysicSpace = World()
