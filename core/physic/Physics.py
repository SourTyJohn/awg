from core.rendering.PyOGL import GLObjectBase
import pymunk


class Hitbox:
    """Hitbox class for detecting collision.
    Can be bounded to dynamic or fixed object"""
    __slots__ = ['offset', 'size', ]

    def __init__(self, offset, size):
        self.offset = offset
        self.size = size

    def getRectList(self, self_pos):
        return [self_pos[0] + self.offset[0], self_pos[1] + self.offset[1], *self.size]


class PhysicObject(GLObjectBase):
    size: list

    mass: int = 0
    density: float = 1.0
    friction: float = 0.5

    btypes = (
        pymunk.Body.STATIC,
        pymunk.Body.DYNAMIC
    )

    hitbox_data: Hitbox  # must define in subclasses
    shape: pymunk.Poly

    def __init__(self, group, pos, size='cls', hitbox='cls', body_type=0, tex_offset=(0, 0), texture=0):
        cls = self.__class__

        if size == 'cls':
            size = cls.size

        if hitbox == 'cls':
            hitbox = cls.hitbox_data

        self.texture = texture
        super().__init__(group, rect=[*pos, *size], tex_offset=tex_offset)

        s = hitbox.size
        points = (
            (0,     0),
            (0,     s[1]),
            (s[0],  s[1]),
            (s[0],  0)
        )

        mass = cls.mass
        moment = pymunk.moment_for_poly(mass, points, (0, 0))

        self.body = pymunk.Body(mass, moment, body_type=PhysicObject.btypes[body_type])
        self.body.position = pos[:]

        self.shape = pymunk.Poly(self.body, points)
        self.shape.friction = cls.friction

        world.space.add(self.body, self.shape)

    def update(self, *args, **kwargs) -> None:
        self.rect.center = self.body.position

    def draw(self, shader):
        if self.visible:
            print(self.body.rotation_vector)
            self.__class__.TEXTURES[self.texture].draw(self.rect.pos, self.vbo,
                                                       shader)


class DynamicObject(PhysicObject):
    def __init__(self, group, pos, size='cls', tex_offset=(0, 0), texture=0, hitbox='cls'):
        super().__init__(group, pos, size=size, body_type=1, hitbox=hitbox, tex_offset=tex_offset, texture=texture)
        pass


class StaticObject(PhysicObject):
    def __init__(self, group, pos, size='cls', tex_offset=(0, 0), texture=0, hitbox='cls'):
        super().__init__(group, pos, size=size, body_type=0, hitbox=hitbox, tex_offset=tex_offset, texture=texture)
        pass


class World:
    __instance = None

    def __init__(self):
        self.space = pymunk.Space()
        self.space.gravity = (0, -1600)
        self.space.sleep_time_threshold = 0.3

    def step(self, dt):
        dt = 1 / 60
        self.space.step(dt)


world = World()
