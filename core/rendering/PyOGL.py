import pygame

from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np

from core.Constants import WINDOW_RESOLUTION, TEXTURE_PACK, DEFAULT_FOV_W, DEFAULT_FOV_H, FULL_SCREEN
from utils.files import load_image

# from core.rendering.Shaders import create_shader
shader_program = None

baseEdgesTex = np.array([(GL_ZERO, GL_ONE), (GL_ONE, GL_ONE), (GL_ONE, GL_ZERO), (GL_ZERO, GL_ZERO)], dtype=np.int16)
baseEdgesObj = np.array([(GL_ZERO, GL_ZERO), (GL_ONE, GL_ZERO), (GL_ONE, GL_ONE), (GL_ZERO, GL_ONE)], dtype=np.int16)


def init_display(size=WINDOW_RESOLUTION):
    global shader_program

    if not FULL_SCREEN:
        pygame.display.set_mode(size, flags=pygame.OPENGL | pygame.DOUBLEBUF | pygame.HWSURFACE | pygame.SRCALPHA)
    else:
        pygame.display.set_mode(
            size, flags=pygame.OPENGL | pygame.DOUBLEBUF | pygame.HWSURFACE | pygame.SRCALPHA | pygame.FULLSCREEN)

    clear_display()

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(GL_ZERO, size[0], size[1], GL_ZERO)
    glMatrixMode(GL_MODELVIEW)

    glEnable(GL_TEXTURE_2D)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    #  Creating shader program that will be used for all rendering
    # shader_program = create_shader('vertex.glsl', 'fragment.glsl')
    # shader_program.use()


def clear_display():
    glClearColor(0.35, 0.35, 0.5, 0.0)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)


class Rect:
    __slots__ = ['values']

    def __init__(self, *args):
        self.values = np.array([*args], dtype=np.int32)

    def __getitem__(self, item):
        return self.values[item]

    def copy(self):
        return Rect(*self.values)

    # center
    def getCenter(self):
        return self.values[0] + self.values[2] // 2, self.values[1] + self.values[3] // 2

    def setCenter(self, center):
        self.values[0] = center[0] - self.values[2] // 2
        self.values[1] = center[1] - self.values[3] // 2

    # pos
    def getPos(self):
        return self.values[:2]

    def setY(self, y_v):
        self.values[1] = y_v

    def setX(self, x_v):
        self.values[0] = x_v
    
    def setPos(self, pos):
        self.setX(pos[0])
        self.setY(pos[1])

    # size
    def getSize(self):
        return self.values[2:4]

    def setSize(self, w, h):
        self.values[2] = w
        self.values[3] = h


class GLObjectGroup(pygame.sprite.Group):
    def __init__(self, *args, do_draw=True):
        super().__init__(*args)
        self.do_draw = do_draw

    def update(self, *args):
        super().update(*args)

    def draw_all(self):
        if self.do_draw:
            for obj in self.sprites():
                obj.draw()

    def empty(self):
        super().empty()
        for obj in self.sprites():
            obj.kill()


class GlTexture:
    """vertexes - numpy массив всех вершин квадрата на котором будет текстура
       edges    - numpy массив всех граней этого квадрата. Он одинаков для всех картинок"""

    def __init__(self, image, tex_name, repeat=False):
        self.size = image.get_size()  # units
        self.key = make_GL2D_texture(image, *self.size, repeat=repeat)
        self.repeat = repeat
        self.name = tex_name.replace('.png', '')

    def __repr__(self):
        return f'<GLTexture[{self.key}] {self.name} {self.size[0]}x{self.size[1]}>'

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

    def makeVertexes(self):
        return np.array([(self.size[0] * i, self.size[1] * j) for i, j in baseEdgesObj], dtype=np.int32)

    """actor - параметр, нужный только для анимаций"""
    def draw(self, pos, ver_obj, ver_tex, color, actor=None, ):
        #  verObj, verTex - грани объекта и текстуры на это объекте

        draw_begin()
        glTranslate(pos[0], pos[1], GL_ZERO)

        #  ---
        glBindTexture(GL_TEXTURE_2D, self.key)
        glEnable(GL_TEXTURE_2D)
        glColor4f(*color)

        glBegin(GL_QUADS)
        for i in range(4):
            glTexCoord2f(*ver_tex[i])
            glVertex2f(*ver_obj[i])
        glEnd()

        glDisable(GL_TEXTURE_2D)
        # ---

        draw_end()

    """Удаление текстуры из памяти"""
    def delete(self):
        glDeleteTextures(1, [self.key, ])
        del self


class GLObjectBase(pygame.sprite.Sprite):
    TEXTURES: [GlTexture, ] = None
    texture = 0

    vertexesTex: np.array = None

    center = None
    size = None

    color: np.array

    def __init__(self, group, rect: list, rotation=0, tex_offset=(0, 0), color=None):
        super().__init__(group)

        self.rect = Rect(*rect)
        self.tex_offset = np.array(tex_offset, dtype=np.float16)  # Offset of a texture on this object
        self.setTexture(self.texture)

        self.vertexesObj = [[i * rect[2], j * rect[3]] for i, j in baseEdgesObj]
        self.vertexesObj = np.array(self.vertexesObj, dtype=np.int32)

        self.rotation = rotation

        if color is None:
            color = [1, 1, 1, 1]
        self.setColor(*color)

    def __init_subclass__(cls, **kwargs):
        if cls.size and cls.center:
            cls.rect = Rect(0, 0, *cls.size)
            cls.rect.setCenter(cls.center)

    def align_center(self, to):
        # Move self rect center to other GLObject's center
        self.rect.setCenter(to.rect.getCenter()[:])

    def draw(self, color=None):
        self.__class__.TEXTURES[self.texture].draw(self.rect, self.vertexesObj, self.vertexesTex, self.color)

    def changeOffset(self, offset):
        no_offset = [[i - self.tex_offset[0], j - self.tex_offset[1]] for i, j in baseEdgesTex]
        self.tex_offset = np.array(offset, dtype=np.int16)
        self.vertexesTex = np.array([[i + offset[0], j + offset[1]] for i, j in no_offset], dtype=np.int32)

    def setTexture(self, number: int):
        self.texture = number
        tex = self.__class__.TEXTURES[number]

        v, h = 1, 1
        if tex.repeat:
            v = self.rect[3] / tex.size[1]
            h = self.rect[2] / tex.size[0]

        self.vertexesTex = np.array([
            (i * h + self.tex_offset[0], j * v + self.tex_offset[1]) for i, j in baseEdgesTex
        ], dtype=np.float16)

    def setRotation(self, rotation):
        if self.rotation == rotation:
            return

        self.rotation = rotation
        self.vertexesTex = [self.vertexesTex[j - 1 + 2 * (j % 2 == 0)] for j in range(4)]

    def setColor(self, *args):
        self.color = np.array([*args], dtype=np.float16)

    def move(self, pos):
        self.rect.setX(pos[0])
        self.rect.setY(pos[1])

    def move_by(self, vector):
        pos = self.rect.getPos()
        pos[0] += vector[0]
        pos[1] += vector[1]

    def delete(self):
        print(f'deleted obj: {self}')
        self.kill()

    def getPos(self):
        return self.rect[:2]


class GLObjectComposite(pygame.sprite.Sprite):
    def __init__(self, group, *objects):
        super().__init__(group)
        self.objects = objects

    def __getitem__(self, item):
        return self.objects[item]

    def draw(self):
        for obj in self.objects:
            obj.draw()

    def setRotation(self, rotation):
        for obj in self.objects:
            obj.setRotation(rotation)


#  Поле зрения. Camera
ortho_params = ()


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


# Для вызова перед отрисовкой
def draw_begin():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glPushMatrix()
    gluOrtho2D(*ortho_params)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    glPushMatrix()
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glEnable(GL_BLEND)


# Для вызова после отрисовки
def draw_end():
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()
    glDisable(GL_BLEND)


# camera
def camera_apply(rect):
    global ortho_params
    ortho_params = np.array([rect[0], rect[0] + rect[2], rect[1], rect[1] + rect[3]], dtype='int16')


def focus_camera_to(x_v, y, fov=None):
    global ortho_params

    if fov:
        width = (WINDOW_RESOLUTION[0] * fov) // 2
        height = (WINDOW_RESOLUTION[1] * fov) // 2
    else:
        width = DEFAULT_FOV_W
        height = DEFAULT_FOV_H

    ortho_params = np.array([x_v - width, x_v + width, y - height, y + height], dtype='int16')


# draw
def draw_line(start, end, color):
    draw_begin()
    glColor4f(*color)

    glBegin(GL_LINES)
    glVertex2f(*start)
    glVertex2f(*end)
    glEnd()

    draw_end()


# def draw_texture(key, pos, ver_obj, ver_tex, color):
#     pass
#     # в sublime text'е сохранил
