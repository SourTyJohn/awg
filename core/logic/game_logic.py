# from utils.files import load_map
from core.rendering.PyOGL import *
from core.rendering.Particles import ParticleManager


class GameContext:
    # TODO TILES -> CHUNK

    def __init__(self):
        self.__groups_DepthWrite = {
            "MainLevelGeometry":    RenderGroup_Materials(),
            "BackgroundWallsO":     RenderGroup_Instanced(),
            "BackgroundColor":      RenderGroup(shader="BackgroundShader"),
            "BackgroundImages":     RenderGroup_Instanced(),
            "BackgroundWallsT":     RenderGroup_Instanced(),  # transparent
        }

        self.__groups_NoDepthWrite = {
            "GameObjectsInstanced":         RenderGroup_Instanced(),
            "GameObjectsSingle":            RenderGroup()
        }

        self.do_DepthTest = True
        self.screen_shader = Shaders.shaders['ScreenShaderGame']
        self._to_update = {}

    def _add(self, obj, group_name, group_type):
        if group_name is None:
            group_name = obj.target_group

        assert group_name in group_type.keys(), \
            KeyError(f"No such group: {group_name}, Groups:{list(group_type.keys())}")

        group_type[group_name].add(obj)

        if hasattr(obj, "update"):
            self._to_update[obj.UID] = obj

        return obj

    def add_single_game_obj(self, obj, group: str = None):
        return self._add(obj, group, self.__groups_NoDepthWrite)

    def add_single_level_obj(self, obj, group: str = None):
        return self._add(obj, group, self.__groups_DepthWrite)

    def update(self, dt: float):
        pass

        for uid, obj in self._to_update.items():
            obj.update(dt)

    def render_I_pass(self):
        glEnable(GL_DEPTH_TEST)
        glDepthMask(GL_TRUE)

        for key, group in self.__groups_DepthWrite.items():
            group.draw_all()

        glDepthMask(GL_FALSE)

        for key, group in self.__groups_NoDepthWrite.items():
            group.draw_all()

    @staticmethod
    def render_II_pass():
        # DEFAULT FRAME BUFFER
        renderLights(camera)
        clearDisplay()
        ParticleManager.render(camera)

    def render(self, dt: float):
        preRender()

        self.render_I_pass()
        self.render_II_pass()

        postRender(self.screen_shader)

    def get_geometry(self):
        pass

    def delete_object(self, obj):
        pass

    def clear(self):
        pass


def loadMap():
    pass
