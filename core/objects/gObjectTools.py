from pymunk import ShapeFilter
from core.physic.physics import PhysicObject, Body
from core.rendering.PyOGL import \
    AnimatedRenderComponent, StaticRenderComponent, RenderObjectComposite,\
    RenderObjectPhysic, RenderObjectPlaced, MaterialRenderComponent
from core.Typing import FLOAT32, TYPE_FLOAT, INT64, TYPE_INT, INF, TYPE_NUM
from core.rendering.PyOGL_line import drawLine


from typing import Tuple
import dataclasses as dtc
import numpy as np
from collections import deque
from beartype import beartype


__all__ = [
    'COLLISION_CATEGORIES',

    'filterAddIgnore',
    'filterDelIgnore',
    'shapeFilter',
    'rectPoints',
    'deleteObject',
    'posFromLeftBottomPoint',
    'drawLine',

    'RC_Animated',
    'RC_Static',
    'RC_Composite',
    'RC_Material',

    'PhysObject',
    'PhysThrowable',

    'RO_Placed',
    'RO_Physic',

    'Direct',
    'Mortal',
    'Tracer',
    'PhysicObjectThrowable'
]


# collision mask categories
COLLISION_CATEGORIES = (
    'no_collision',
    'player',
    'level',
    'obstacle',
    'bg_obstacle',
    'enemy',
    'trigger',
    'particle'
)
COLLISION_CATEGORIES = {x: 2 ** i for i, x in enumerate(COLLISION_CATEGORIES)}


# SHAPE FILTER
def filterAddIgnore(filter_obj, categories):
    mask = filter_obj.mask
    if isinstance(categories, tuple):
        for x in categories:
            mask -= COLLISION_CATEGORIES[x]
    elif isinstance(categories, int):
        mask -= categories
    else:
        raise ValueError(f'Got {type(categories)} Accepts int or tuple')
    return ShapeFilter(group=filter_obj.group, categories=filter_obj.categories, mask=mask)


def filterDelIgnore(filter_obj, categories):
    mask = filter_obj.mask
    if isinstance(categories, tuple):
        for x in categories:
            mask += COLLISION_CATEGORIES[x]
    elif isinstance(categories, int):
        mask += categories
    else:
        raise ValueError(f'Got {type(categories)} Accepts int or tuple')
    return ShapeFilter(group=filter_obj.group, categories=filter_obj.categories, mask=mask)


def shapeFilter(category, ignore: Tuple = None, collide_with: Tuple = None) -> ShapeFilter:
    __doc__ = """
    arg:: ignore         list(tuple) of collision categories that won't collide with this mask
    arg:: collide_with   list(tuple) of collision categories that will collide with this mask
    Pass only one of described args"""
    if ignore is not None and collide_with is not None:
        raise ValueError('Pass only one of provided args: "ignore" "collide_with" ')
    if category not in COLLISION_CATEGORIES:
        raise ValueError(f'Category {category} does not exist\n'
                         f'Chose from {COLLISION_CATEGORIES.keys()}')

    # MASK
    mask = 4_294_967_295  # all 32-bit -> Collide with everything
    if ignore is not None:
        for x in ignore:
            mask -= COLLISION_CATEGORIES[x]

    elif collide_with is not None:
        mask = 0
        for x in collide_with:
            mask += COLLISION_CATEGORIES[x]

    # CATEGORIES
    cat = COLLISION_CATEGORIES[category]

    # COMPLETE
    return ShapeFilter(categories=cat, mask=mask)
#


def rectPoints(w, h, x_offset=0, y_offset=0) -> Tuple[Tuple, Tuple, Tuple, Tuple]:
    """
    ::args      width height offset_x offset_y
    ::returns   tuple of rect vertexes with given params
    """

    w /= 2
    h /= 2

    return (
        (-w + x_offset, -h + y_offset),
        (-w + x_offset, +h + y_offset),
        (+w + x_offset, +h + y_offset),
        (+w + x_offset, -h + y_offset)
    )


def deleteObject(obj):
    """Checks if object has image or/and physic body and deletes it/both
    Slowest deletion method, but universal"""
    if hasattr(obj, 'delete_Mortal'):
        obj.delete_Mortal()
    if hasattr(obj, 'body'):
        PhysicObject.delete_from_physic(obj)


@beartype
def posFromLeftBottomPoint(l_: TYPE_FLOAT, b_: TYPE_FLOAT, size):
    return l_ + size[0] / 2, b_ + size[1]


free_render_UIDs = set( range( 2 ** 16 ) )


class InGameObject:
    """Direct access means that object complete and ready to be placed on level
       Subclasses of this class will be added to allObjects dict"""

    _UID = 0

    @property
    def UID(self):
        if not self._UID:
            self._UID = free_render_UIDs.pop()
        return self._UID


class Mortal:
    """Mortal means that object have .health: int and if .health <= 0 object will .die_Mortal()
       Apply this to every DESTRUCTIBLE OBJECT"""

    __Mortal_lethal_fall_velocity: int = -1
    """[y] velocity that will cause calling die_Mortal()
    if set to -1, object can not get damage from falling
    if velocity[y] >= lethal_fall_velocity // 4 -> damage"""

    __Mortal_health: np.ndarray
    __Mortal_show_health_bar: int = 2  # 0 - no, 1 - yes, 2 - on damage

    def init_Mortal(self, cls, health: list):
        """You need to call this in constructor of subclasses
        to fully integrate Mortal functionality"""
        self.__Mortal_health = np.array(health, dtype=INT64)

    def update_Mortal(self, dt: float) -> None:
        pass

    def fall_Mortal(self, vec):
        if self.__Mortal_lethal_fall_velocity == -1:
            return

        damage = abs(vec.length / self.__Mortal_lethal_fall_velocity)
        if damage < 0.35:
            return
        damage = round(damage ** 2 * self.__Mortal_health[1])
        self.get_damage_Mortal(damage)

    def get_damage_Mortal(self, amount: TYPE_INT, damage_type: int = 0):
        """
        :param amount: amount
        :param damage_type: 0 for int amount and 1 for percentage"""
        if damage_type == 0:
            self.__Mortal_health[0] -= amount
        else:
            self.__Mortal_health[0] -= INT64(self.__Mortal_health[1] * amount)

        if self.__Mortal_health[0] <= 0:
            self.die_Mortal()

    def delete_Mortal(self):
        pass

    def die_Mortal(self):
        deleteObject(self)


class PhysicObjectThrowable(PhysicObject):
    """Additional interface to objects, that can be picked up and thrown
    You can add this only to classes with PhysicObject interface"""

    # own
    __Throwable_default_moment: Body.moment
    __Throwable_is_thrown: bool
    __Throwable_time_since_throw: float

    def __init__(self, body, shape):
        super(PhysicObjectThrowable, self).__init__(body, shape)

        self.__Throwable_default_moment = self.body.moment
        self.__Throwable_time_since_throw = 0.0
        self.__Throwable_is_thrown = False

    def update_Throwable(self, dt) -> bool:
        if self.__Throwable_is_thrown:
            self.__Throwable_time_since_throw += dt
            return True
        return False

    def thrown_Throwable(self, by, vec):
        self.__Throwable_is_thrown = True

    def throw_hit_Throwable(self):
        self.__Throwable_time_since_throw = 0.0
        self.__Throwable_is_thrown = False

    def grabbed_Throwable(self, by):
        b = self.body
        b.moment = INF
        b.angular_velocity = 0
        b.angle = 0
        self.shape.filter = filterAddIgnore(self.shape_filter, by.shape.filter.categories)

    def putted_Throwable(self, by):
        body = self.body
        body.moment = self.__Throwable_default_moment
        body.velocity = by.body.velocity
        self.shape_filter = self.physic_data["shape_filter"]


@dtc.dataclass
class Tracer:
    """This class remembers position of a given <actor> every <frequency> second.
    Actor must have defined .pos method.

    Works as queue. Last added data deleted if max amount of points achieved"""

    frequency: dtc.field(default_factory=float)
    points: dtc.field(default_factory=deque)
    time: dtc.field(default_factory=float)
    __started: dtc.field(default_factory=bool)

    def __init__(self, target, frequency=0.17, max_points=2):
        self.frequency = frequency
        self.target = target

        self.points = deque(maxlen=max_points)
        self.points.append(target.pos)
        self.time = 0.0
        self.__started = False

    def start(self):
        self.__started = True
        if self.time == 0.0:
            p = self.target.pos
            self.points.extend([p for _ in range(self.points.maxlen)])

    def pause(self):
        self.__started = False

    def stop(self):
        self.__started = False
        self.time = 0.0
        self.points = deque(maxlen=self.points.maxlen)

    @beartype
    def update_Tracer(self, dt: float) -> bool:
        """Must be called in actor's update method.
        There is no auto-update"""
        if not self.__started:
            return False

        self.time += dt
        if self.time >= self.frequency:
            self.time = 0
            self.points.append(self.target.pos)
        return True

    @beartype
    def __getitem__(self, item: int):
        return self.points[item]

    def to_array(self) -> np.ndarray:
        return np.array(self.points, dtype=FLOAT32)

    def clear(self):
        self.points.clear()


class Projectile(PhysicObject):
    def __init__(self, pos, points=None, radius=None, mass=None,
                 destroy_by: Tuple = (), max_time: float = -1.0):
        shape_filter = shapeFilter('projectile', collide_with=destroy_by)
        super().__init__(self, pos, points, shape_filter, radius, mass)
        self.projectile_max_time = max_time
        self.projectile_current_time = 0.0

    @beartype
    def update_Projectile(self, dt: float) -> None:
        self.projectile_current_time += dt
        if self.projectile_current_time >= self.projectile_current_time:
            deleteObject(self)

    @classmethod
    def from_angle(cls, speed: TYPE_NUM, angle: TYPE_INT):
        cls.__init__()


light_shape_filter = shapeFilter('obstacle', collide_with=('enemy', 'player', ) )


#  RENDER COMPONENTS
RC_Animated = AnimatedRenderComponent
RC_Static = StaticRenderComponent
RC_Composite = RenderObjectComposite
RC_Material = MaterialRenderComponent

#  RENDER OBJECTS
RO_Placed = RenderObjectPlaced
RO_Physic = RenderObjectPhysic  # requires PhysObject

PhysObject = PhysicObject
PhysThrowable = PhysicObjectThrowable
Direct = InGameObject
