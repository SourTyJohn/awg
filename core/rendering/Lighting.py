from core.Constants import FLOAT32, MAX_LIGHT_SOURCES, INT64, MAX_TEXTURES_BIND
from core.math.linear import FullTransformMat
from core.rendering.PyOGL_utils import zFromLayer, bufferize, drawDataLightSource
from core.rendering.Shaders import shaders

from dataclasses import dataclass, field
from typing import Dict, List, Union
import numpy as np
from beartype import beartype


LIGHT_COLOR_PRESETS = {
    'fire': (1.0, 0.3, 0.0)
}

__all__ = [
    "__LightingManager",
]


@dataclass
class LightSource:
    __slots__ = ("color", "size", "posXY", "posZ", "z_rotation", "visible")

    color: field(default_factory=np.ndarray)
    size: field(default_factory=FLOAT32)
    posXY: field(default_factory=np.ndarray)
    posZ: field(default_factory=FLOAT32)

    z_rotation: field(default_factory=FLOAT32)
    shadow_mask_key: field(default_factory=INT64)

    visible: field(default_factory=bool)

    @beartype
    def __init__(
            self,
            pos: Union[List, tuple, np.ndarray],
            size: Union[float, List, np.ndarray],
            layer: int,
            color: Union[str, List, np.ndarray, tuple],
            brightness: float,
            z_rotation: float = 0.0
    ):
        if type(color) == str:
            self.color = np.array([*LIGHT_COLOR_PRESETS[color], brightness], dtype=FLOAT32)
        else:
            self.color = np.array([*color, brightness], dtype=FLOAT32)

        if type(size) == float:
            self.size = np.array([size, size], dtype=FLOAT32)
        else:
            self.size = np.array([*size], dtype=FLOAT32)

        self.posXY = np.array(pos, dtype=FLOAT32)
        self.posZ = FLOAT32(zFromLayer(layer))
        self.z_rotation = FLOAT32(z_rotation)
        self.visible = True

    def __repr__(self):
        return f'LS {list(self.posXY)}'

    def calculate_shadows(self):
        pass

    @beartype
    def update(self, dt: float):
        pass

    def get_transform(self, camera):
        return FullTransformMat(*self.posXY, camera.get_matrix(), self.z_rotation)


class ExplosionLightSource(LightSource):
    __slots__ = ('curr_time', 'end_time', 'peak_time', )

    curr_time: field(default_factory=float)
    end_time: field(default_factory=float)
    peak_time: field(default_factory=float)

    def __init__(self, pos, power, layer, color, brightness, time, peak):
        super().__init__(pos, power, layer, color, brightness)
        assert peak < time, "Max time must be greater or equal to peak time"
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
    sources: Dict[str, Dict] = {}

    def __init__(self, shader="LightSourceShader"):
        self.sources: Dict[ str, Dict[int, LightSource] ] = {}
        self.vbo: int = bufferize( drawDataLightSource() )
        self.shader = shaders[shader]
        self.free_ids = set(range(MAX_LIGHT_SOURCES))
        self.do_render = True

        self.changed = True
        self.groups = []

    @beartype
    def newSource(self, texture: str, s_type=0, **kwargs):
        if s_type == 0:
            source = LightSource(**kwargs)
        else:
            source = ExplosionLightSource(**kwargs)

        idd = self.new_id()
        if texture in self.sources.keys():
            self.sources[texture][idd] = source
        else:
            self.sources[texture] = {idd: source, }

        self.changed = True
        return idd, source

    def new_id(self):
        return self.free_ids.pop()

    def generate_groups(self) -> List[ Dict ]:
        """If new LightSource is added"""

        if self.changed:
            self.changed = False
            self.groups = []

            sources_all = self.sources
            group_n = 0
            for tex, sources in sources_all.items():

                while sources:
                    self.groups.append({"texture": tex, "sources": []})
                    limit = min(MAX_TEXTURES_BIND - 1, len(sources))

                    for _ in range(limit):
                        _, source = sources.popitem()
                        self.groups[group_n]["sources"].append(source)
                    group_n += 1

        return self.groups

    def delete_source(self, texture, idd):
        self.free_ids.add(idd)
        s = self.sources[texture]
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

    def clear(self):
        pass
