import pymunk
from core.math.linear import degreesFromNormal
from core.Constants import \
    GRAVITY_VECTOR, BODY_TYPES, FLOAT32, SLEEP_TIME_THRESHOLD, TYPE_VEC
inf = float('inf')
from beartype import beartype
from typing import List


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

    _mass: float = 1.0
    _density: float = 1.0
    _friction: float = 1.0
    """Physic body params.
    Can be changed in subclasses."""

    body_type = 'static'
    """
    'static': pymunk.Body.STATIC,       Level geometry
    'dynamic': pymunk.Body.DYNAMIC,     Moving objects
    'kinematic': pymunk.Body.KINEMATIC  Level objects, that can be moved by The Power of Code
    """
    shape_filter = None

    def __init__(self, pos, points=None, shape_filter=None, radius=None, mass=None):
        """You can specify points for polygon shape or radius for circle shape
        Do not specify both of them"""
        """If no data given, than take it from class. Usually it is not given.
        Only exception is WorldRectangles"""
        cls = self.__class__
        points = (cls.points if points is None else points) if not radius else None
        shape_filter = cls.shape_filter if not shape_filter else shape_filter
        mass = cls._mass if not mass else mass
        body_type = cls.body_type

        # Pymunk things. Make Shape and Body
        if radius:  # Circle
            self.body = makeBodyCircle(pos, radius, body_type, mass)
            self.shape = makeShapeCircle(self.body, radius,
                                         cls._friction, shape_filter=shape_filter)
        else:       # Polygon
            self.body = makeBodyPolygon(pos, points, body_type, mass)
            self.shape = makeShapePolygon(self.body, points,
                                          cls._friction, shape_filter=shape_filter)

        # Collision handler
        pass

        # Add to world (Physic simulation)
        MainPhysicSpace.add(self, self.body, self.shape)

        if hasattr(self, '_render_type'):
            self._render_type = 1

    def can_rotate(self, b):
        if b:
            pass
        else:
            self.body.moment = inf

    @property
    def bhash(self):
        return self.body.get_hash_key

    def delete_from_physic(self):
        # Fully deleting object from physic world
        MainPhysicSpace.vanish(self)

    # PHYSIC
    @property
    def z_rotation(self):
        return degreesFromNormal(self.body.rotation_vector)

    @property
    def mass(self):
        return self.body.mass

    @mass.setter
    def mass(self, value):
        self.mass = value

    @property
    def friction(self):
        return self.shape.friction

    @friction.setter
    def friction(self, value):
        self.shape.friction = value

    @property
    def pos(self):
        return self.body.pos

    @pos.setter
    def pos(self, value):
        self.body.pos = value

    @property
    def velocity(self):
        return self.body.velocity

    @velocity.setter
    def velocity(self, value: TYPE_VEC):
        self.body.velocity = value

    def set_shape_filter(self, shape_filter):
        self.shape_filter = shape_filter
        self.shape.filter = shape_filter
        self.shape.collision_type = shape_filter.categories

    def post_collision_handle(self, arbiter: pymunk.Arbiter, space: pymunk.Space) -> bool:
        # rewrite in child-classes
        return True

    def pre_collision_handle(self, arbiter: pymunk.Arbiter, space: pymunk.Space) -> bool:
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

    def simple_add(self, *to_add):
        self.space.add(*to_add)

    def simple_delete(self, *to_delete):
        self.space.remove(*to_delete)

    def add_joints(self, *joints):
        self.space.add(*joints)

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
            # Physically delete_Mortal object
            obj.__class__.delete_from_physic(obj, )


# MAKE BODY
def makeBodyPolygon(pos, points, body_type, mass=0.0, moment=0):
    if moment == 0:
        moment = pymunk.moment_for_poly(mass, points, (0, 0))
    body = Body(mass, moment, body_type=BODY_TYPES[body_type])
    body.pos = pos if pos else (0, 0)
    return body


def makeBodyCircle(pos, radius, body_type, mass=0.0, moment=0):
    if moment == 0:
        moment = pymunk.moment_for_circle(mass, radius, radius)
    body = Body(mass, moment, body_type=BODY_TYPES[body_type])
    body.pos = pos if pos else (0, 0)
    return body


# MAKE SHAPE
def makeShapePolygon(body, points, friction=0.0, sensor=False, shape_filter=None):
    shape = pymunk.Poly(body, points)
    shape.friction = friction
    shape.sensor = sensor
    shape.collision_type = shape_filter.categories

    if shape_filter:
        shape.filter = shape_filter

    return shape


def makeShapeCircle(body, radius, friction=0.0, sensor=False, shape_filter=None):
    shape = pymunk.Circle(body, radius)
    shape.friction = friction
    shape.sensor = sensor
    shape.collision_type = shape_filter.categories

    if shape_filter:
        shape.filter = shape_filter

    return shape


# REY CAST
def reyCast(start: TYPE_VEC, end: TYPE_VEC,
            shape_filter: pymunk.ShapeFilter = None,
            radius=1) -> List[pymunk.SegmentQueryInfo]:
    return MainPhysicSpace.space.segment_query(
        start, end, radius, shape_filter)


def reyCastFirst(start: TYPE_VEC, end: TYPE_VEC,
                 shape_filter: pymunk.ShapeFilter = None,
                 radius=1) -> pymunk.SegmentQueryInfo:
    return MainPhysicSpace.space.segment_query_first(
        start, end, radius, shape_filter)


# JOINTS
def attachHard(a: "Body", b: "Body", point_a=None, point_b=None):
    point_a = point_a if point_a else a.center_of_gravity
    point_b = point_b if point_b else b.center_of_gravity
    joint = pymunk.PinJoint(a, b, point_a, point_b)
    MainPhysicSpace.add_joints(joint)
    return joint


def attachSoft(a: "Body", b: "Body", rest_length: float, stiffness: float,
               damping: float, point_a=None, point_b=None):
    point_a = point_a if point_a else a.center_of_gravity
    point_b = point_b if point_b else b.center_of_gravity
    joint = pymunk.DampedSpring(
        a, b, point_a, point_b, rest_length, stiffness, damping)
    MainPhysicSpace.add_joints(joint)
    return joint


# singleton world class
MainPhysicSpace = World()
