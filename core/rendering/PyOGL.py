import pygame
from OpenGL.GL import *
import numpy as np

from core.Constants import WINDOW_RESOLUTION, TEXTURE_PACK, DEFAULT_FOV_W,\
    DEFAULT_FOV_H, FULL_SCREEN, DEBUG, DEFAULT_SCALE
from utils.files import load_image

import core.Math.Matrix as Mat
from core.Math.DataTypes import Rect4f

# from pympler.asizeof import asizeof


import core.rendering.Shaders as Shaders

# background color
clear_color = (0.0, 0.0, 0.0, 0.0)


class Camera:
    """Singleton that stores camera's position and fov.
    In game usually focused on hero"""

    ortho_params: np.array
    __instance = None  # Camera object is Singleton

    def __init__(self):
        #  Camera params. np.array([left, right, bottom, top], dtype=int64)
        self.ortho_params = None

        #  Field of view
        self.fov = 1  # scale
        self.fovW = DEFAULT_FOV_W  # field half width
        self.fovH = DEFAULT_FOV_H  # filed half height

    def __new__(cls, *args, **kwargs):
        if cls.__instance:
            del cls.__instance
        cls.__instance = super(Camera, cls).__new__(cls)
        return cls.__instance

    def __getitem__(self, item):
        return self.ortho_params[item]

    def setFov(self, fov):
        if fov != self.fov:
            self.fov = fov
            self.fovW = (WINDOW_RESOLUTION[0] * self.fov) // 2
            self.fovH = (WINDOW_RESOLUTION[1] * self.fov) // 2

    def getRect(self):
        # returns Rect4f objects representing field of camera view
        o = self.ortho_params
        return Rect4f(o[0], o[2], o[1] - o[0], o[3] - o[2])

    def getPos(self):
        return np.array([(self[0] + self[1]) // 2, (self[2] + self[3]) // 2], dtype=np.int32)

    def setField(self, rect):
        x_, y, w, h = rect[0], rect[1], rect[2] / 2, rect[3] / 2
        self.ortho_params = np.array([x_ - w, x_ + w, y - h, y + h], dtype='int64')

    def getMatrix(self):
        # applying field of view. Called only in draw_begin()
        return Mat.ortho(*self.ortho_params)

    def focusTo(self, x_v, y_v, soft=True):
        if soft:
            # camera smoothly moving to (x_v, y_x) point
            past_pos = self.getPos()
            d_x, d_y = past_pos[0] - x_v, past_pos[1] - y_v
            x_v, y_v = past_pos[0] - d_x * 0.2, past_pos[1] - d_y * 0.2

        self.ortho_params = np.array(
            [x_v - self.fovW, x_v + self.fovW, y_v - self.fovH, y_v + self.fovH],
            dtype='int64'
        )


camera: Camera


def init_display(size=WINDOW_RESOLUTION):
    global camera

    # Display flags
    flags = pygame.OPENGL | pygame.DOUBLEBUF | pygame.HWSURFACE | pygame.SRCALPHA

    if FULL_SCREEN:
        flags |= pygame.FULLSCREEN
    pygame.display.set_mode(size, flags=flags)

    #
    clear_display()

    # Modes
    glEnable(GL_TEXTURE_2D)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glEnable(GL_BLEND)

    # Camera singleton object
    camera = Camera()

    #  Initialize shaders
    Shaders.init()

    # Setting clear color
    glClearColor(*clear_color)

    # Order of vertexes when drawing
    indices = np.array([0, 1, 2, 2, 3, 0], dtype=np.uint32)
    EBO = glGenBuffers(1)
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, EBO)
    glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices, GL_STATIC_DRAW)


def clear_display():
    # fully clearing display
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)


class GLObjectGroupRender(pygame.sprite.Group):
    __slots__ = ('do_draw', 'name', 'shader')
    """Container of GlObjects
    Can be named for debug output
    
    shader - Shader object from rendering.Shaders.py
    To __init__ pass only key of Shader, not Shader
    This shader will be used for drawing objects from this group
    """

    def __init__(self, *args, g_name='no-name', do_draw=True, shader='DefaultShader'):
        super().__init__(*args)
        self.do_draw = do_draw
        self.name = g_name

        if shader not in Shaders.shaders.keys():
            raise KeyError(f'There is no Shader with key: {shader}.'
                           f'\nCheck Shader initialization in DEBUG output')
        self.shader = shader

    def __repr__(self):
        #  Memory: {asizeof(self)}
        return f'<GLObjectGroupRender({len(self.sprites())}) {self.name}>'

    """drawing all of this group objects"""
    def draw_all(self, shader_load):
        if not self.do_draw:
            return

        shader = Shaders.shaders[self.shader]
        if shader_load:
            # PREPARING SHADER USAGE
            # calculating and binding matrixes of scale and camera
            scaleM = Mat.scale(DEFAULT_SCALE, DEFAULT_SCALE)
            orthoM = camera.getMatrix()

            # getting current shader class from Shaders.py and it's GL ShaderProgram
            shader.use()
            prg = shader.p()

            # pass to shader scale and camera params
            loc = glGetUniformLocation(prg, "Scale")
            glUniformMatrix4fv(loc, 1, GL_FALSE, scaleM)

            loc = glGetUniformLocation(prg, "Ortho")
            glUniformMatrix4fv(loc, 1, GL_FALSE, orthoM)

        # DRAWING
        for obj in self.sprites():
            obj.draw(shader)

    """Clearing storage"""
    def empty(self):
        super().empty()

    """Deleting all of group.sprites()"""
    def delete_all(self):

        for obj in self.sprites():
            obj.delete()

        self.empty()


class GlTexture:
    __slots__ = ('size', 'key', 'repeat', 'name')

    def __init__(self, image, tex_name, repeat=False):
        self.size = image.get_size()  # units
        self.key = make_GL2D_texture(image, *self.size, repeat=repeat)
        self.repeat = repeat
        self.name = tex_name.replace('.png', '')

        if DEBUG:
            print(self)

    def __repr__(self):
        return f'<GLTexture[{self.key}] \t size: {self.size[0]}x{self.size[1]}px. \t name: "{self.name}">'

    @classmethod
    def load_image(cls, image_name, repeat=False):
        code, texture = load_image(image_name, TEXTURE_PACK)

        if not code:
            pass
            # print(f'texture: {image_name} loading success')
        else:
            print(f'texture: {image_name} error -{code}')

        return GlTexture(texture, image_name, repeat)

    @classmethod  # Генерация текста по готовому объекту шрифта
    def load_text(cls, text, color, font=None, font_settings=None):
        if len(color) == 3:
            color = (color[0], color[1], color[2], 255)

        """Средствами pygame генерируем текстуру с текстом"""
        if font_settings:
            font = pygame.font.SysFont(*font_settings)

        texture = font.render(text, False, color, (0, 0, 0, 255)).convert_alpha()

        w, h = texture.get_size()

        """Переносим текст на новую поверхность и работаем с ней"""
        tmp = pygame.Surface((w, h), flags=pygame.SRCALPHA)
        tmp.blit(texture, (0, 0))
        tmp.set_colorkey((0, 0, 0, 255))
        tmp.set_alpha(color[3])
        texture = tmp.convert_alpha(tmp)

        return GlTexture(texture, f'text:{text}')

    def makeDrawData(self, color=(1.0, 1.0, 1.0, 1.0)):
        """Make draw data with size of this texture
        Usually GlObjects have their own drawData, but you can calculate drawData,
        which will perfect for this texture"""
        w_o, h_o = self.size[0] / 2, self.size[1] / 2

        data = np.array([
            # obj cords   |color     |tex cords
            -w_o, -h_o,   *color,     0.0, 1.0,
            +w_o, -h_o,   *color,     1.0, 1.0,
            +w_o, +h_o,   *color,     1.0, 0.0,
            -w_o, +h_o,   *color,     0.0, 0.0

        ], dtype=np.float32)

        return data

    def draw(self, pos, vbo, shader, z_rotation=0):
        """pos - where to draw
        vbo - key of VertexBufferObject in memory
        shader - currently active shader program"""

        # bind VBO
        glBindBuffer(GL_ARRAY_BUFFER, vbo)

        # drawing using Shader
        shader.draw(pos, rotation=z_rotation, camera=camera)

        # drawing
        glBindTexture(GL_TEXTURE_2D, self.key)
        glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None)

    """Удаление текстуры из памяти"""
    def delete(self):
        glDeleteTextures(1, [self.key, ])
        del self


class Sprite(pygame.sprite.Sprite):
    rect: Rect4f


class GLObjectBase(Sprite):
    __slots__ = ('rect', 'tex_offset', 'rotation', 'color', 'visible', 'drawData', 'vbo')
    """Base render object. Provides drawing given texture:GLTexture within given rect:Rect4f
    For :args info check in __init__"""

    TEXTURES: [GlTexture, ] = None
    texture = 0

    size = None

    color: np.array
    drawData: np.array
    vbo: int

    def __init__(self, group, rect: list, rotation=1, tex_offset=(0, 0), color=None, no_vbo=False):
        """If no group provided, than this object won't be rendered unless
        it is part of GLObjectComposite"""
        super().__init__(group) if group is not None else super().__init__()

        # in this rect stored position rect[:2] and size of sprite rect[2:]
        self.rect = Rect4f(*rect)

        # Offset of a texture on this object
        self.tex_offset = np.array(tex_offset, dtype=np.float32)

        # additional color over texture
        if color is None:
            color = [1, 1, 1, 1]
        self.color = np.array(color, dtype=np.float32)

        # if False object wont be rendered
        self.visible = True

        #  -1 for left   1 for right
        self.y_Rotation = rotation

        # calculate drawData
        if self.texture is not None:
            self.setTexture(self.texture, rotation)

        # bind Vertex Array Buffer. Object must have Vertex Array Buffer,
        # if no_vbo, than you must bind vbo outside class constructor
        if not no_vbo:
            self.bindBuffer(self.drawData)
            del self.drawData

    def setTexture(self, texture, rotation=1):
        self.texture = texture
        tex = self.__class__.TEXTURES[texture]

        w_t, h_t = 1, 1
        if tex.repeat:
            w_t = self.rect[2] / tex.size[0]
            h_t = self.rect[3] / tex.size[1]

        w_o, h_o = self.rect[2] / 2, self.rect[3] / 2

        # right (base)
        if rotation == 1:
            data = np.array([
                # obj cords    # color           # tex cords
                -w_o, -h_o,    *self.color,      0.0, h_t,
                +w_o, -h_o,    *self.color,      w_t, h_t,
                +w_o, +h_o,    *self.color,      w_t, 0.0,
                -w_o, +h_o,    *self.color,      0.0, 0.0,
            ], dtype=np.float32)

        # left (mirrored)
        else:
            data = np.array([
                # obj cords    # color           # tex cords
                -w_o, -h_o, *self.color, w_t, h_t,
                +w_o, -h_o, *self.color, 0.0, h_t,
                +w_o, +h_o, *self.color, 0.0, 0.0,
                -w_o, +h_o, *self.color, w_t, 0.0,
            ], dtype=np.float32)

        self.drawData = data

    def rotY(self, new_rotation):
        if abs(new_rotation) != 1:
            raise ValueError('Rotation must be 1 or -1')

        if self.y_Rotation != new_rotation:
            self.y_Rotation = new_rotation
            self.setTexture(self.texture, new_rotation)
            self.bindBuffer(self.drawData, self.vbo)

    def bindBuffer(self, data, vbo=None):
        """Generating Buffer to store this object's vertex data,
        necessary for drawing"""

        if vbo is None:
            vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, vbo)

        # self.drawData.nbytes usually == 128. 32 * np.float32
        glBufferData(GL_ARRAY_BUFFER, data.nbytes, data, GL_STATIC_DRAW)
        self.vbo = vbo

    def __repr__(self):
        return f'<{self.__class__.__name__} {self.rect}. In {len(self.groups())} groups. VBO: {self.vbo}>'

    def align_center(self, to):
        # Move self rect center to other GLObject's center
        self.rect.pos = to.rect.center[:]

    def draw(self, shader):
        if self.visible:
            self.__class__.TEXTURES[self.texture].draw(self.rect.pos, self.vbo, shader)

    #  visual
    def changeOffset(self, offset):
        pass
        # no_offset = [[i - self.tex_offset[0], j - self.tex_offset[1]] for i, j in baseEdgesTex]
        # self.tex_offset = np.array(offset, dtype=np.int16)
        # self.vertexesTex = np.array([[i + offset[0], j + offset[1]] for i, j in no_offset], dtype=np.int32)

    def setColor(self, *args):
        self.color = np.array([*args], dtype=np.float32)
        self.setTexture(self.texture, self.rotation)
        self.bindBuffer(self.drawData, self.vbo)

    #  move
    def move_to(self, pos):
        self.rect.x = pos[0]
        self.rect.y = pos[1]

    def move_by(self, vector):
        self.rect.move_by(vector)

    def getPos(self):
        return self.rect[:2]

    #  delete
    def delete(self):
        print(f'deleted obj: {self}')

        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, 0, None, GL_STATIC_DRAW)

        self.kill()


class GLObjectComposite(Sprite):
    """Multiple GLObjects drawn, moved and rotated together.
    Little variant of GLObjectGroup"""

    def __init__(self, group, *objects):

        """All of the objects must not be members of any SpriteGroups"""
        if any(j.groups() for j in objects):
            raise ValueError(f'One or more of objects are members of GLObjectGroups')

        super().__init__(group)
        self.objects = objects

    def __getitem__(self, item):
        return self.objects[item]

    def draw(self, shader):
        for obj in self.objects:
            obj.draw(shader)

    def rotY(self, rotation):
        for obj in self.objects:
            obj.rotY(rotation)

    def delete(self):
        for obj in self.objects:
            obj.delete()


def make_GL2D_texture(image: pygame.Surface, w: int, h: int, repeat=False) -> int:
    """Loading pygame.Surface as OpenGL texture
    :return New Texture key"""

    # getting data from pygame.Surface
    raw_data = image.get_buffer().raw
    data = np.fromstring(raw_data, np.uint8)

    # bind new texture
    key = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, key)

    # SETTING UP
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)  # настройка сжатия
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)  # настройка растяжения

    if repeat:
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)

    glTexImage2D(GL_TEXTURE_2D, GL_ZERO, GL_RGBA, w, h, GL_ZERO, GL_BGRA, GL_UNSIGNED_BYTE, data)
    #

    # unbind new texture
    glBindTexture(GL_TEXTURE_2D, 0)

    return key


def splitDrawData(draw_data: np.array):
    obj_v = [list(draw_data[h * 8: h * 8 + 2]) for h in range(4)]
    tex_v = [list(draw_data[h * 8 + 6: h * 8 + 8]) for h in range(4)]
    return obj_v, tex_v


def drawGroups(*groups):
    # THE ONLY WAY TO DRAW ON SCREEN

    # drawing each object in each group
    prev_shader = None
    for group in groups:
        group.draw_all(shader_load=(prev_shader is None or prev_shader != group.shader))
        prev_shader = group.shader
