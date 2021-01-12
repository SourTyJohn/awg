from OpenGL.GL import *

import numpy as np
from collections import namedtuple

from core.Constants import *
from utils.files import load_image

import core.math.linear as lin
import core.rendering.Shaders as Shaders
from core.math.rect4f import Rect4f

# background color
clear_color = (0.0, 0.0, 0.0, 0.0)


# CAMERA
class Camera:
    """Singleton that stores camera's position and fov.
    In game usually focused on hero"""

    ortho_params: np.array
    __instance = None  # Camera object is Singleton

    def __init__(self):
        #  Camera params. np.array([left, right, bottom, top], dtype=int64)
        self.ortho_params = np.array([0, 0, 0, 0], dtype=np.int64)

        #  Field of view
        self.fov = 1  # scale
        self.fovW = DEFAULT_FOV_W  # field half width
        self.fovH = DEFAULT_FOV_H  # filed half height

        #
        self.triggers = set()

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
            self.fovW = (WINDOW_SIZE[0] * self.fov) / 2
            self.fovH = (WINDOW_SIZE[1] * self.fov) / 2

    def getRect(self):
        # returns Rect4f objects representing field of camera view
        o = self.ortho_params
        return Rect4f(o[0], o[2], o[1] - o[0], o[3] - o[2])

    @property
    def pos(self):
        return np.array([(self[0] + self[1]) // 2, (self[2] + self[3]) // 2], dtype=np.int32)

    def setField(self, rect):
        x_, y_, w, h = rect[0], rect[1], rect[2] / 2, rect[3] / 2
        self.ortho_params = np.array([x_ - w, x_ + w, y_ - h, y_ + h], dtype='int64')

    def getMatrix(self):
        # applying field of view. Called only in draw_begin()
        return lin.ortho(*self.ortho_params)

    def focusTo(self, x_v, y_v, soft=True):
        if soft:
            # camera smoothly moving to (x_v, y_x) point
            past_pos = self.pos
            d_x, d_y = past_pos[0] - x_v, past_pos[1] - y_v
            x_v, y_v = past_pos[0] - d_x * 0.2, past_pos[1] - d_y * 0.2

        self.ortho_params = np.array(
            [x_v - self.fovW, x_v + self.fovW, y_v - self.fovH, y_v + self.fovH],
            dtype='int64'
        )


camera: Camera


# DISPLAY
def init_display(size=WINDOW_RESOLUTION):
    global camera, frameBuffer

    # Display flags
    flags = pygame.OPENGL | pygame.DOUBLEBUF | pygame.HWSURFACE | pygame.SRCALPHA

    if FULL_SCREEN:
        flags |= pygame.FULLSCREEN
    pygame.display.set_mode(size, flags=flags)

    # Check Version
    glMajorVersion = [int(x) for x in glGetString(GL_VERSION).decode('utf-8').split(' - ')[0].split('.')]
    if glMajorVersion[0] < 3 or (glMajorVersion[0] == 3 and glMajorVersion[1] < 2):
        # TODO NOTIFICATION WINDOW
        raise GLerror('You need OpenGL 3.2 or higher to run')

    Shaders.init()
    frameBuffer = FrameBuffer()
    clear_display()
    camera = Camera()
    glClearColor(*clear_color)

    # Order of vertexes when drawing
    indices = np.array([0, 1, 2, 2, 3, 0], dtype=np.uint32)
    ebo = glGenBuffers(1)
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo)
    glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices, GL_STATIC_DRAW)


def clear_display():
    # fully clearing display
    glClearColor(*clear_color)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)


# RENDER
def pre_render():
    # MY FRAME BUFFER
    frameBuffer.bind()
    clear_display()

    # ENABLE STUFF
    glEnable(GL_TEXTURE_2D)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glEnable(GL_BLEND)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_MULTISAMPLE)


def post_render():
    # MY FRAME BUFFER
    fb = frameBuffer

    # DEFAULT FRAME BUFFER
    glBindFramebuffer(GL_FRAMEBUFFER, 0)
    clear_display()

    fb.shader.use()
    glBindBuffer(GL_ARRAY_BUFFER, fb.vbo)

    # DISABLE STUFF 1
    glDisable(GL_DEPTH_TEST)
    glDisable(GL_MULTISAMPLE)

    # SHADER
    fb.shader.draw(None, )

    # DRAW
    fb.bind_texture()
    glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None)

    # DISABLE STUFF 2
    glDisable(GL_TEXTURE_2D)
    glDisable(GL_BLEND)


# RENDER GROUP
class RenderGroup(pygame.sprite.Group):
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
        return f'<RenderGroup({len(self.sprites())}) {self.name}>'

    """drawing all of this group objects"""
    def draw_all(self, shader_load, to_draw=None):
        """Set of Physic Objects body hash, that should be rendered
        If None, all object will be rendered"""

        if not self.do_draw:
            return

        shader = Shaders.shaders[self.shader]
        if shader_load:
            # PREPARING SHADER USAGE
            # calculating and binding matrixes of scale and camera
            scaleM = lin.scale(DEFAULT_SCALE, DEFAULT_SCALE)
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
            obj.smart_draw(shader)

    """Clearing storage"""
    def empty(self):
        super().empty()

    """Deleting all of group.sprites()"""
    def delete_all(self):

        for obj in self.sprites():
            obj.delete()

        self.empty()


# TEXTURE
class GlTexture:
    __slots__ = ('size', 'key', 'repeat', 'name', 'normals')

    def __init__(self, image, tex_name, repeat=False, normal_map=None):
        self.size = image.get_size()  # units
        self.key = make_GL2D_texture(image, *self.size, repeat=repeat)
        self.repeat = repeat
        self.name = tex_name.replace('.png', '')

        # NORMAL MAP
        if normal_map is not None:
            self.normals = make_GL2D_texture(normal_map, *self.size, repeat=repeat)
        else:
            self.normals = 0

        # DEBUG
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

    # TODO: TEXT, TEXT STORAGE, TEXT DELETE WHEN NOT USED
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
        object_data = (-w_o, -h_o, w_o, -h_o, w_o, h_o, -w_o, h_o)
        color_data = (color, color, color, color)
        texture_data = (0, 1, 1, 1, 1, 0, 0, 0)
        return object_data, texture_data, color_data

    def draw(self, pos, vbo, shader, z_rotation=0):
        """pos - where to draw
        vbo - key of VertexBufferObject in memory
        shader - currently active shader program"""

        # BINDING BUFFERS
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


# ANIMATION
class Animation:
    frames: tuple = None

    def __init__(self, frames, repeat=False):
        """frames = [ [GLTexture,  Rect4f,  int,      ], ... ]
                       texture,    hitbox,  end_time,  """
        self.frames = frames
        self.repeat = repeat

    def __getitem__(self, item):
        return self.frames[item]

    @property
    def frames_count(self):
        return len(self.frames)

    def started(self, actor, frame=0):
        pass

    def new_frame(self, actor):
        pass


class AttackAnimation(Animation):
    hit_frames: {int: namedtuple, }
    # hit_frames = {frame_number: tuple(damage, size, offset)

    def new_frame(self, actor):
        if actor.a_frame in self.hit_frames.keys():
            # DO HIT -> CREATE TRIGGER OBJECT
            pass


# RENDER OBJECT
class Sprite(pygame.sprite.Sprite):
    rect: Rect4f

    def smart_draw(self, shader):
        pass


class RenderObject(Sprite):
    """Base render object. Provides drawing given texture:GLTexture within given rect:Rect4f
    For :args info check in __init__"""

    # public
    size: tuple = None
    colors: np.array = [np.array([1.0, 1.0, 1.0, 1.0], dtype=np.float32),
                        np.array([1.0, 1.0, 1.0, 1.0], dtype=np.float32),
                        np.array([1.0, 1.0, 1.0, 1.0], dtype=np.float32),
                        np.array([1.0, 1.0, 1.0, 1.0], dtype=np.float32)]

    # vertex buffer object key
    vbo: int = 0

    # should object be rendered
    visible = True

    def __init__(self, group, pos, size=None, rotation=1, tex_offset=(0, 0), drawdata='auto', layer=0.5):
        pass
        """If no group provided, than this object won't be rendered,
        unless it is part of GLObjectComposite"""
        super().__init__(group) if group is not None else super().__init__()

        """Rect - rectangle where object's texture will be rendered
        rect[0, 1] - center position, rect[2, 3] - width, height of rectangle"""
        self.rect = Rect4f(*pos, *self.__class__.size if not size else size)

        # Offset of a texture on this object
        self.tex_offset = np.array(tex_offset, dtype=np.float32)

        # if False object wont be rendered
        self.visible = True

        #  -1 for left   1 for right
        self.y_Rotation = rotation

        """Load and bufferize (load to gl buffer) all data, that is required for drawing
        This data includes: texture coords, object coords and color"""
        if drawdata == 'auto':
            drawdata = make_draw_data(self.rect.size, self.curr_image, self.colors, rotation=rotation, layer=layer)
        self.vbo = bufferize(drawdata)

        """If set to False, it will set glDepthMask to False when rendering ->
        this object won't hide overlapped objects behind it. 
        Should be set False, if this object's texture has alpha channel other than 255"""
        # self.depth_mask = depth_mask

    def __repr__(self):
        return f'<{self.__class__.__name__} {self.rect}. In {len(self.groups())} groups>'

    @property
    def curr_image(self):
        """Getting current image of object.
        In this class it does not work as intended.
        True functions defined in subclasses"""
        return GlTexture

    # VISUAL
    def changeOffset(self, offset):
        pass
        # no_offset = [[i - self.tex_offset[0], j - self.tex_offset[1]] for i, j in baseEdgesTex]
        # self.tex_offset = np.array(offset, dtype=np.int16)
        # self.vertexesTex = np.array([[i + offset[0], j + offset[1]] for i, j in no_offset], dtype=np.int32)

    def rotY(self, new_rotation):
        if self.y_Rotation != new_rotation:
            self.y_Rotation = new_rotation
            drawdata = make_draw_data(self.rect.size, self.curr_image, self.colors, new_rotation)
            bufferize(drawdata, self.vbo)

    # MOVE
    def move_to(self, pos):
        self.rect.x = pos[0]
        self.rect.y = pos[1]

    def move_by(self, vector):
        self.rect.move_by(vector)

    # DELETE
    def delete(self):
        print(f'deleted obj: {self}')
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, 0, None, GL_STATIC_DRAW)
        self.kill()

    # DRAW
    def smart_draw(self, shader):
        if hasattr(self, 'body') and hasattr(self, 'z_rotation'):
            # DRAW OBJECTS WITH PHYSIC BODY
            if self.visible:
                frame = self.curr_image
                frame.draw(self.body.pos, self.vbo, shader, z_rotation=self.z_rotation)
        else:
            # DRAW BASE RENDER OBJECTS
            self.__class__.draw(self, shader)

    def draw(self, shader, z_rotation):
        return self.visible


class RenderObjectAnimated(RenderObject):
    ANIMATIONS: [Animation, ] = None
    animation = 0
    # ANIMATIONS[0] - always idle animation

    # a_ stands for Animation
    a_time = 0
    a_frame = 0

    def update(self, dt, *args, **kwargs) -> None:
        animation = self.__class__.ANIMATIONS[self.animation]
        frame = animation[self.a_frame]

        self.a_time += dt * animation.speed

        # next frame
        if self.a_time >= frame[2]:

            # animation ended
            if animation.frames_count == self.a_frame:

                # Catch animation end
                animation.ended(self.animation)

                if animation.repeat:
                    # Restart current animation if it is repeating
                    self.animation_start(self.animation)
                else:
                    # Start idle animation
                    self.animation_start(0)
                return

            self.a_frame += 1
            animation.new_frame()

    def animation_start(self, animation, frame=0):
        self.animation = animation
        self.a_frame = frame

        a = self.ANIMATIONS[animation]
        a.started(self, frame)

        if frame != 0:
            # You can start animation from any of it's frame
            self.a_time = a[frame - 1][2]
            return
        self.a_time = 0

    def draw(self, shader, z_rotation=0):
        if super().draw(shader, z_rotation):
            self.curr_image.draw(self.rect.pos, self.vbo, shader, z_rotation=z_rotation)

    @property
    def curr_image(self):
        return self.__class__.ANIMATIONS[self.animation][self.a_frame][0]


class RenderObjectStatic(RenderObject):
    TEXTURES: [GlTexture, ] = None
    texture = 0

    def draw(self, shader, z_rotation=0):
        if super().draw(shader, z_rotation):
            self.curr_image.draw(self.rect.pos, self.vbo, shader, z_rotation=z_rotation)

    @property
    def curr_image(self):
        return self.__class__.TEXTURES[self.texture]


class RenderObjectComposite(Sprite):
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


# MAKE && BIND TEXTURE
def make_GL2D_texture(image, w: int, h: int, repeat=False) -> int:
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


# DRAW DATA
def make_draw_data(size, tex, colors, rotation=1, layer=0.5):
    w_t, h_t = 1, 1
    if tex.repeat:
        # if texture is repeating
        w_t = size[0] / tex.size[0]
        h_t = size[1] / tex.size[1]

    w_o, h_o = size[0] / 2, size[1] / 2

    # right (base)
    if rotation == 1:
        data = np.array([
            # obj cords         # color      # tex cords
            -w_o, -h_o, layer,  *colors[0],  0.0, h_t,
            +w_o, -h_o, layer,  *colors[1],  w_t, h_t,
            +w_o, +h_o, layer,  *colors[2],  w_t, 0.0,
            -w_o, +h_o, layer,  *colors[3],  0.0, 0.0,
        ], dtype=np.float32)

    # left (mirrored)
    else:
        data = np.array([
            # obj cords         # color      # tex cords
            -w_o, -h_o, layer,  *colors[0],  w_t, h_t,
            +w_o, -h_o, layer,  *colors[1],  0.0, h_t,
            +w_o, +h_o, layer,  *colors[2],  0.0, 0.0,
            -w_o, +h_o, layer,  *colors[3],  w_t, 0.0,
        ], dtype=np.float32)

    return data


def make_draw_data_for_screen(colors, layer=1.0):
    w_t, h_t = 1.0, 1.0

    data = np.array([
        # obj cords         # color      # tex cords
        -1.0, -1.0, layer,  *colors[0],  0.0, h_t,
        +1.0, -1.0, layer,  *colors[1],  w_t, h_t,
        +1.0, +1.0, layer,  *colors[2],  w_t, 0.0,
        -1.0, +1.0, layer,  *colors[3],  0.0, 0.0,
    ], dtype=np.float32)

    return data


def bufferize(data, vbo=None):
    """Generating Buffer to store this object's vertex data,
    necessary for drawing"""
    if vbo is None:
        vbo = glGenBuffers(1)

    glBindBuffer(GL_ARRAY_BUFFER, vbo)
    glBufferData(GL_ARRAY_BUFFER, data.nbytes, data, GL_STATIC_DRAW)

    return vbo


def splitDrawData(data: np.array):
    obj_v = [list(data[h * 8: h * 8 + 2]) for h in range(4)]
    tex_v = [list(data[h * 8 + 6: h * 8 + 8]) for h in range(4)]
    return obj_v, tex_v


# DRAWING FUNCTION
def drawGroups(render_zone, *groups):
    # THE ONLY WAY TO DRAW ON SCREEN

    # Drawing each object in each group
    prev_shader = None

    # Getting objects that should be rendered
    to_draw = None
    # if render_zone is not None:
    #     to_draw = render_zone.entities

    for group in groups:
        group.draw_all(to_draw=to_draw, shader_load=(prev_shader is None or prev_shader != group.shader))
        prev_shader = group.shader


# FRAME BUFFER
class FrameBuffer:
    vbo: int
    shader: Shaders.Shader

    def __init__(self, anti_alias=settings['Anti-Alias']):
        size = WINDOW_RESOLUTION

        self.key = glGenFramebuffers(1)
        self.bind()

        # TEXTURE FOR IMAGE BUFFER
        self.tex = glGenTextures(1)
        self.anti_alias = anti_alias

        if anti_alias != 0:
            # TODO: ANTI-ALIAS
            raise ValueError('Anti-Alias does not work yet')
            # TEXTURE WITH ANTI-ALIASING
            # glBindTexture(GL_TEXTURE_2D_MULTISAMPLE, self.tex)
            # glTexImage2DMultisample(GL_TEXTURE_2D_MULTISAMPLE, anti_alias, GL_RGBA, *size, False)
            # glBindTexture(GL_TEXTURE_2D_MULTISAMPLE, 0)
            # glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D_MULTISAMPLE, self.tex, 0)

        else:
            # TEXTURE WITHOUT ANTI-ALIASING
            glBindTexture(GL_TEXTURE_2D, self.tex)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, *size, 0, GL_RGBA, GL_UNSIGNED_BYTE, None)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glBindTexture(GL_TEXTURE_2D, 0)
            glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self.tex, 0)

        # DEPTH + STENCIL BUFFER
        self.rbo = glGenRenderbuffers(1)
        glBindRenderbuffer(GL_RENDERBUFFER, self.rbo)
        glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH24_STENCIL8, *size)
        glBindRenderbuffer(GL_RENDERBUFFER, 0)
        glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_STENCIL_ATTACHMENT, GL_RENDERBUFFER, self.rbo)

        # SHADER
        color = ((1.0, 1.0, 1.0, 1.0),
                 (1.0, 1.0, 1.0, 1.0),
                 (1.0, 1.0, 1.0, 1.0),
                 (1.0, 1.0, 1.0, 1.0))
        screen_quad = make_draw_data_for_screen(color)
        self.vbo = bufferize(screen_quad)
        self.set_shader()

        # CHECK COMPLETE
        self.check()
        self.unbind()

    def set_shader(self, shader='Default'):
        self.shader = Shaders.shaders['ScreenShader' + shader]

    def bind(self):
        glBindFramebuffer(GL_FRAMEBUFFER, self.key)

    def bind_texture(self):
        glBindTexture(GL_TEXTURE_2D, self.tex)
        # if self.anti_alias:
        #     glBindTexture(GL_TEXTURE_2D_MULTISAMPLE, self.tex)

    @staticmethod
    def unbind():
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

    def check(self):
        """If buffer incomplete raises error.
        Called when frame buffer initialized"""
        glBindFramebuffer(GL_FRAMEBUFFER, self.key)
        status = glCheckFramebufferStatus(GL_FRAMEBUFFER)
        if status == GL_FRAMEBUFFER_COMPLETE:
            return True
        raise GLerror(f'FrameBuffer[{self.key}] Buffer Incomplete; Status: {status}')


frameBuffer: FrameBuffer
