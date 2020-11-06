from OpenGL.GL import *
from OpenGL.GLU import *

from utils.files import get_shader_path


class BlankShader:
    def __init__(self):
        pass

    def use(self):
        print('BlankShader.use() warning !')


class Shader:
    def __init__(self, vertex_path: str, fragment_path: str):

        #  Reading shader code
        v = open(get_shader_path(vertex_path))
        vertx_code = v.read()
        v.close()

        f = open(get_shader_path(fragment_path))
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
