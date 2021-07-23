from core.physic.physics import PhysicObject
from core.objects.gObjectTools import shapeFilter, deleteObject
from core.rendering.PyOGL import RenderObjectStatic
from core.rendering.Textures import EssentialTextureStorage as Ets
from core.rendering.Lighting import LightSource

from math import sin, cos, radians
from random import randint


class Particle(RenderObjectStatic, PhysicObject):
    points = None
    body_type = 'dynamic'
    collision_type = 'particle'
    shape_filter = shapeFilter(categories=('particle', ), collide_with=('obstacle', ))

    # static
    TEXTURES = Ets

    # dynamic
    mass = 1.0

    def __init__(self, gr, pos, texture, mass=None):
        self.texture = texture
        super().__init__(gr, pos, size=Ets[texture].size)
        PhysicObject.__init__(self, pos, radius=4, mass=mass)
        self.can_rotate(False)

    @classmethod
    def create(cls, gr, texture, pos, amount: tuple, speed: tuple, angle: tuple = (0, 360), mass: float = 0.0):
        """
        :param gr: RenderGroup
        :param texture:
        :param pos:
        :param amount: (min, max)
        :param speed: (min, max)
        :param angle: (min, max) in degrees
        :param mass: (min, max)
        :return:
        """
        rd = randint
        for _ in range(rd(*amount)):
            a = radians(rd(*angle))
            vel = [x * rd(*speed) for x in (cos(a), sin(a))]
            p = cls(gr, pos, texture, mass=mass)
            p.body.apply_impulse_at_local_point(vel, (0, 0))

    def pre_collision_handle(self, impulse, **data):
        deleteObject(self)
        return False


class LightParticle():
    pass
