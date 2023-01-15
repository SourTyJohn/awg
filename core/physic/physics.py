import pymunk
from core.math.linear import degreesFromNormal
from core.Constants import \
    GRAVITY_VECTOR, BODY_TYPES, SLEEP_TIME_THRESHOLD, MAX_PHYSIC_STEP
from core.Typing import TYPE_VEC, FLOAT32
inf = float('inf')
from typing import List

from pymunk._chipmunk import lib as cp


objects = {}
"""Includes all physic objects and triggers
::keys       obj.body.__hash__()
::values     obj

CollisionHandlers can only get object's shapes and body,
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
        v = cp.cpBodyGetPosition(self._body)
        return pymunk.Vec2d(v.x, v.y)

    @pos.setter
    def pos(self, value: TYPE_VEC):
        cp.cpBodySetPosition(self._body, value)

    @property
    def pos_FLOAT32(self):
        v = cp.cpBodyGetPosition(self._body)
        return FLOAT32(v.x), FLOAT32(v.y)

    @property
    def angle(self):
        return cp.cpBodyGetAngle(self._body)

    @angle.setter
    def angle(self, value):
        cp.cpBodySetAngle(self._body, value)


class PhysicObject:
    # __slots__ = ('shapes', 'body', )
    """Main class of game object with physic body powered by pymunk
    Recommended to specify object's params in its class attributes.
    """

    """
    Shape
        points
        mass
        friction=0.0
        sensor=False
        shape_filter=None
        elasticity=0

    body_type
        'static': pymunk.Body.STATIC,       Level geometry
        'dynamic': pymunk.Body.DYNAMIC,     Moving objects
        'kinematic': pymunk.Body.KINEMATIC  Level objects, that can be moved by The Power of Code
    """

    def __init__(self, pos, body_type, shapes: List[dict], **kwargs):
        """You can specify points for polygon shapes or radius for circle shapes
        Do not specify both of them"""
        """If no data given, than take it from class. Usually it is not given.
        Only exception is WorldRectangles"""
        self.body = makeEmptyBody(pos, body_type)
        self.shapes = []
        for shape_data in shapes:
            if "radius" in shape_data.keys():
                shape = makeShapeCircle(self.body, **shape_data)
            else:
                shape = makeShapePolygon(self.body, **shape_data)
            self.shapes.append(shape)

        # Add to world (Physic simulation)
        MainPhysicSpace.add(self, self.body, *self.shapes)

    def get_bb(self, shape: int) -> pymunk.bb.BB:  # Returns bounding box of object's shape
        _bb = self.shapes[shape].cache_bb()
        return _bb

    @property
    def single_BB_size(self):
        _bb = cp.cpShapeCacheBB(self.shapes[0])
        return pymunk.Vec2d(_bb.r - _bb.l, _bb.t - _bb.b)

    def can_rotate(self, b):
        if b:
            pass
        else:
            for s in self.shapes:

                s.moment = inf
        self.body.center_of_gravity

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

    def get_friction(self, shape):
        return self.shapes[shape].friction

    def set_friction(self, shape, value):
        self.shapes[shape].friction = value

    @property
    def body_friction(self):
        return self.shapes[0].friction

    @body_friction.setter
    def body_friction(self, value):
        for s in self.shapes:
            s.friction = value

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

    @property
    def shape_filter(self):
        return self.shapes[0].filter

    def set_shape_filter(self, shapes, shape_filter):
        for s in shapes:
            self.shapes[s].filter = shape_filter
            self.shapes[s].collision_type = shape_filter.categories

    def post_collision_handle(self, arbiter: pymunk.Arbiter, space: pymunk.Space) -> bool:
        # rewrite in child-classes
        return True

    def pre_collision_handle(self, arbiter: pymunk.Arbiter, space: pymunk.Space) -> bool:
        # rewrite in child-classes
        return True

    def should_update(self) -> bool:
        pass

    def update(self, dt) -> bool:
        pass


class World:
    __instance = None
    """Pymunk.World singleton abstraction"""

    def __init__(self):
        # setting up space
        self.space = pymunk.Space()
        self.space.gravity = GRAVITY_VECTOR
        self.space.sleep_time_threshold = SLEEP_TIME_THRESHOLD

        self.__delete_query = []
        self.__add_query = []

        # setting up collision handlers
        from core.physic.collision_handlers import setup
        setup(self.space)

    # DELETE OBJECTS
    def vanish(self, obj):
        # Delete object from world
        del objects[obj.bhash]
        self.delete_query(obj.body, obj.shapes)

    def vanish_by_key(self, key):
        # Same with vanish, but deletion is made by key
        obj = objects.pop(key)
        self.delete_query(obj.body, obj.shapes)

    def delete_query(self, *to_delete):
        for obj in to_delete:
            self.__delete_query.append( obj )
    #

    # ADD OBJECTS
    def add(self, obj, body, *shapes):
        # Add object to world
        self.add_query(body, *shapes)
        objects[body.get_hash_key] = obj

    def add_query(self, *to_add):
        for obj in to_add:
            self.__add_query.append(obj)
    #

    # ON UPDATE
    def step(self, dt: float):
        dt = max( dt, MAX_PHYSIC_STEP )
        self.space.step(dt)
        self.update_triggers(dt)
        return dt

    @staticmethod
    def update_triggers(dt: float):
        for tr in triggers:
            tr.update(dt)

    def post_step(self):
        self.space.remove( *self.__delete_query )
        self.__delete_query = []

        self.space.add( *self.__add_query )
        self.__add_query = []
    #

    # FINALLY
    @staticmethod
    def clear():
        # Clearing physic world
        while objects.values():
            obj = list(objects.values())[0]
            # Physically delete_Mortal object
            obj.__class__.delete_from_physic(obj, )


# MAKE BODY
def makeBodyPolygon(pos, points, body_type, mass=0, moment=0):
    if moment == 0:
        moment = pymunk.moment_for_poly(mass, points, (0, 0))
    body = Body(mass, moment, body_type=BODY_TYPES[body_type])
    body.pos = pos if pos else (0, 0)
    return body


def makeBodyCircle(pos, radius, body_type, mass=0, moment=0):
    if moment == 0:
        moment = pymunk.moment_for_circle(mass, radius, radius)
    body = Body(mass, moment, body_type=BODY_TYPES[body_type])
    body.pos = pos if pos else (0, 0)
    return body


def makeEmptyBody(pos, body_type):
    body = Body(body_type=BODY_TYPES[body_type])
    body.pos = pos
    return body


# MAKE SHAPE
def makeShapePolygon(body, points, mass, friction=1.0, sensor=False, shape_filter=None, elasticity=0):
    shape = pymunk.Poly(body, points)

    shape.friction = friction
    shape.sensor = sensor
    shape.collision_type = shape_filter.categories
    shape.elasticity = elasticity
    shape.mass = mass

    if shape_filter:
        shape.filter = shape_filter

    return shape


def makeShapeCircle(body, radius, mass, friction=1.0, sensor=False, shape_filter=None, elasticity=0):
    shape = pymunk.Circle(body, radius)
    shape.friction = friction
    shape.sensor = sensor
    shape.collision_type = shape_filter.categories
    shape.density = elasticity
    shape.mass = mass

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
    MainPhysicSpace.add_query(joint)
    return joint


def attachSoft(a: "Body", b: "Body", rest_length: float, stiffness: float,
               damping: float, point_a=None, point_b=None):
    point_a = point_a if point_a else a.center_of_gravity
    point_b = point_b if point_b else b.center_of_gravity
    joint = pymunk.DampedSpring(
        a, b, point_a, point_b, rest_length, stiffness, damping)
    MainPhysicSpace.add_query(joint)
    return joint


# singleton world object
MainPhysicSpace = World()
