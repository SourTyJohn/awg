from pymunk import ShapeFilter
from core.physic.physics import PhysicObject
from core.rendering.PyOGL import RenderObjectAnimated, RenderObjectStatic, RenderObjectComposite
from core.Constants import DEBUG


# collision mask categories
COLLISION_CATEGORIES = ('obstacle', 'no_collision', 'mortal', 'character', 'player', 'light', 'trigger', 'particle')
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


def shapeFilter(categories, ignore=None, collide_with=None):
    __doc__ = """
    arg:: ignore         list(tuple) of collision categories that won't collide with this mask
    arg:: collide_with   list(tuple) of collision categories that will collide with this mask
    Pass only one of described args"""
    if ignore is not None and collide_with is not None:
        raise ValueError('Pass only one of provided args: "ignore" "collide_with" ')
    if not all([c in COLLISION_CATEGORIES for c in categories]):
        raise ValueError(f'Some of categories from: {categories}'
                         f' does not exist. Chose from {COLLISION_CATEGORIES.keys()}')

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
    cat = 0
    for c in categories:
        cat += COLLISION_CATEGORIES[c]

    # COMPLETE
    return ShapeFilter(categories=cat, mask=mask)
#


def rectPoints(w, h, x_offset=0, y_offset=0):
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
    if DEBUG:
        print(f'Fully Deleted: {obj}')
    obj.delete()
    PhysicObject.delete_physic(obj)


class DirectAccessObject:
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

    shape_filter = shapeFilter(('mortal',), )

    # health
    health: int
    max_health: int

    # stamina
    stamina: int
    max_stamina: int

    def init_mortal(self, cls, health='max'):
        """You need to call this in constructor of subclasses
        to fully integrate Mortal functionality"""
        if health == 'max':
            self.health = cls.max_health

    def update(self, *args, **kwargs):
        pass

    def fall(self, vec):
        if self.lethal_fall_velocity == -1:
            return

        damage = abs(vec.length / self.lethal_fall_velocity)

        if damage < 0.35:
            return

        damage = round(damage ** 2 * self.max_health)
        self.get_damage(damage)

    def get_damage(self, amount):
        self.health -= amount
        if self.health <= 0:
            self.die()

    def die(self):
        deleteObject(self)


animated = RenderObjectAnimated
image = RenderObjectStatic
composite = RenderObjectComposite
phys = PhysicObject
direct = DirectAccessObject
mortal = Mortal
