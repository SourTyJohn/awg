from OpenGL.GL import *
from utils.files import get_full_path
from utils.debug import dprint
import core.Constants as Const
from core.Constants import TYPE_VEC, TYPE_FLOAT, TYPE_INT
from beartype import beartype
from typing import Dict
import numpy as np

shaders: Dict[str, "Shader"] = {}

ActiveShader = None


class Shader:
    __doc__ = """
    Abstraction of compiled and linked .glsl files
    Each Shader class is a Singleton.
    To start rendering using this Shader call .use()
    Shader is a meta-class
    
    In .glsl shader files you can write after version define:
    #constant <constant type> <constant name>
    This line, while compiling, will be replaced with:
    <constant type> <constant name> = <constant value from Constants.py>
    You should you use this, instead of regular in-glsl define,
    if this constant are used in multiple shaders, 
    otherwise you you have to rewrite constant value in every shader separately
    """

    __instance = None

    def __init__(self, vertex_path: str, fragment_path: str, geometry_path: str = ''):
        #  Reading shader code
        vertx_code = loadGLSL(vertex_path)
        fragm_code = loadGLSL(fragment_path)
        gemtr_code = loadGLSL(geometry_path) if geometry_path else None

        #  Compiling shaders
        vertex = glCreateShader(GL_VERTEX_SHADER)
        self.compile_shader(vertex, vertx_code, vertex_path)

        fragment = glCreateShader(GL_FRAGMENT_SHADER)
        self.compile_shader(fragment, fragm_code, fragm_code)

        geometry = glCreateShader(GL_GEOMETRY_SHADER)
        self.compile_shader(geometry, gemtr_code, geometry_path)

        #  Creating program and attaching shaders
        self.program = glCreateProgram()
        glAttachShader(self.program, vertex)
        glAttachShader(self.program, fragment)
        if geometry_path:
            glAttachShader(self.program, geometry)
        glLinkProgram(self.program)

        if not glGetProgramiv(self.program, GL_LINK_STATUS):
            print(f'Shader Program error:')
            print(glGetProgramInfoLog(self.program))
            raise GLerror('Shader Program error')

        #  Cleaning up
        glDeleteShader(vertex)
        glDeleteShader(fragment)
        glDeleteShader(geometry)

        self.active_shader = None

        self.cached_uniform_locations = {}

    @staticmethod
    def compile_shader(gl_shader, code: str, path: str):
        if not path:
            return None

        glShaderSource(gl_shader, code)
        glCompileShader(gl_shader)

        if not glGetShaderiv(gl_shader, GL_COMPILE_STATUS):
            print(f'Shader compilation error in: {path}')
            print(glGetShaderInfoLog(gl_shader))

    def __new__(cls, *args, **kwargs):
        cls.__instance = super(Shader, cls).__new__(cls)
        return cls.__instance

    def universal_use(self):
        global ActiveShader
        if ActiveShader != self.program:
            glUseProgram(self.program)

    def use(self):
        self.universal_use()

        glEnableVertexAttribArray(0)
        glEnableVertexAttribArray(1)
        glEnableVertexAttribArray(2)

    def prepareDraw(self, **kw):
        stride = 36
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
        glVertexAttribPointer(1, 4, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(12))
        glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(28))
        return self.program

    # PASS UNIFORMS TO SHADER
    def get_uniform_location(self, name_: str):
        loc = self.cached_uniform_locations.get(name_)
        if loc is None:
            loc = glGetUniformLocation(self.program, name_)
            self.cached_uniform_locations[name_] = loc
        return loc

    @beartype
    def passMat4(self, name_: str, value: np.ndarray) -> None:
        loc = self.get_uniform_location(name_)
        glUniformMatrix4fv(loc, 1, GL_FALSE, value)

    @beartype
    def passFloat(self, name_: str, value: TYPE_FLOAT) -> None:
        loc = self.get_uniform_location(name_)
        glUniform1f(loc, value)

    @beartype
    def passInteger(self, name_: str, value: TYPE_INT):
        loc = self.get_uniform_location(name_)
        glUniform1i(loc, value)

    @beartype
    def passTexture(self, name_: str, value) -> None:
        loc = self.get_uniform_location(name_)
        glUniform1i(loc, value)

    @beartype
    def passVec2f(self, name_: str, value) -> None:
        loc = self.get_uniform_location(name_)
        glUniform2f(loc, *value)

    @beartype
    def passVec4f(self, name_: str, value: TYPE_VEC) -> None:
        loc = self.get_uniform_location(name_)
        glUniform4f(loc, *value)


# DEFAULT
class DefaultShader(Shader):
    """Basic Shader with no effects. Can use colors from VBO"""

    __instance = None

    def __init__(self):
        super().__init__('default_vert.glsl', 'default_frag.glsl')

    def prepareDraw(self, **kw):
        super().prepareDraw()
        self.passMat4('Transform', kw['transform'])


class DefaultInstancedShader(Shader):
    __instance = None

    def __init__(self):
        super().__init__('default_vert.glsl', 'default_frag.glsl')

    def prepareDraw(self, **kw):
        super().prepareDraw()


class BackgroundShader(Shader):
    """Shader for fancy :) gradient background drawing"""

    __instance = None

    def __init__(self):
        super().__init__('back_vert.glsl', 'back_frag.glsl')

    def prepareDraw(self, **kw):
        super().prepareDraw(**kw)

        self.passMat4('Transform', kw['transform'])
        self.passFloat('cameraPos', kw['camera'].pos[1] / Const.WINDOW_SIZE[1])


# LIGHTING
class RoundLightShader(Shader):
    def __init__(self):
        super().__init__('light_round_vert.glsl',
                         'light_round_frag.glsl',
                         'light_round_geo.glsl')

    def prepareDraw(self, **kw):
        stride = 32

        # ATTRIBUTES POINTERS
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)

        glVertexAttribPointer(1, 4, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(12))
        glEnableVertexAttribArray(1)

        glVertexAttribPointer(2, 1, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(28))
        glEnableVertexAttribArray(2)

        self.passMat4('Transform', kw['transform'])


# SCREENS AND GUIS
class ScreenShaderGame(Shader):
    """Post-effect shader"""

    __instance = None

    def __init__(self):
        super().__init__('screen_vert.glsl', 'screen_frag.glsl')

    def prepareDraw(self, **kw):
        super().prepareDraw(**kw)
        self.passTexture("lightMap", 1)
        self.passTexture("depthMap", 2)
        self.passFloat('brightness', Const.BRIGHTNESS)


class ScreenShaderMenu(Shader):
    def __init__(self):
        super().__init__('screen_vert.glsl', 'screen_nolight_frag.glsl')

    def prepareDraw(self, **kw):
        super().prepareDraw(**kw)
        self.passFloat('brightness', Const.BRIGHTNESS)


class GUIShader(Shader):
    def __init__(self):
        super().__init__('gui_vert.glsl', 'gui_frag.glsl')

    def prepareDraw(self, **kw):
        super().prepareDraw(**kw)
        self.passMat4('Transform', kw['transform'])


# PARTICLES AND EFFECTS
class StraightLineShader(Shader):
    def __init__(self):
        super().__init__('straight_line_vert.glsl',
                         'straight_line_frag.glsl',
                         'straight_line_geo.glsl')

    def prepareDraw(self, **kw):
        shader = self.program

        # ATTRIBUTES POINTERS
        glGetAttribLocation(shader, "position")
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 12, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)
        self.passMat4('Transform', kw['transform'])
        self.passVec4f('LineColor', kw['color'])
        self.passInteger('Thickness', kw['width'])


class ParticlePolyShader(Shader):
    def __init__(self):
        super().__init__('particle_vert.glsl',
                         'particle_frag.glsl',
                         'particle_poly_geo.glsl')

    def prepareDraw(self, **kw):
        shader = self.program
        stride = 36

        # ATTRIBUTES POINTERS
        glGetAttribLocation(shader, "position")
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)

        glGetAttribLocation(shader, "color")
        glVertexAttribPointer(1, 4, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(12))
        glEnableVertexAttribArray(1)

        glGetAttribLocation(shader, "size")
        glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(28))
        glEnableVertexAttribArray(2)

        self.passMat4('Transform', kw['transform'])


def init():
    print('\n-- Shaders initialization')

    for cls in Shader.__subclasses__():
        shaders[cls.__name__] = cls()
        dprint(f'Inited: {cls.__name__}')

    dprint('-- Done.\n')


def loadGLSL(path):
    with open(get_full_path(path, file_type='shd')) as file:
        code = file.readlines()
        for i, line in enumerate(code):
            if line[0] != '#':
                break

            tags = line.split()
            if tags[0] == '#constant':
                value = getattr(Const, tags[2])
                if type(value) in {set, list, tuple, np.ndarray}:
                    code[i] = f'const {tags[1]} {tags[2]} = vec{len(value)}({str(list(value))[1:-1]});\n'
                else:
                    code[i] = f'const {tags[1]} {tags[2]} = {value};\n'

    return ''.join(code)
