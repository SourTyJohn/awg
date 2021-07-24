from OpenGL.GL import *
from utils.files import get_full_path
import core.Constants as Const
from beartype import beartype
import numpy as np

shaders = {}


def shader_load(path):
    with open(get_full_path(path, file_type='shd')) as file:
        code = file.readlines()
        for i, line in enumerate(code):
            if line[0] != '#':
                break

            tags = line.split()
            if tags[0] == '#constant':
                code[i] = f'{tags[1]} {tags[2]} = {getattr(Const, tags[2])};\n'

    return ''.join(code)


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

    def __init__(self, vertex_path: str, fragment_path: str):
        #  Reading shader code
        vertx_code = shader_load(vertex_path)
        fragm_code = shader_load(fragment_path)

        #  Compiling shaders
        vertex = glCreateShader(GL_VERTEX_SHADER)
        glShaderSource(vertex, vertx_code)
        glCompileShader(vertex)

        if not glGetShaderiv(vertex, GL_COMPILE_STATUS):
            print(f'vertex shader error in: {vertex_path}')
            print(glGetShaderInfoLog(vertex))

        fragment = glCreateShader(GL_FRAGMENT_SHADER)
        glShaderSource(fragment, fragm_code)
        glCompileShader(fragment)

        if not glGetShaderiv(fragment, GL_COMPILE_STATUS):
            print(f'fragment shader error in: {fragment_path}')
            print(glGetShaderInfoLog(fragment))

        #  Creating program and attaching shaders
        self.program = glCreateProgram()
        glAttachShader(self.program, vertex)
        glAttachShader(self.program, fragment)
        glLinkProgram(self.program)

        if not glGetProgramiv(self.program, GL_LINK_STATUS):
            print(f'Shader Program error:')
            print(glGetProgramInfoLog(self.program))
            raise GLerror('Shader Program error')

        #  Cleaning up
        glDeleteShader(vertex)
        glDeleteShader(fragment)

    def __new__(cls, *args, **kwargs):
        cls.__instance = super(Shader, cls).__new__(cls)
        return cls.__instance

    def use(self):
        glUseProgram(self.program)

    def prepareDraw(self, pos, **kw):
        stride = 36
        shader = self.program

        # ATTRIBUTES POINTERS
        glGetAttribLocation(shader, "position")
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)

        glGetAttribLocation(shader, "color")
        glVertexAttribPointer(1, 4, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(12))
        glEnableVertexAttribArray(1)

        glGetAttribLocation(shader, "InTexCoords")
        glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(28))
        glEnableVertexAttribArray(2)

        return shader

    # PASS UNIFORMS TO SHADER
    @beartype
    def passMat4(self, name_: str, value: np.ndarray) -> None:
        loc = glGetUniformLocation(self.program, name_)
        glUniformMatrix4fv(loc, 1, GL_FALSE, value)

    @beartype
    def passFloat(self, name_: str, value) -> None:
        loc = glGetUniformLocation(self.program, name_)
        glUniform1f(loc, value)

    @beartype
    def passTexture(self, name_: str, value) -> None:
        frame = glGetUniformLocation(self.program, name_)
        glUniform1i(frame, value)

    @beartype
    def passVec2(self, name_: str, value) -> None:
        loc = glGetUniformLocation(self.program, name_)
        glUniform2f(loc, *value)


class DefaultShader(Shader):
    """Basic Shader with no effects. Can use colors from VBO"""

    __instance = None

    def __init__(self):
        super().__init__('default_vert.glsl', 'default_frag.glsl')

    def prepareDraw(self, pos, **kw):
        super().prepareDraw(pos, **kw)
        self.passMat4('Transform', kw['transform'])


# SHADERS
class BackgroundShader(Shader):
    """Shader for fancy gradient background drawing"""

    __instance = None

    def __init__(self):
        super().__init__('back_vert.glsl', 'back_frag.glsl')

    def prepareDraw(self, pos, **kw):
        super().prepareDraw(pos, **kw)

        self.passMat4('Transform', kw['transform'])
        self.passFloat('cameraPos', kw['camera'].pos[1] / Const.WINDOW_SIZE[1])


# light shaders
class RoundLightShader(Shader):
    def __init__(self):
        super().__init__('light_round_vert.glsl', 'light_round_frag.glsl')

    def prepareDraw(self, pos, **kw):
        super().prepareDraw(pos, **kw)
        self.passMat4('Transform', kw['transform'])


class RoundFlatLightShader(Shader):
    def __init__(self):
        super().__init__('light_round_vert.glsl', 'light_fire_frag.glsl')

    def prepareDraw(self, pos, **kw):
        super().prepareDraw(pos, **kw)
        self.passMat4('Transform', kw['transform'])
        self.passFloat('RandK', kw['noise'])
#


class ScreenShaderGame(Shader):
    """Post-effect shader"""

    __instance = None

    def __init__(self):
        super().__init__('screen_vert.glsl', 'screen_frag.glsl')

    def prepareDraw(self, pos, **kw):
        super().prepareDraw(pos, **kw)
        self.passTexture("lightMap", 1)
        self.passTexture("depthMap", 2)
        self.passFloat('brightness', Const.BRIGHTNESS)


class ScreenShaderMenu(Shader):
    def __init__(self):
        super().__init__('screen_vert.glsl', 'screen_nolight_frag.glsl')

    def prepareDraw(self, pos, **kw):
        super().prepareDraw(pos, **kw)
        self.passFloat('brightness', Const.BRIGHTNESS)


class GUIShader(Shader):
    def __init__(self):
        super().__init__('gui_vert.glsl', 'gui_frag.glsl')

    def prepareDraw(self, pos, **kw):
        super().prepareDraw(pos, **kw)
        self.passMat4('Transform', kw['transform'])
#


def init():
    print('\n-- Shaders initialization')

    for cls in Shader.__subclasses__():
        shaders[cls.__name__] = cls()
        print(f'Inited: {cls.__name__}')

    print('-- Done.\n')
