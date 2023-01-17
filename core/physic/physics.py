import pymunk
from pymunk import Vec2d

from core.math.linear import degreesFromNormal
from core.Constants import \
    GRAVITY_VECTOR, BODY_TYPES, SLEEP_TIME_THRESHOLD, MAX_PHYSIC_STEP
from core.Typing import TYPE_VEC, FLOAT32, List, PhysicProperties, TYPE_NUM
inf = float('inf')
from beartype import beartype

from pymunk.shapes import cp


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
        v = cp.cpBodyGetPosition(self._body)
        return Vec2d(v.x, v.y)

    @pos.setter
    def pos(self, value):
        cp.cpBodySetPosition(self._body, value)

    @property
    def pos_FLOAT32(self):
        v = cp.cpBodyGetPosition(self._body)
        yield FLOAT32(v.x)
        yield FLOAT32(v.y)

    @property
    def angle(self):
        return cp.cpBodyGetAngle(self._body)

    @angle.setter
    def angle(self, value):
        cp.cpBodySetAngle(self._body, value)


class PhysicObject:
    """Main class of game object with physic body powered by pymunk
    Recommended to specify object's params in its class attributes.
    """

    points: list
    """points of hitbox shape
    Must define in subclasses, except WorldRectangle objects"""

    physic_data: PhysicProperties
    """Must define in subclasses"""

    def __init__(self, body: "Body", shape: pymunk.Shape):
        self.body, self.shape = body, shape
        MainPhysicSpace.add_object(self)
        MainPhysicSpace.add(self.body, self.shape)

    @classmethod
    def Polygon(cls, _inst, pos, points: tuple, physic_props: PhysicProperties = None):
        if physic_props is None:
            physic_props = _inst.physic_data
        mass, body_type, friction, shape_filter, elasticity = physic_props.get()

        body = makeBodyPolygon(pos, points, body_type, mass)
        shape = makeShapePolygon(
            body, points, friction, shape_filter=shape_filter, elasticity=elasticity
        )
        return cls.__init__(_inst, body, shape)

    @classmethod
    def Circle(cls, _inst, pos, radius: TYPE_NUM, physic_props: PhysicProperties = None):
        if physic_props is None:
            physic_props = _inst.physic_data
        body_type, shape_filter, mass, friction, elasticity = physic_props.get()

        body = makeBodyCircle(pos, radius, body_type, mass)
        shape = makeShapeCircle(
            body, radius, friction, shape_filter=shape_filter, elasticity=elasticity
        )
        return cls.__init__(_inst, body, shape)

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

    @property
    def BB(self) -> pymunk.BB:
        return self.shape.cache_bb()

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

    @property
    def shape_filter(self):
        return self.shape.filter

    @shape_filter.setter
    def shape_filter(self, value: pymunk.ShapeFilter):
        self.shape.filter = value
        self.shape.collision_type = value.categories

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
        # self.space.sleep_time_threshold = SLEEP_TIME_THRESHOLD
        self.space.collision_slop = 0.05
        self.space.iterations = 12

        self.__add_query = []
        self.__del_query = []

        # setting up collision handlers
        from core.physic.collision_handlers import setup
        setup(self.space)

    def vanish(self, obj):
        # Delete object from world
        del objects[obj.bhash]
        self.delete(obj.body, obj.shape)

    @staticmethod
    def add_object(obj):
        objects[obj.body.get_hash_key] = obj

    def add(self, *args):
        for f in args:
            self.__add_query.append(f)

    def delete(self, *args):
        for f in args:
            self.__del_query.append(f)

    def step(self, dt: float):
        dt = min( dt, MAX_PHYSIC_STEP )
        self.space.step(dt)
        self.update_triggers(dt)
        self.post_step()
        return dt

    def post_step(self):
        self.space.add(*self.__add_query)
        self.__add_query = []

        self.space.remove(*self.__del_query)
        self.__del_query = []

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

    def get_geometry(self, camera):
        pass


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
def makeShapePolygon(body, points, friction=0.0, sensor=False, shape_filter=None, elasticity=0):
    shape = pymunk.Poly(body, points)

    shape.friction = friction
    shape.sensor = sensor
    shape.collision_type = shape_filter.categories
    shape.elasticity = elasticity

    if shape_filter:
        shape.filter = shape_filter

    return shape


def makeShapeCircle(body, radius, friction=0.0, sensor=False, shape_filter=None, elasticity=0):
    shape = pymunk.Circle(body, radius)
    shape.friction = friction
    shape.sensor = sensor
    shape.collision_type = shape_filter.categories
    shape.density = elasticity

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
    MainPhysicSpace.add(joint)
    return joint


def attachSoft(a: "Body", b: "Body", rest_length: float, stiffness: float,
               damping: float, point_a=None, point_b=None):
    point_a = point_a if point_a else a.center_of_gravity
    point_b = point_b if point_b else b.center_of_gravity
    joint = pymunk.DampedSpring(
        a, b, point_a, point_b, rest_length, stiffness, damping)
    MainPhysicSpace.add(joint)
    return joint


# singleton world object
MainPhysicSpace = World()
