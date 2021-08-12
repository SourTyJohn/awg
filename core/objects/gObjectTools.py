from pymunk import ShapeFilter, Shape
from core.physic.physics import PhysicObject, Body
from core.rendering.PyOGL import RenderObjectAnimated, RenderObjectStatic, RenderObjectComposite
from core.rendering.PyOGL_line import drawLine
from core.rendering.Particles import ParticleManager
from core.Constants import FLOAT32, TYPE_FLOAT, INT64, TYPE_INT, INF, TYPE_VEC

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

    'RObjectAnimated',
    'RObjectStatic',
    'PObject',
    'RObjectComposite',
    'Direct',
    'Mortal',
    'Tracer',
    'Throwable'
]


# collision mask categories
COLLISION_CATEGORIES = ('obstacle', 'no_collision', 'enemy', 'level',
                        'player', 'light', 'trigger', 'particle', 'bg_obstacle')
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
    #  deletes image and physic body of obj
    # if DEBUG:
    #     print(f'Fully Deleted: {obj}')
    obj.delete()
    PhysicObject.delete_from_physic(obj)


@beartype
def posFromLeftBottomPoint(l_: TYPE_FLOAT, b_: TYPE_FLOAT, size):
    return l_ + size[0] / 2, b_ + size[1]


class InGameObject:
    """Direct access means that object complete and ready to be placed on level
       Subclasses of this class will be added to allObjects dict"""
    rect = None

    def __repr__(self):
        return f'<Direct obj: {self.__class__.__name__}> at pos: {self.rect[:2]}'


class Mortal:
    """Mortal means that object have .health: int and if .health <= 0 object will .die()
       Apply this to every DESTRUCTABLE OBJECT"""

    lethal_fall_velocity: int = -1
    """[y] velocity that will cause calling die()
    if set to -1, object can not get damage from falling
    if velocity[y] >= lethal_fall_velocity // 4 -> damage"""

    health: np.ndarray
    show_health_bar: int = 2  # 0 - no, 1 - yes, 2 - on damage

    def init_mortal(self, cls, health: list):
        """You need to call this in constructor of subclasses
        to fully integrate Mortal functionality"""
        self.health = np.array(health, dtype=INT64)

    def update(self, *args, **kwargs):
        pass

    def fall(self, vec):
        if self.lethal_fall_velocity == -1:
            return

        damage = abs(vec.length / self.lethal_fall_velocity)
        if damage < 0.35:
            return
        damage = round(damage ** 2 * self.health[1])
        self.get_damage(damage)

    def get_damage(self, amount: TYPE_INT, damage_type: int = 0):
        """
        :param amount: amount
        :param damage_type: 0 for int amount and 1 for percentage"""
        if damage_type == 0:
            self.health[0] -= amount
        else:
            self.health[0] -= INT64(self.health[1] * amount)

        if self.health[0] <= 0:
            self.die()

    def delete(self):
        pass

    def die(self):
        deleteObject(self)


class Throwable:
    """Additional interface to objects, that can be picked up and thrown
    You can add this only to classes with PhysicObject interface"""

    # own
    touchable_after_throw: bool = True
    __default_shapeFilter: ShapeFilter
    __default_moment: Body.moment
    __throw_shapeFilter: ShapeFilter

    # physic object
    body: Body
    shape: Shape
    pos: TYPE_VEC

    @property
    def shape_filter(self):
        """Call this from PhysicObject"""
        return ShapeFilter

    def __init__(self, cls, filter_after_throw: ShapeFilter):
        self.__default_shapeFilter = cls.shape_filter
        self.__throw_shapeFilter = filter_after_throw
        self.__default_moment = self.body.moment

        self.__time_since_throw = 0.0
        self.__is_thrown = False

    def update(self, dt):
        if self.__is_thrown:
            self.__time_since_throw += dt
            ParticleManager.create(
                0, self.pos, (4, 4), (6, 12), (1, 1), (0.8, 0.0, 0.0, 0.6), (4, 4), None
            )

    def thrown(self, by, vec):
        self.__is_thrown = True

    def throw_hit(self):
        self.__time_since_throw = 0.0
        self.__is_thrown = False

    def grabbed(self, by):
        b = self.body
        b.moment = INF
        b.angular_velocity = 0
        b.angle = 0
        self.shape.filter = filterAddIgnore(self.shape_filter, by.shape.filter.categories)

    def putted(self, by):
        body = self.body
        body.moment = self.__default_moment
        body.velocity = by.body.velocity
        self.shape.filter = self.__default_shapeFilter


@dtc.dataclass
class Tracer:
    """This class remembers position of an given <actor> every <frequency> second.
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
    def update(self, dt: float) -> bool:
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


RObjectAnimated = RenderObjectAnimated
RObjectStatic = RenderObjectStatic
RObjectComposite = RenderObjectComposite
PObject = PhysicObject
Direct = InGameObject
