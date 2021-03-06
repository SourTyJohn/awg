from OpenGL.GL import *

import numpy as np
import pygame
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


def blank(): pass


camera: Camera
renderLights = blank


def clear_display():
    # fully clearing display
    glClearColor(*clear_color)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)


# RENDER
def pre_render(do_depth_test=True):
    # MY FRAME BUFFER
    frameBuffer.bind()
    clear_display()

    # ENABLE STUFF
    glEnable(GL_TEXTURE_2D)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glEnable(GL_BLEND)

    if do_depth_test:
        glEnable(GL_DEPTH_TEST)


#  pre_render()
#  draw_groups()
#  post_render()


def post_render(screen_shader):
    """screen shader - Shader from Shaders module with 'ScreenShader' prefix
    Shader that will be used to render full scene to screen"""

    # MY FRAME BUFFER
    fbuff = frameBuffer
    lbuff = lightBuffer

    # DEFAULT FRAME BUFFER
    renderLights()

    clear_display()

    screen_shader.use()
    glBindBuffer(GL_ARRAY_BUFFER, fbuff.vbo)

    # DISABLE STUFF 1
    glDisable(GL_DEPTH_TEST)

    # SHADER
    screen_shader.prepareDraw(None, )

    # DRAW SCENE AND GUI
    fbuff.bind_texture(0)        # bind scene texture
    lbuff.bind_texture(1)        # bind light texture
    fbuff.bind_depth_texture(2)  # bind depth texture
    glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None)

    # DISABLE STUFF 2
    glDisable(GL_TEXTURE_2D)
    glDisable(GL_BLEND)


# RENDER GROUP
class RenderGroup(pygame.sprite.Group):
    __slots__ = ('_visible', )
    """Container of GlObjects
    """

    def __init__(self, *args, visible=True):
        super().__init__(*args)
        self.visible = visible

    def __repr__(self):
        #  Memory: {asizeof(self)}
        return f'<RenderGroup({len(self.sprites())})>'

    """drawing all of this group objects"""
    def draw_all(self, to_draw=None):
        """Set of Physic Objects body hash, that should be rendered
        If None, all object will be rendered"""

        if not self.visible:
            return

        # DRAWING
        for obj in self.sprites():
            obj.smart_draw()

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

    def __init__(self, data: np.ndarray, size, tex_name, repeat=False):
        self.size = size  # units
        self.key = make_GL2D_texture(data, *self.size, repeat=repeat)
        self.repeat = repeat
        self.name = tex_name.replace('.png', '')

        # DEBUG
        if DEBUG:
            print(self)

    def __repr__(self):
        return f'<GLTexture[{self.key}] \t size: {self.size[0]}x{self.size[1]}px. \t name: "{self.name}">'

    @classmethod
    def load_file(cls, image_name, repeat=False):
        data, size = load_image(image_name, TEXTURE_PACK)

        if data is None:
            print(f'texture: {image_name} error. Not loaded')

        return GlTexture(data, size, image_name, repeat)

    @classmethod
    def load_image(cls, image_name, image, repeat=False):
        data = np.fromstring(image.tobytes(), np.uint8)
        size = image.size

        return GlTexture(data, size, image_name, repeat)

    def makeDrawData(self, layer, colors=None):
        """Make draw data with size of this texture
        Usually GlObjects have their own drawData, but you can calculate drawData,
        which will perfectly match this texture"""
        if colors is None:
            colors = ((1.0, 1.0, 1.0, 1.0), ) * 4

        make_draw_data(self.size, colors, layer=layer)
        return make_draw_data(self.size, colors, layer=layer)

    def draw(self, pos, vbo, shader, z_rotation=0, **kwargs):
        draw(self.key, pos, vbo, shader, z_rotation, **kwargs)

    """Удаление текстуры из памяти"""
    def delete(self):
        glDeleteTextures(1, [self.key, ])
        del self


def draw(tex, pos, vbo, shader, z_rotation=0, tex_slot=0, **kwargs):
    glBindBuffer(GL_ARRAY_BUFFER, vbo)

    mat = lin.FullTransformMat(*pos, camera, -z_rotation)
    shader.prepareDraw(pos, camera=camera, transform=mat, fbuffer=frameBuffer, **kwargs)

    glActiveTexture(GL_TEXTURE0 + tex_slot)
    glBindTexture(GL_TEXTURE_2D, tex)
    glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None)


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

    def smart_draw(self):
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

    shader = 'DefaultShader'

    def __init__(self, group, pos, size=None, rotation=1, tex_offset=(0, 0), drawdata='auto', layer=5):
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
        assert abs(rotation) <= 1 and isinstance(rotation, int),\
            ValueError(f'Wrong rotation value: {rotation}. Must be -1, 0 or 1')

        """Load and bufferize (load to gl buffer) all data, that is required for drawing
        This data includes: texture coords, object coords and color"""
        if isinstance(drawdata, str) and drawdata == 'auto':
            drawdata = make_draw_data(self.rect.size, self.colors, rotation=rotation, layer=layer)
        self.vbo = bufferize(drawdata)
        self._layer = layer

        """If set to False, it will set glDepthMask to False when rendering ->
        this object won't hide overlapped objects behind it. 
        Should be set False, if this object's texture has alpha channel other than 255"""
        # self.depth_mask = depth_mask

        """Shader that will be used to draw this object"""
        self.shader = Shaders.shaders[self.shader]

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
            drawdata = make_draw_data(self.rect.size, self.colors, rotation=new_rotation, layer=self._layer)
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
    def smart_draw(self, ):
        """This method decides if object should be rendered as object with physic body
        or as regular RenderObject.
        PhysicObjects will be rendered with same position and z_rotation as it's ph.body"""

        if not self.visible:
            return

        self.shader.use()

        if hasattr(self, 'body') and hasattr(self, 'z_rotation'):
            # DRAW OBJECTS WITH PHYSIC BODY
            frame = self.curr_image
            frame.draw(self.body.pos, self.vbo, self.shader, z_rotation=self.z_rotation)
        else:
            # DRAW BASE RENDER OBJECTS
            self.__class__.draw(self, self.shader, 0)

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

    def smart_draw(self):
        for obj in self.objects:
            obj.smart_draw()

    def rotY(self, rotation):
        for obj in self.objects:
            obj.rotY(rotation)

    def delete(self):
        for obj in self.objects:
            obj.delete()


# MAKE && BIND TEXTURE
def make_GL2D_texture(image_data: np.ndarray, w: int, h: int, repeat=False) -> int:
    """Loading pygame.Surface as OpenGL texture
    :return New Texture key"""

    # getting data from pygame.Surface

    # bind new texture
    key = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, key)

    # SETTING UP
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)  # настройка сжатия
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)  # настройка растяжения

    if repeat:
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)

    glTexImage2D(GL_TEXTURE_2D, GL_ZERO, GL_RGBA, w, h, GL_ZERO, GL_RGBA, GL_UNSIGNED_BYTE, image_data)
    #

    # unbind new texture
    glBindTexture(GL_TEXTURE_2D, 0)

    return key


# DRAW DATA
def make_draw_data(size, colors, rotation=1, layer=5):
    # ::arg layer - value from 0 to 10
    # lower it is, nearer object to a camera
    assert 0 <= layer <= 10 and isinstance(layer, int), f'Wrong layer param: {layer}. ' \
                                                        f'Should be integer from 1 to 10'
    layer = (5 - layer) / 10

    w_t, h_t = 1, 1
    w_o, h_o = size[0] / 2, size[1] / 2

    # right (base)
    if rotation == 1:
        data = np.array([
            # obj cords         # color      # tex cords
            -w_o, -h_o, layer, *colors[0],   0.0, h_t,
            +w_o, -h_o, layer, *colors[1],   w_t, h_t,
            +w_o, +h_o, layer, *colors[2],   w_t, 0.0,
            -w_o, +h_o, layer, *colors[3],   0.0, 0.0,
        ], dtype=np.float32)

    # left (mirrored)
    else:
        data = np.array([
            # obj cords         # color      # tex cords
            -w_o, -h_o, layer, *colors[0],   w_t, h_t,
            +w_o, -h_o, layer, *colors[1],   0.0, h_t,
            +w_o, +h_o, layer, *colors[2],   0.0, 0.0,
            -w_o, +h_o, layer, *colors[3],   w_t, 0.0,
        ], dtype=np.float32)

    return data


def make_draw_data_for_screen(colors):
    layer = 1
    w_t, h_t = 1.0, 1.0
    w_o, h_o = 1.0, 1.0

    data_base = np.array([
        # obj cords         # color       # texture
        -w_o, -h_o, layer, *colors[0], 0.0, h_t,
        +w_o, -h_o, layer, *colors[1], w_t, h_t,
        +w_o, +h_o, layer, *colors[2], w_t, 0.0,
        -w_o, +h_o, layer, *colors[3], 0.0, 0.0,
    ], dtype=np.float32)

    return data_base


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

    # Getting objects that should be rendered
    to_draw = None
    # if render_zone is not None:
    #     to_draw = render_zone.entities

    for group in groups:
        group.draw_all(to_draw=to_draw)


# FRAME BUFFER
class FrameBuffer:
    vbo: int
    shader: Shaders.Shader

    def __init__(self, depth_buff=False):
        size = WINDOW_RESOLUTION

        self.key = glGenFramebuffers(1)
        self.bind()

        # TEXTURE FOR IMAGE BUFFER
        self.tex = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.tex)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, *size, 0, GL_RGBA, GL_UNSIGNED_BYTE, None)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glBindTexture(GL_TEXTURE_2D, 0)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self.tex, 0)

        self.rbo = 0
        if depth_buff:
            self.rbo = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, self.rbo)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_DEPTH_COMPONENT, *size, 0, GL_DEPTH_COMPONENT, GL_FLOAT, None)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_COMPARE_MODE, GL_NONE)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
            glBindTexture(GL_TEXTURE_2D, 0)
            glFramebufferTexture(GL_DRAW_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, self.rbo, 0)

        # SHADER
        color = ((1.0, 1.0, 1.0, 1.0),
                 (1.0, 1.0, 1.0, 1.0),
                 (1.0, 1.0, 1.0, 1.0),
                 (1.0, 1.0, 1.0, 1.0))
        screen_quad = make_draw_data_for_screen(color)
        self.vbo = bufferize(screen_quad)

        # CHECK COMPLETE
        self.check()
        unbind_framebuff()

    def bind(self):
        glBindFramebuffer(GL_FRAMEBUFFER, self.key)

    def bind_texture(self, slot=0):
        glActiveTexture(GL_TEXTURE0 + slot)
        glBindTexture(GL_TEXTURE_2D, self.tex)

    def check(self):
        """If buffer incomplete raises error.
        Called when frame buffer initialized"""
        glBindFramebuffer(GL_FRAMEBUFFER, self.key)
        status = glCheckFramebufferStatus(GL_FRAMEBUFFER)
        if status == GL_FRAMEBUFFER_COMPLETE:
            return True
        raise GLerror(f'FrameBuffer[{self.key}] Buffer Incomplete; Status: {status}')

    def bind_depth_texture(self, slot=2):
        if not self.rbo:
            raise ReferenceError('FrameBuffer has no render buffer (depth buffer)')
        glActiveTexture(GL_TEXTURE0 + slot)
        glBindTexture(GL_TEXTURE_2D, self.rbo)


def unbind_framebuff():
    glBindFramebuffer(GL_FRAMEBUFFER, 0)


frameBuffer: FrameBuffer
lightBuffer: FrameBuffer


# DISPLAY
def init_display(size=WINDOW_RESOLUTION):
    global camera, frameBuffer, renderLights, lightBuffer

    # Display flags
    flags = pygame.OPENGL | pygame.DOUBLEBUF | pygame.HWSURFACE | pygame.SRCALPHA

    if FULL_SCREEN:
        flags |= pygame.FULLSCREEN
    pygame.display.set_mode(size, flags=flags)
    
    #  Correct OpenGL Version requierment
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 2)

    Shaders.init()
    frameBuffer = FrameBuffer(depth_buff=True)
    clear_display()
    camera = Camera()
    glClearColor(*clear_color)
    glDepthFunc(GL_LEQUAL)

    # Order of vertexes when drawing
    indices = np.array([0, 1, 2, 2, 3, 0], dtype=np.uint32)
    ebo = glGenBuffers(1)
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo)
    glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices, GL_STATIC_DRAW)

    # Does not allow deprecated gl functions
    pygame.display.gl_set_attribute(
        pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE
    )

    # LIGHTING IMPORT
    from core.rendering.Lighting import renderLights as Rl
    from core.rendering.Lighting import lightBuffer as Lb
    renderLights, lightBuffer = Rl, Lb
