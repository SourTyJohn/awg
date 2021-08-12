from core.rendering.PyOGL import bindEBO, frameBuffer
from core.rendering.Shaders import shaders
from core.Constants import FLOAT32, ZERO_FLOAT32
from core.math.linear import FullTransformMat

from math import sin, cos, radians
from random import randint
from beartype import beartype
import numpy as np
from typing import Dict, Tuple, Union
from pymunk import Vec2d

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


class __ParticleManager:
    __doc__ = """
    Particle: [
        position:   np.ndarray[3],
        velocity:   np.ndarray[2],   
        gravity:    FLOAT32, 
        curr time:  float,  
        start time: float,
        base color: np.ndarray[4]
    ]
    """
    particles: Dict[int, Dict] = {}
    free_ids = set(range(2 ** 10))
    vbo_id: int

    shaders = {
        0: shaders["ParticlePolyShader"],
    }

    def __init__(self):
        self.particles = {i: dict() for i in self.__class__.shaders.keys()}
        self.vbo_id = glGenBuffers(1)

    def update(self, dt):
        for key in self.particles.keys():
            particles = self.particles[key]
            to_delete = set()

            for k, p in particles.items():
                p[0] += p[1] * dt
                p[1][1] -= p[2] * dt
                p[3] -= dt
                if p[3] <= 0.0:
                    self.free_ids.add(k)
                    to_delete.add(k)

            for _ in range(len(to_delete)):
                del self.particles[key][to_delete.pop()]

    _T = Tuple[int, int]

    @beartype
    def create(self,
               shape: int,
               pos: Vec2d,
               amount: _T,
               speed: _T,
               time: _T,
               color: Tuple[float, float, float, float],
               size_x: _T,
               size_y: Union[_T, None],
               angle: _T = (0, 360),
               gravity: float = 0.0):

        rd = randint
        base_color = np.array(color)

        for _ in range(rd(*amount)):
            a = radians(rd(*angle))
            vel = np.array(
                [v * rd(*speed) for v in (cos(a), sin(a))], dtype=FLOAT32
            )
            t = rd(*time)
            idd = self.new_id(shape)
            sx = rd(*size_x)
            sy = rd(*size_y) if size_y else sx
            self.particles[shape][idd] = [
                np.array(pos, dtype=FLOAT32),
                vel,
                gravity,
                t,
                t,
                base_color,
                np.array([sx, sy], dtype=FLOAT32)
            ]

    def new_id(self, shape):
        """If the is no free ids for Particle,
        then it returns last added Particle's id"""
        if self.free_ids:
            return self.free_ids.pop()
        return self.particles[shape].popitem()[0]

    def draw(self, hero_pos, camera):
        bindEBO(2)
        glDisable(GL_DEPTH_TEST)

        hero_pos = np.array(hero_pos, dtype=FLOAT32)

        for key in self.particles.keys():
            particles = self.particles[key]
            if not particles:
                continue
            Shader = self.shaders[key]
            Shader.use()

            points = np.array(
                [
                    np.array([
                        *(p[0] - hero_pos), 0.5,                 # position
                        *p[-2][:-1], p[-2][-1] * (p[3] / p[4]),  # color
                        *p[-1]                                   # size
                    ]).flatten()
                    for p in particles.values()]
            ).flatten()
            data = np.array(points, dtype=FLOAT32)

            # GL part
            glBindBuffer(GL_ARRAY_BUFFER, self.vbo_id)
            glBufferData(GL_ARRAY_BUFFER, data.nbytes, data, GL_STATIC_DRAW)

            x_, y_ = hero_pos
            mat = FullTransformMat(x_, y_, camera.get_matrix(), ZERO_FLOAT32)
            Shader.prepareDraw(hero_pos, transform=mat, fbuffer=frameBuffer)

            glDrawElements(GL_POINTS, len(particles), GL_UNSIGNED_INT, None)

        bindEBO()
        glEnable(GL_DEPTH_TEST)


ParticleManager = __ParticleManager()
