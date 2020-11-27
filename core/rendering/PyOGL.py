import pygame

from OpenGL.GL import *

import numpy as np

from core.Constants import WINDOW_RESOLUTION, TEXTURE_PACK, DEFAULT_FOV_W,\
    DEFAULT_FOV_H, FULL_SCREEN, DEBUG, DEFAULT_SCALE
from utils.files import load_image
from core.rendering.Shaders import create_shader

import core.Math.Matrix as Mat
from core.Math.DataTypes import Rect4f

# from core.rendering.Shaders import create_shader
shader_program = None

# background color
clear_color = (0.35, 0.35, 0.5, 0.0)


class Camera:
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
        return np.array([(self[0] + self[1]) // 2, (self[2] + self[3]) // 2], dtype=np.int64)

    def setField(self, rect):
        self.ortho_params = np.array([rect[0], rect[0] + rect[2], rect[1], rect[1] + rect[3]], dtype='int64')

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
    global shader_program, camera

    flags = pygame.OPENGL | pygame.DOUBLEBUF | pygame.HWSURFACE | pygame.SRCALPHA

    if FULL_SCREEN:
        flags |= pygame.FULLSCREEN
    pygame.display.set_mode(size, flags=flags)

    clear_display()

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glMatrixMode(GL_MODELVIEW)

    glEnable(GL_TEXTURE_2D)

    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glEnable(GL_BLEND)

    # camera singleton object
    camera = Camera()

    #  Creating shader program that will be used for all rendering
    shader_program = create_shader('vertex.glsl', 'fragment.glsl')
    shader_program.use()

    # setting clear color
    glClearColor(*clear_color)

    # order of vertexes when drawing
    indices = np.array([0, 1, 2, 2, 3, 0], dtype=np.uint32)
    EBO = glGenBuffers(1)
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, EBO)
    glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices, GL_STATIC_DRAW)


def clear_display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)


class GLObjectGroup(pygame.sprite.Group):
    def __init__(self, *args, do_draw=True):
        super().__init__(*args)
        self.do_draw = do_draw

    def update(self, *args):
        super().update(*args)

    def draw_all(self, shader):
        if self.do_draw:
            for obj in self.sprites():
                obj.draw(shader)

    def empty(self):
        super().empty()
        for obj in self.sprites():
            obj.kill()


class GlTexture:
    __slots__ = ['size', 'key', 'repeat', 'name']

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
        # make draw data with size of this texture
        w_o, h_o = self.size

        data = np.array([
            # obj cords|color      |tex cords
            0.0, 0.0,   *color,     0.0, 1.0,
            w_o, 0.0,   *color,     1.0, 1.0,
            w_o, h_o,   *color,     1.0, 0.0,
            0.0, h_o,   *color,     0.0, 0.0

        ], dtype=np.float32)

        return data

    def draw(self, pos, vbo, shader):
        """pos - where to draw
        vbo - key of VertexBufferObject in memory
        shader - currently active shader program"""

        # bind VBO
        glBindBuffer(GL_ARRAY_BUFFER, vbo)

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

        # drawing
        glBindTexture(GL_TEXTURE_2D, self.key)
        glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None)

    """Удаление текстуры из памяти"""
    def delete(self):
        glDeleteTextures(1, [self.key, ])
        del self


class GLObjectBase(pygame.sprite.Sprite):
    TEXTURES: [GlTexture, ] = None
    texture = 0

    center = None
    size = None

    color: np.array

    drawData: np.array

    vbo: int

    def __init__(self, group, rect: list, rotation=0, tex_offset=(0, 0), color=None, no_vbo=False):
        if group is not None:  # group - GLSpriteGroup
            super().__init__(group)
        else:
            super().__init__()

        # in this rect stored position rect[:2] and size of sprite rect[2:]
        self.rect = Rect4f(*rect)

        # Offset of a texture on this object
        self.tex_offset = np.array(tex_offset, dtype=np.float16)

        # -1 for left    0 for middle   1 for right
        self.rotation = rotation

        # additional color over texture
        if color is None:
            color = [1, 1, 1, 1]
        self.setColor(*color)

        # if False object wont be rendered
        self.visible = True

        # calculate drawData
        self.setTexture(self.texture)

        # bind Vertex Array Buffer. Object must have Vertex Array Buffer,
        # if no_vbo, than you must bind vbo outside class constructor
        if not no_vbo:
            self.bindBuffer(self.drawData)

    def setTexture(self, texture: int = None, rotation: int = None):
        if texture is not None:
            self.texture = texture
            tex = self.__class__.TEXTURES[texture]

            w_t, h_t = 1, 1

            if tex.repeat:
                w_t = self.rect[2] / tex.size[0]
                h_t = self.rect[3] / tex.size[1]

            w_o, h_o = self.rect[2], self.rect[3]

            data = np.array([
                # obj cords  # color           # tex cords
                0.0, 0.0,    *self.color,      0.0, h_t,
                w_o, 0.0,    *self.color,      w_t, h_t,
                w_o, h_o,    *self.color,      w_t, 0.0,
                0.0, h_o,    *self.color,      0.0, 0.0
            ], dtype=np.float32)

            self.drawData = data

        if rotation:
            pass

    def bindBuffer(self, data):
        """Generating Buffer to store this object's vertex data,
        necessary for drawing"""

        vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, vbo)

        # self.drawData.nbytes usually == 128. 32 * np.float32
        glBufferData(GL_ARRAY_BUFFER, data.nbytes, data, GL_STATIC_DRAW)
        self.vbo = vbo

    def __init_subclass__(cls, **kwargs):
        #  setting up subclasses
        if cls.size and cls.center:
            """If class has .size and .center, than .rect of this class
            will be set based on this params"""

            cls.rect = Rect4f(0, 0, *cls.size)
            cls.rect.setCenter(cls.center)

    def __repr__(self):
        return f'<{self.__class__.__name__} Rect4f: {self.rect}. In {len(self.groups())} groups.>'

    def align_center(self, to):
        # Move self rect center to other GLObject's center
        self.rect.setCenter(to.rect.getCenter()[:])

    def draw(self, shader):
        if self.visible:
            self.__class__.TEXTURES[self.texture].draw(self.rect.getPos(), self.vbo, shader)

    #  visual
    def changeOffset(self, offset):
        pass
        # no_offset = [[i - self.tex_offset[0], j - self.tex_offset[1]] for i, j in baseEdgesTex]
        # self.tex_offset = np.array(offset, dtype=np.int16)
        # self.vertexesTex = np.array([[i + offset[0], j + offset[1]] for i, j in no_offset], dtype=np.int32)

    def setRotation(self, rotation):
        pass
        # self.vertexesTex = [self.vertexesTex[j - 1 + 2 * (j % 2 == 0)] for j in range(4)]

    def setColor(self, *args):
        self.color = np.array([*args], dtype=np.float16)

    #  move
    def move_to(self, pos):
        self.rect.setX(pos[0])
        self.rect.setY(pos[1])

    def move_by(self, vector):
        pos = self.rect.getPos()
        pos[0] += vector[0]
        pos[1] += vector[1]

    def getPos(self):
        return self.rect[:2]

    #  delete
    def delete(self):
        print(f'deleted obj: {self}')
        self.kill()


class GLObjectComposite(pygame.sprite.Sprite):
    def __init__(self, group, *objects):

        """All of the objects must be in zero SpriteGroups"""
        assert not any(j.groups() for j in objects)

        super().__init__(group)
        self.objects = objects

    def __getitem__(self, item):
        return self.objects[item]

    def draw(self, shader):
        for obj in self.objects:
            obj.draw(shader)

    def setRotation(self, rotation):
        for obj in self.objects:
            obj.setRotation(rotation)


def make_GL2D_texture(image, w, h, repeat=False):
    """pygame.Surface --> OpenGL.texture"""

    raw_data = image.get_buffer().raw
    data = np.fromstring(raw_data, np.uint8)
    bitmap_tex = glGenTextures(1)

    glBindTexture(GL_TEXTURE_2D, bitmap_tex)

    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)  # настройка сжатия
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)  # настройка растяжения

    if repeat:
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)

    glTexImage2D(GL_TEXTURE_2D, GL_ZERO, GL_RGBA, w, h, GL_ZERO, GL_BGRA, GL_UNSIGNED_BYTE, data)
    glBindTexture(GL_TEXTURE_2D, 0)
    return bitmap_tex


def splitDrawData(draw_data: np.array):
    obj_v = [list(draw_data[h * 8: h * 8 + 2]) for h in range(4)]
    tex_v = [list(draw_data[h * 8 + 6: h * 8 + 8]) for h in range(4)]
    return obj_v, tex_v


def drawGroups(*groups):
    # THE ONLY WAY TO DRAW ON SCREEN

    # calculating and binding matrixes of scale and camera
    scaleM = Mat.scale(DEFAULT_SCALE, DEFAULT_SCALE)
    orthoM = camera.getMatrix()
    shader = shader_program.p()

    loc = glGetUniformLocation(shader, "Scale")
    glUniformMatrix4fv(loc, 1, GL_FALSE, scaleM)

    loc = glGetUniformLocation(shader, "Ortho")
    glUniformMatrix4fv(loc, 1, GL_FALSE, orthoM)

    # drawing each object in each group
    for group in groups:
        group.draw_all(shader)
