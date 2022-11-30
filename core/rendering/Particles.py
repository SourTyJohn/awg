from core.rendering.PyOGL import bindEBO, LightingManager
from core.rendering.Shaders import shaders
from core.Constants import FLOAT32, ZERO_FLOAT32, MAX_PARTICLES
from core.math.linear import FullTransformMat
from core.math.random import randf
from pymunk import Body, Shape
from core.physic.physics import MainPhysicSpace, makeBodyCircle, makeShapeCircle
from core.objects.gObjectTools import shapeFilter, COLLISION_CATEGORIES

from math import sin, cos, radians
from random import randint
from beartype import beartype
import numpy as np
from typing import Dict, Tuple, Union
from pymunk import Vec2d
from dataclasses import dataclass, field


from OpenGL.GL import \
    glGenBuffers,\
    glDisable,\
    glEnable,\
    glBindBuffer,\
    glBufferData,\
    glDrawElements,\
    GL_POINTS,\
    GL_UNSIGNED_INT,\
    GL_ARRAY_BUFFER,\
    GL_STATIC_DRAW,\
    GL_DEPTH_TEST


__all__ = [
    "ParticleManager"
]


@dataclass
class Particle:
    __slots__ = (
        "position", "velocity", "gravity", "curr_time",
        "max_time", "color", "size"
    )

    position: field(default_factory=np.ndarray)
    velocity: field(default_factory=np.ndarray)
    gravity: field(default_factory=FLOAT32)
    curr_time: field(default_factory=float)
    max_time: field(default_factory=float)
    color: field(default_factory=np.ndarray)
    size: field(default_factory=np.ndarray)

    def update(self, dt) -> bool:
        self.position += self.velocity * dt
        self.position[1] -= self.gravity * dt
        self.curr_time -= dt
        if self.curr_time <= 0.0:
            return True
        return False

    def get_data(self):
        c = self.color
        return np.array(
            [*self.position, 0.5, *c[:-1], c[-1] * (self.curr_time / self.max_time), *self.size]
        ).flatten()

    def delete(self):
        pass


@dataclass
class PhysicParticle:
    __slots__ = (
        "body", "shape", "curr_time", "start_time",
        "color", "size", "delete_on_hit"
    )

    body: field(default_factory=Body)
    shape: field(default_factory=Shape)
    curr_time: field(default_factory=float)
    start_time: field(default_factory=float)
    color: field(default_factory=np.ndarray)
    size: field(default_factory=np.ndarray)
    delete_on_hit: field(default_factory=bool)

    def __init__(self, idd, ptype, body, shape, curr_time,
                 start_time, color, size, delete_on_hit):
        self.body = body
        self.shape = shape
        self.curr_time = curr_time
        self.start_time = start_time
        self.color = color
        self.size = size

        self.shape.delete_on_hit = delete_on_hit
        self.shape.idd = idd
        self.shape.ptype = ptype

    @beartype
    def update(self, dt: float) -> bool:
        self.curr_time -= dt
        if self.curr_time < 0.0:
            self.delete()
            return True
        return False

    def get_data(self):
        c = self.color
        return np.array([
            *self.body.pos, 0.5, *c[:-1], c[-1] * (self.curr_time / self.start_time), *self.size
        ]).flatten()

    def delete(self) -> None:
        MainPhysicSpace.simple_delete(self.body, self.shape)


class PhysicLightedParticle(PhysicParticle):
    __slots__ = ("light_source", "idd_source", "type_source")

    def __init__(self, idd, ptype, body, shape, curr_time,
                 start_time, color, size, delete_on_hit, *light_params):
        super().__init__(idd, ptype, body, shape, curr_time, start_time, color, size, delete_on_hit)
        self.idd_source, self.light_source = LightingManager.newSource(*light_params)
        self.type_source = light_params[0]

    def update(self, dt: float) -> bool:
        if not super().update(dt):
            self.light_source.posXY = self.body.position
            return False
        LightingManager.delete_source(self.type_source, self.idd_source)
        return True


class __ParticleManager:
    __doc__ = """
    Particle: [
        position:   np.ndarray[3],
        velocity:   np.ndarray[2],   
        gravity:    FLOAT32, 
        curr time:  float,  
        start time: float,
        base color: np.ndarray[4],
        size:       np.ndarray[2]
    ]
    
    Physic Particle: [
        body:       pymunk.Body,
        shape:      pymunk.Shape (Circle),
        curr_time:  float,
        start_time: float,
        base_color: np.ndarray[4],
        size:       np.ndarray[2],
    ]
    """

    particles: Dict[int, Dict] = {}
    free_ids = set(range(MAX_PARTICLES))

    vbo_id: int

    shaders = {
        0: "ParticlePolyShader",
    }

    def __init__(self):
        self.particles = {
            i: dict() for i in self.__class__.shaders.keys()
        }
        self.vbo_id = glGenBuffers(1)
        self.__setup_collision_handler()

    @staticmethod
    def __setup_collision_handler():
        handler2 = MainPhysicSpace.space.\
            add_wildcard_collision_handler(COLLISION_CATEGORIES['particle'])

        def particleCollisionHandlerPost(arbiter, space, _):
            if arbiter.is_first_contact:
                shape = arbiter.shapes[0]
                elasticity = shape.elasticity

                if shape.delete_on_hit:
                    ParticleManager.delete_physic_particle(shape, space)
                    return False
                elif elasticity > 0.0:
                    shape.body.velocity = \
                        Vec2d(shape.body.velocity[0] * arbiter.normal[0],
                              shape.body.velocity[1] * arbiter.normal[1]) * elasticity
            return True

        handler2.begin = particleCollisionHandlerPost

    @beartype
    def update(self, dt: float):
        for key in self.particles.keys():
            particles = self.particles[key]
            to_delete = set()

            for k, p in particles.items():
                if p.update(dt):
                    self.free_ids.add(k)
                    to_delete.add(k)

            for _ in range(len(to_delete)):
                del self.particles[key][to_delete.pop()]

    _T = Tuple[int, int]

    @beartype
    def create_simple(self,
                      ptype: int,
                      pos: Vec2d,
                      amount: _T,
                      speed: _T,
                      time: Tuple[float, float],
                      color: Tuple[float, float, float, float],
                      size_x: _T,
                      size_y: Union[_T, None],
                      angles: Tuple = (0, 360),
                      gravity: float = 0.0):

        rd = randint
        rf = randf
        base_color = np.array(color)
        angles_lenn = len(angles) // 2 - 1

        for _ in range(rd(*amount)):
            a = rd(0, angles_lenn)
            a = radians(rd(*angles[a * 2: a * 2 + 2]))

            vel = np.array(
                [v * rd(*speed) for v in (cos(a), sin(a))], dtype=FLOAT32
            )
            t = rf(*time)
            idd = self.new_id(ptype)
            sx = rd(*size_x)
            sy = rd(*size_y) if size_y else sx
            self.particles[ptype][idd] = Particle(
                np.array(pos, dtype=FLOAT32),
                vel,
                gravity,
                t,
                t,
                base_color,
                np.array([sx, sy], dtype=FLOAT32)
            )

    @beartype
    def create_physic(self,
                      ptype: int,
                      pos: Vec2d,
                      amount: _T,
                      speed: _T,
                      time: Tuple[float, float],
                      color: Tuple[float, float, float, float],
                      size_x: _T,
                      size_y: Union[_T, None],
                      angles: Tuple = (0, 360),
                      collide_with=('level', ),
                      delete_on_hit=False,
                      elasticity: float = 0.0):

        rd = randint
        rf = randf
        base_color = np.array(color)
        angles_lenn = len(angles) // 2 - 1

        for _ in range(rd(*amount)):
            a = rd(0, angles_lenn)
            a = radians(rd(*angles[a * 2: a * 2 + 2]))

            vel = Vec2d(
                cos(a), sin(a)
            ) * rd(*speed)

            t = rf(*time)
            idd = self.new_id(ptype)
            sx = rd(*size_x)
            sy = rd(*size_y) if size_y else sx

            body = makeBodyCircle(pos, 2, 'dynamic', mass=1.0)
            shape = makeShapeCircle(body, 4, friction=0,
                                    shape_filter=shapeFilter('particle', collide_with=collide_with))
            body.velocity = vel
            shape.elasticity = elasticity
            MainPhysicSpace.simple_add(body, shape)

            self.particles[ptype][idd] = PhysicParticle(
                idd,
                ptype,
                body,
                shape,
                t,
                t,
                base_color,
                np.array([sx, sy], dtype=FLOAT32),
                delete_on_hit
            )

    @beartype
    def create_physic_light(self,
                            ptype: int,
                            pos: Vec2d,
                            amount: _T,
                            speed: _T,
                            time: Tuple[float, float],
                            color: Tuple[float, float, float, float],
                            size_x: _T,
                            size_y: Union[_T, None],
                            light_params: Tuple,
                            angles: Tuple = (0, 360),
                            collide_with=('level',),
                            delete_on_hit=False,
                            elasticity: float = 0.0):

        rd = randint
        rf = randf
        base_color = np.array(color)
        angles_lenn = len(angles) // 2 - 1

        for _ in range(rd(*amount)):
            a = rd(0, angles_lenn)
            a = radians(rd(*angles[a * 2: a * 2 + 2]))

            vel = Vec2d(cos(a), sin(a)) * rd(*speed)

            t = rf(*time)
            idd = self.new_id(ptype)
            sx = rd(*size_x)
            sy = rd(*size_y) if size_y else sx

            body = makeBodyCircle(pos, 2, 'dynamic', mass=1.0)
            shape = makeShapeCircle(body, 4, friction=0,
                                    shape_filter=shapeFilter('particle', collide_with=collide_with))
            body.velocity = vel
            shape.elasticity = elasticity
            MainPhysicSpace.simple_add(body, shape)

            self.particles[ptype][idd] = PhysicLightedParticle(
                idd,
                ptype,
                body,
                shape,
                t,
                t,
                base_color,
                np.array([sx, sy], dtype=FLOAT32),
                delete_on_hit,
                *light_params
            )

    def new_id(self, shape):
        """If the is no free ids for Particle,
        then it returns last added Particle's id"""
        if self.free_ids:
            return self.free_ids.pop()
        return self.particles[shape].popitem()[0]

    def delete_physic_particle(self, shape, space):
        key = shape.idd
        ptype = shape.ptype

        if key in self.particles[ptype].keys():
            del self.particles[ptype][key]
            self.free_ids.add(key)
            space.remove(shape, shape.body)

    def render(self, camera):
        bindEBO(2)
        glDisable(GL_DEPTH_TEST)

        for key in self.particles.keys():
            particles = self.particles[key]
            if not particles:
                continue
            Shader = shaders[self.shaders[key]]
            Shader.use()

            data = np.array(
                [p.get_data() for p in particles.values()], dtype=FLOAT32
            ).flatten()
            self.__drawGL_from_data(data, camera, len(particles), Shader)

        bindEBO()
        glEnable(GL_DEPTH_TEST)

    def __drawGL_from_data(self, data, camera_, elements, shader):
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo_id)
        glBufferData(GL_ARRAY_BUFFER, data.nbytes, data, GL_STATIC_DRAW)

        mat = FullTransformMat(ZERO_FLOAT32, ZERO_FLOAT32, camera_.get_matrix(), ZERO_FLOAT32)
        shader.prepareDraw(transform=mat)

        glDrawElements(GL_POINTS, elements, GL_UNSIGNED_INT, None)


ParticleManager = __ParticleManager()
