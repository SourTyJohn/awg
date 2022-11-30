from OpenGL.GL import *

from core.Constants import TILE_SIZE, FLOAT32, TYPE_NUM,\
    TYPE_VEC, MAX_LIGHT_SOURCES, ZERO_FLOAT32
from core.math.linear import FullTransformMat
from core.rendering.PyOGL_utils import zFromLayer
from core.rendering.Shaders import shaders

from dataclasses import dataclass, field
from typing import Tuple, Dict, Union
import numpy as np
from beartype import beartype


LIGHT_COLOR_PRESETS = {
    'fire': (1.0, 0.3, 0.0, 0.0)
}

__all__ = [
    "__LightingManager",
]


@dataclass
class LightSource:
    __slots__ = ("color", "radius", "posXY", "posZ")

    color: field(default_factory=np.ndarray)
    radius: field(default_factory=FLOAT32)
    posXY: field(default_factory=np.ndarray)
    posZ: field(default_factory=FLOAT32)

    def __init__(self, pos, power, layer, color, brightness, trigger=None):
        self.color = np.array([*color, brightness], dtype=FLOAT32)
        self.radius = FLOAT32(power * TILE_SIZE)
        self.posXY = np.array(pos, dtype=FLOAT32)
        self.posZ = FLOAT32(zFromLayer(layer))

    def calculate_shadows(self, trigger):
        pass

    def __repr__(self):
        return f'LS {list(self.posXY)}'

    @beartype
    def update(self, dt: float):
        pass

    def get_data(self):
        return np.array(
            [*self.posXY, self.posZ, *self.color, self.radius]
        ).flatten()


class ExplosionLightSource(LightSource):
    __slots__ = ('curr_time', 'end_time', 'peak_time', )

    curr_time: field(default_factory=float)
    end_time: field(default_factory=float)
    peak_time: field(default_factory=float)

    def __init__(self, pos, power, layer, color, brightness, time, peak):
        super().__init__(pos, power, layer, color, brightness)
        assert peak < time, "Max time must be greater than peak time"
        self.curr_time = 0.0
        self.end_time = time
        self.peak_time = peak

    @beartype
    def update(self, dt: float):
        self.curr_time += dt
        if self.curr_time >= self.end_time:
            return True

    def get_data(self):
        crt, ndt, pkt = self.curr_time, self.end_time, self.peak_time
        if crt >= pkt:
            kff = 1.0 - (crt - pkt) / (ndt - pkt)
        else:
            kff = crt / pkt

        return np.array(
            [*self.posXY, self.posZ, *self.color[:-1], self.color[-1] * kff, self.radius * kff]
        ).flatten()


class __LightingManager:
    sources: Dict[int, Dict] = {}
    free_ids = set(range(MAX_LIGHT_SOURCES))

    vbo_id: int
    shaders = {
        0: "RoundLightShader",
    }
    do_render = True

    def __init__(self):
        self.sources = {
            i: dict() for i in self.__class__.shaders.keys()
        }
        self.vbo_id = glGenBuffers(1)
        self.frame_buffer = None

    @beartype
    def newSource(self, ltype: int, pos: Union[TYPE_VEC, Tuple], power: TYPE_NUM,
                  layer: int = 1, color: Tuple[float, float, float] = (0.1, 0.1, 0.1),
                  brightness: float = 0.8):

        if isinstance(color, str):
            assert color in LIGHT_COLOR_PRESETS.keys(),\
                KeyError(f'No such color preset. Chose from {LIGHT_COLOR_PRESETS.keys()}')

        source = LightSource(pos, power, layer, color, brightness)
        idd = self.new_id(ltype)
        self.sources[ltype][idd] = source
        return idd, source

    @beartype
    def newSource_explosion(self, ltype: int, pos: Union[TYPE_VEC, Tuple], power: TYPE_NUM,
                            time: float, peak_time: float,
                            layer: int = 1, color: Tuple[float, float, float] = (0.1, 0.1, 0.1),
                            brightness: float = 0.8):

        if isinstance(color, str):
            assert color in LIGHT_COLOR_PRESETS.keys(),\
                KeyError(f'No such color preset. Chose from {LIGHT_COLOR_PRESETS.keys()}')

        source = ExplosionLightSource(pos, power, layer, color, brightness, time, peak_time)
        idd = self.new_id(ltype)
        self.sources[ltype][idd] = source
        return source

    @beartype
    def new_id(self, ltype: int):
        """If the is no free ids for Source,
        then it returns last added Source's id"""
        if self.free_ids:
            return self.free_ids.pop()
        return self.sources[ltype].popitem()[0]

    def render(self, camera_):
        for key in self.sources.keys():
            if not (sources := self.sources[key]):
                continue
            Shader = shaders[self.shaders[key]]
            Shader.use()

            data = np.array(
                [p.get_data() for p in sources.values()], dtype=FLOAT32
            ).flatten()

            self.__drawGL_from_data(data, camera_, len(sources), Shader)

    def delete_source(self, ltype, idd):
        self.free_ids.add(idd)
        s = self.sources[ltype]
        if idd in s.keys():
            del s[idd]

    @beartype
    def update(self, dt: float):
        for key in self.sources.keys():
            to_delete = set()

            for idd, source in self.sources[key].items():
                if source.update(dt):
                    self.free_ids.add(idd)
                    to_delete.add(idd)

            for _ in range(len(to_delete)):
                del self.sources[key][to_delete.pop()]

    def __drawGL_from_data(self, data, camera_, elements, shader):
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo_id)
        glBufferData(GL_ARRAY_BUFFER, data.nbytes, data, GL_STATIC_DRAW)

        mat = FullTransformMat(ZERO_FLOAT32, ZERO_FLOAT32, camera_.get_matrix(), ZERO_FLOAT32)
        shader.prepareDraw(transform=mat)

        glDrawElements(GL_POINTS, elements, GL_UNSIGNED_INT, None)

    def bind_buffer(self):
        self.frame_buffer.bind()

    def clear(self):
        pass
