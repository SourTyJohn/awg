from OpenGL.GL import *

from utils.files import get_full_path

from core.Math import Matrix as Mat


shaders = {}


class Shader:
    """Abstraction of compiled and linked .glsl files
    Each Shader class is a Singleton.
    To start rendering using this Shader call .use()
    Shader class can't be used on it's own, use only child-classes"""

    __instance = None

    def __init__(self, vertex_path: str, fragment_path: str):

        #  Reading shader code
        v = open(get_full_path(vertex_path, file_type='shd'))
        vertx_code = v.read()
        v.close()

        f = open(get_full_path(fragment_path, file_type='shd'))
        fragm_code = f.read()
        f.close()

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
            print(f'shader program error while creating')
            print(glGetProgramInfoLog(self.program))

        glDeleteShader(vertex)
        glDeleteShader(fragment)

    def __new__(cls, *args, **kwargs):
        cls.__instance = super(Shader, cls).__new__(cls)
        return cls.__instance

    def p(self):
        return self.program

    def use(self):
        glUseProgram(self.program)

    def draw(self, pos, **kwargs):
        pass


class DefaultShader(Shader):
    """Basic Shader with no effects. Can use colors from VBO"""

    __instance = None
    __name__ = 'default'

    def __init__(self):
        super().__init__('default_vert.glsl', 'default_frag.glsl')

    def draw(self, pos, **kwargs):
        shader = self.p()

        # attribute pointers
        glGetAttribLocation(shader, 'position')
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 32, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)

        glGetAttribLocation(shader, 'color')
        glVertexAttribPointer(1, 4, GL_FLOAT, GL_FALSE, 32, ctypes.c_void_p(8))
        glEnableVertexAttribArray(1)

        glGetAttribLocation(shader, "InTexCoords")
        glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, 32, ctypes.c_void_p(24))
        glEnableVertexAttribArray(2)

        # translate matrix
        translateM = Mat.translate(*pos)
        loc = glGetUniformLocation(shader, "Translate")
        glUniformMatrix4fv(loc, 1, GL_FALSE, translateM)


class BackgroundShader(Shader):
    """Shader for fancy gradient background drawing"""

    __instance = None
    __name__ = 'background'

    def __init__(self):
        super().__init__('back_vert.glsl', 'back_frag.glsl')

    def draw(self, pos, **kwargs):
        shader = self.p()

        # attribute pointers
        glGetAttribLocation(shader, 'position')
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 24, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)

        glGetAttribLocation(shader, 'color')
        glVertexAttribPointer(1, 4, GL_FLOAT, GL_FALSE, 24, ctypes.c_void_p(8))
        glEnableVertexAttribArray(1)

        # translate matrix
        translateM = Mat.translate(*pos)
        loc = glGetUniformLocation(shader, "Translate")
        glUniformMatrix4fv(loc, 1, GL_FALSE, translateM)

        cameraPos = kwargs['camera'].getPos()[1]
        loc = glGetUniformLocation(shader, "cameraPos")
        glUniform1f(loc, cameraPos)


def init():
    print('\n-- Shaders initialization')

    for cls in Shader.__subclasses__():
        shaders[cls.__name__] = cls()
        print(f'Inited: {cls.__name__}')

    print('-- Done.\n')
