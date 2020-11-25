from OpenGL.GL import *
from OpenGL.GLU import *

from utils.files import get_full_path


class BlankShader:
    def __init__(self):
        pass

    @staticmethod
    def use():
        print('BlankShader.use() warning !')


class Shader:
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

    def use(self):
        glUseProgram(self.program)


def create_shader(v_path, f_path):
    return Shader(v_path, f_path)
