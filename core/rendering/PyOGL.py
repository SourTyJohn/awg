from OpenGL.GL import *

import core.rendering.Shaders as Shaders
import core.math.linear as lin
from core.rendering.Lighting import __LightingManager
from core.rendering.PyOGL_utils import *
from core.math.rect4f import Rect4f
from core.Constants import *
from core.rendering.Textures import GlTexture
from core.rendering.Textures import EssentialTextureStorage as Ets

from collections import namedtuple
from beartype import beartype
import numpy as np
import pygame


"""
    [CORE RENDERING MODULE]
    
    render pipeline after initDisplay:
        preRender() -> prepare to render
            clearDisplay()
        
        [MAIN PHASE, RENDERING ALL IN-GAME OBJECTS]
        drawGroupsFinally()
            drawTexture()
        drawAllLines()
            drawLineBackend()
        renderLights()
            LightManager.render()
            
        postRender() -> render scene onto the screen
            clearDisplay()
            renderLights()
"""

# background color
clear_color = (0.0, 0.0, 0.0, 0.0)

FIRST_EBO: uintc
T_RENDER_OBJECT = Union["RenderObject", "RenderObjectComposite"]
MAX_OBJECTS_PER_GROUP = 8_192


# CAMERA
class Camera:
    """Singleton that stores camera's position and fov.
    In game usually focused on hero"""
    ortho_params: ARRAY
    matrix: TYPE_MAT
    fov: TYPE_FLOAT = 0.0
    fovW: TYPE_INT = 0
    fovH: TYPE_INT = 0

    __instance = None  # Camera object is Singleton

    def __init__(self, fov=FOV):
        self.set_fov(fov)

        self.ortho_params = np.array([0, 1, 0, 1], dtype=INT64)
        self.prepare_matrix()

    def __new__(cls, *args, **kwargs):
        if cls.__instance:
            del cls.__instance
        cls.__instance = super(Camera, cls).__new__(cls)
        return cls.__instance

    def __getitem__(self, item):
        return self.ortho_params[item]

    def to_default_position(self) -> None:
        self.set_filed(WINDOW_RECT)

    @beartype
    def set_fov(self, fov: float):
        if fov != self.fov:
            self.fov = fov
            self.fovW = (WINDOW_SIZE[0] * self.fov) // 2
            self.fovH = (WINDOW_SIZE[1] * self.fov) // 2

    def get_rect(self):
        # returns Rect4f objects representing field of camera view
        o = self.ortho_params
        return Rect4f(o[0], o[2], o[1] - o[0], o[3] - o[2])

    @property
    def pos(self):
        return np.array([(self[0] + self[1]) // 2, (self[2] + self[3]) // 2], dtype=INT64)

    def set_filed(self, rect) -> None:
        x_, y_, w, h = rect[0], rect[1], rect[2] / 2, rect[3] / 2
        self.ortho_params = np.array([x_ - w, x_ + w, y_ - h, y_ + h], dtype=INT64)

    def prepare_matrix(self) -> None:
        # applying field of view. Called only in draw_begin()
        self.matrix = lin.ortho(*self.ortho_params)

    @beartype
    def get_matrix(self) -> TYPE_MAT:
        return self.matrix

    @beartype
    def focus_to(self, x_v: TYPE_FLOAT, y_v: TYPE_FLOAT, soft: float = 0.2):
        if soft > 0:
            # camera smoothly moving to (x_v, y_x) point
            past_pos = self.pos
            d_x, d_y = past_pos[0] - x_v, past_pos[1] - y_v
            x_v, y_v = past_pos[0] - d_x * soft, past_pos[1] - d_y * soft

        self.ortho_params = np.array(
            [x_v - self.fovW, x_v + self.fovW, y_v - self.fovH, y_v + self.fovH],
            dtype=INT64
        )


camera: Camera


# RENDER GROUP
class RenderGroup:
    __slots__ = (
        '_visible', 'objects', 'updatable', 'frame_buffer', 'shader', 'free_ids', 'depth_write'
    )
    """Container for in-game Objects"""

    def __init__(self, shader="DefaultShader", frame_buffer=None, visible=True, depth_write=True):
        self.frame_buffer = frameBufferGeometry if frame_buffer is None else frame_buffer
        self.objects = {}
        self.updatable = {}
        self.free_ids = set(range(MAX_OBJECTS_PER_GROUP))
        self.depth_write = depth_write

        self.shader = Shaders.shaders.get(shader)
        if self.shader is None:
            raise Error(f"There is no shader with name: {shader}")
        self._visible = visible

    def __repr__(self):
        return f'<RenderGroup({len(self.objects)})>'

    def generate_group_id(self):
        return self.free_ids.pop()

    def add(self, *objs: [T_RENDER_OBJECT, ]):
        for obj in objs:
            #  GETTING TEXTURE KEY
            try:
                key = obj.curr_image().key
            except AttributeError as _:
                key = 0

            #  ADDING OBJECT TO RENDER QUEUE
            grp_id = self.generate_group_id()
            obj.group_id = grp_id
            if key not in self.objects.keys():
                self.objects[key] = {}
            self.objects[key][grp_id] = obj

            #  ADDING OBJECT TO RENDER QUEUE AND UPDATE QUEUE, IF NEEDED
            if hasattr(obj, "update"):
                self.updatable[grp_id] = obj

    def update(self, dt, *args):
        for o in self.updatable.values():
            o.update(dt, *args)

    """drawing all of this group objects"""
    def draw_all(self, object_ids=None):
        """
        to_draw:: Set of Physic Objects body hash, that should be rendered
        If None, all object will be rendered"""

        if not self.pre_draw(): return
        glActiveTexture(GL_TEXTURE0)

        for texture_key, objects in self.objects.items():
            glBindTexture(GL_TEXTURE_2D, texture_key)
            for obj in objects.values():
                obj.draw_single(self.shader)

    def pre_draw(self):
        if not self._visible:
            return False

        self.shader.use()
        return True

    """Deleting all of group.sprites()"""
    def delete_all(self):
        for objs in self.objects.values():
            for obj in objs.values():
                obj.delete()
        self.objects = {}

    def remove(self, obj):
        if hasattr(obj, "curr_image"):
            key = obj.curr_image().key
        else:
            key = "noTex"
        ind = self.objects[key].index(obj)
        del self.objects[key][ind]


class RenderGroupInstanced(RenderGroup):
    def __init__(self, shader="DefaultInstancedShader", frame_buffer=None, visible=True, depth_write=True):
        super().__init__(shader, frame_buffer, visible, depth_write)

    def draw_all(self, object_ids=()):
        """
        to_draw:: Set of Physic Objects body hash, that should be rendered
        If None, all object will be rendered"""

        if not self.pre_draw(): return

        for texture_key, objects in self.objects.items():
            glActiveTexture(GL_TEXTURE0)
            glBindTexture(GL_TEXTURE_2D, texture_key)

            obj = None
            transform = []
            for i, obj in enumerate(objects.values()):
                # if obj.bhash not in object_ids: continue
                transform.append( obj.get_transform() )
            self.shader.passMat4V(f"Transform[0]", np.asfortranarray(transform, dtype=FLOAT32))

            if obj is None: continue
            glBindBuffer(GL_ARRAY_BUFFER, obj.vbo)
            self.shader.prepareDraw()
            glDrawElementsInstanced(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None, len(objects.values()))


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


class RenderObject:
    """Base render object.
    Provides possibility for drawing given texture: GLTexture within given rect: Rect4f
    For :args info check in __init__"""

    # public
    size: tuple = None
    colors: np.array = [np.array([1.0, 1.0, 1.0, 1.0], dtype=np.float32),
                        np.array([1.0, 1.0, 1.0, 1.0], dtype=np.float32),
                        np.array([1.0, 1.0, 1.0, 1.0], dtype=np.float32),
                        np.array([1.0, 1.0, 1.0, 1.0], dtype=np.float32)]
    visible = True
    _vbo: int = 0

    group: Union["RenderGroup", "RenderGroupInstanced"]
    group_id: int

    def __init__(self, group, size=None, rotation=1, tex_offset=(0, 0), drawdata='auto', layer=5):
        self.group_id = 0
        if group is not None:
            group.add(self)
        self.group = group

        # Offset of a texture on this object
        self.tex_offset = np.array(tex_offset, dtype=np.float32)

        # if False object wont be rendered
        self.visible = True

        #  -1 for left   1 for right
        self.y_Rotation = rotation
        assert abs(rotation) <= 1 and isinstance(rotation, int),\
            ValueError(f'Wrong rotation value: {rotation}. Must be -1, 0 or 1')
        self.size = size if size else self.__class__.size

        """Load and bufferize (load to gl buffer) all data, that is required for drawing
        This data includes: texture coords, object coords and color"""
        if isinstance(drawdata, str) and drawdata == 'auto':
            drawdata = drawData(size, self.colors, rotation=rotation, layer=layer)
        self._vbo = bufferize(drawdata)
        self._layer = layer

        """If set to False, it will set glDepthMask to False when rendering ->
        this object won't hide overlapped objects behind it. 
        Should be set False, if this object's texture has alpha channel other than 255"""
        # self.depth_mask = depth_mask

    def __repr__(self):
        return f'<{self.__class__.__name__} {self.rect if hasattr(self, "rect") else "NO RECT"}'

    # VISUAL
    def change_offset(self, offset):
        pass
        # no_offset = [[i - self.tex_offset[0], j - self.tex_offset[1]] for i, j in baseEdgesTex]
        # self.tex_offset = np.array(offset, dtype=np.int16)
        # self.vertexesTex = np.array([[i + offset[0], j + offset[1]] for i, j in no_offset], dtype=np.int32)

    def set_rotation_y(self, new_rotation):
        #  y-axis: left or right
        if self.y_Rotation != new_rotation:
            self.y_Rotation = new_rotation
            drawdata = drawData(self.size, self.colors, rotation=new_rotation, layer=self._layer)
            bufferize(drawdata, self._vbo)

    # DELETE
    def delete(self):
        glBindBuffer(GL_ARRAY_BUFFER, self._vbo)
        glBufferData(GL_ARRAY_BUFFER, 0, None, GL_STATIC_DRAW)
        glDeleteBuffers(1, np.array(self._vbo, ))
        if self.group is not None:
            self.group.remove(self)

    @property
    def vbo(self):
        return self._vbo


class RenderObjectPlaced(RenderObject):
    """Alternative for RenderObjectPhysic
    This object will be rendered in place, taken from self.pos"""

    def __init__(self, group, pos, size=None, rotation=1, tex_offset=(0, 0), drawdata='auto', layer=5):
        super().__init__(group, size, rotation, tex_offset, drawdata, layer)
        self.rect = Rect4f(*pos, *self.__class__.size if not size else size)

    @property
    def pos(self):
        return self.rect.pos

    @pos.setter
    def pos(self, value):
        self.rect.pos = value

    def move_to(self, pos):
        self.rect.x = pos[0]
        self.rect.y = pos[1]

    def move_by(self, vector):
        self.rect.move_by(vector)

    def draw_single(self, shader):
        if not self.visible: return
        drawBound(self.rect.pos, self._vbo, shader, 0)

    def get_transform(self):
        x_, y_ = self.rect.pos
        return lin.FullTransformMat(x_, y_, camera.get_matrix(), FLOAT32(0))


class RenderObjectPhysic(RenderObject):
    """Alternative for RenderObjectPlaced
    This object will be rendered in place, taken from its physic body pos (self.body.pos)
    It will also take rotation from physic body"""

    def __init__(self, group, body, size=None, rotation=1, tex_offset=(0, 0), drawdata='auto', layer=5):
        super().__init__(group, size, rotation, tex_offset, drawdata, layer)
        self.body = body

    @property
    def z_rotation(self):
        return lin.degreesFromNormal(self.body.rotation_vector)

    def draw_single(self, shader):
        if not self.visible: return
        drawBound(self.body.pos_FLOAT32, self._vbo, shader, self.z_rotation)

    def get_transform(self):
        x_, y_ = self.body.pos_FLOAT32
        return lin.FullTransformMat(x_, y_, camera.get_matrix(), FLOAT32(-self.z_rotation))


class AnimatedRenderComponent:
    ANIMATIONS: [Animation, ] = None
    animation = 0
    # ANIMATIONS[0] - always idle animation

    a_time = 0
    a_frame = 0

    def update(self, dt) -> None:
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

    def curr_image(self):
        return self.__class__.ANIMATIONS[self.animation][self.a_frame][0]


class StaticRenderComponent:
    _texture: Union["GlTexture", "str"]

    def curr_image(self):
        return self.texture

    @property
    def texture(self):
        return self._texture

    @texture.setter
    def texture(self, tex_or_key: Union["str", "GlTexture"]):
        if type(tex_or_key) == str:
            self._texture = Ets[tex_or_key]
        else:
            self._texture = tex_or_key

    @texture.getter
    def texture(self, ):
        return self._texture


class RenderObjectComposite:
    """Multiple GLObjects drawn, moved and rotated together.
    Little variant of GLObjectGroup"""

    def __init__(self, group, *objects):
        """None of the objects must not be members of any SpriteGroups"""
        if any(j.group for j in objects):
            raise ValueError(f'One or more of objects are members of GLObjectGroups')

        if group is not None:
            group.add(self)
        self.group = group

        self.objects = objects

    def __getitem__(self, item):
        return self.objects[item]

    def update(self, dt, *args):
        pass

    def draw(self):
        for obj in self.objects:
            obj.draw()

    def rotY(self, rotation):
        for obj in self.objects:
            obj.set_rotation_y(rotation)

    def delete(self):
        for obj in self.objects:
            obj.delete()

    def move_by(self, vector):
        for o in self.objects:
            o.rect.move_by(vector)


# FRAME BUFFER
class FrameBuffer:
    vbo: int
    shader: Shaders.Shader

    def __init__(self):
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

        # SHADER
        color = ((1.0, 1.0, 1.0, 1.0),
                 (1.0, 1.0, 1.0, 1.0),
                 (1.0, 1.0, 1.0, 1.0),
                 (1.0, 1.0, 1.0, 1.0))
        screen_quad = drawDataFullScreen(color)
        self.vbo = bufferize(screen_quad)

        # CHECK COMPLETE
        self.check()
        FrameBuffer.unbind()

    def bind(self):
        glBindFramebuffer(GL_FRAMEBUFFER, self.key)

    def bind_texture(self, slot):
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

    @staticmethod
    def unbind():
        glBindFramebuffer(GL_FRAMEBUFFER, 0)


class FrameBufferDepth(FrameBuffer):
    def __init__(self):
        super(FrameBufferDepth, self).__init__()
        size = WINDOW_RESOLUTION
        self.bind()

        self.rbo = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.rbo)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_DEPTH_COMPONENT, *size, 0, GL_DEPTH_COMPONENT, GL_FLOAT, None)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_COMPARE_MODE, GL_NONE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glBindTexture(GL_TEXTURE_2D, 0)
        glFramebufferTexture(GL_DRAW_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, self.rbo, 0)

    def bind_depth_texture(self, slot):
        if not self.rbo:
            raise ReferenceError('FrameBuffer has no render buffer (depth buffer)')
        glActiveTexture(GL_TEXTURE0 + slot)
        glBindTexture(GL_TEXTURE_2D, self.rbo)


frameBufferGeometry: FrameBufferDepth
frameBufferLight: FrameBuffer
LightingManager: __LightingManager


# DISPLAY
def initDisplay(size=WINDOW_RESOLUTION):
    global camera, frameBufferGeometry, frameBufferLight, FIRST_EBO, LightingManager

    # Display flags
    flags = pygame.OPENGL | pygame.DOUBLEBUF | pygame.HWSURFACE | pygame.SRCALPHA
    flags = flags | pygame.FULLSCREEN if FULL_SCREEN else flags
    pygame.display.set_mode(size, flags=flags)
    
    #  Correct OpenGL Version requirement
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 4)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 0)

    # Initialize modules
    Shaders.init()
    LightingManager = __LightingManager()

    frameBufferGeometry = FrameBufferDepth()
    frameBufferLight = FrameBuffer()
    clearDisplay()
    camera = Camera()
    glClearColor(*clear_color)
    glDepthFunc(GL_LEQUAL)

    glEnable(GL_SCISSOR_TEST)
    glScissor(0, 0, *WINDOW_SIZE)

    # Order of vertexes when drawing
    indices = [
        np.array([0, 1, 2, 2, 3, 0], dtype=np.uint32),
        np.array([0, *np.array([[v, v] for v in range(1, 256)]).flatten()], dtype=np.uint32),
        np.array(range(2 ** 13), dtype=np.uint32)
    ]
    first_ebo = None
    for i in indices:
        ebo = glGenBuffers(1)
        if first_ebo is None:
            first_ebo = ebo
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, i, GL_STATIC_DRAW)
    FIRST_EBO = first_ebo
    bindEBO()

    # Does not allow deprecated gl functions
    pygame.display.gl_set_attribute(
        pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE
    )


def bindEBO(offset=0):
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, FIRST_EBO + offset)


def preRender(do_depth_test=True):
    # MY FRAME BUFFER
    camera.prepare_matrix()
    frameBufferGeometry.bind()
    clearDisplay()

    # ENABLE STUFF
    glEnable(GL_TEXTURE_2D)
    glEnable(GL_STENCIL_TEST)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glEnable(GL_BLEND)

    if do_depth_test:
        glEnable(GL_DEPTH_TEST)


def drawGroupsFinally(object_ids, *groups):
    # THE ONLY WAY TO DRAW ON SCREEN
    # Drawing each object in each group

    for group in groups:
        group.draw_all(object_ids)


def drawBound(pos: TYPE_VEC, vbo: TYPE_NUM, shader: Shaders.Shader, z_rotation: TYPE_NUM = 0.0, **kwargs):
    glBindBuffer(GL_ARRAY_BUFFER, vbo)

    x_, y_ = pos
    mat = lin.FullTransformMat(x_, y_, camera.get_matrix(), FLOAT32(-z_rotation))
    shader.prepareDraw(pos=pos, camera=camera, transform=mat, fbuffer=frameBufferGeometry, **kwargs)

    glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None)


def renderLights(camera_, ):
    lm = LightingManager
    shader = lm.shader

    if lm.do_render:
        glBlendFunc(GL_ONE, GL_ONE_MINUS_SRC_ALPHA)
        frameBufferLight.bind()
        clearDisplay()

        light_groups = lm.generate_groups()
        previous_tex = -1
        shader.use()
        for group in light_groups:
            tex = Ets[ group["texture"] ].key

            if tex != previous_tex:
                previous_tex = tex
                glActiveTexture(GL_TEXTURE0)
                glBindTexture(GL_TEXTURE_2D, tex)

            colors = []
            scales = []
            stencils = []
            transforms = []

            for i, source in enumerate( group["sources"] ):
                transforms.append(source.get_transform(camera_))
                colors.append(source.color)
                scales.append(source.size)
                stencils.append(0)

            shader.passMat4V(f"sTransform[0]", np.asfortranarray(transforms, dtype=FLOAT32))
            shader.passVec4fV(f"sColor[0]", np.asfortranarray(colors, dtype=FLOAT32))
            shader.passVec2fV(f"sScale[0]", np.asfortranarray(scales, dtype=FLOAT32))
            shader.passUIntV(f"sStencil[0]", np.asfortranarray(stencils, dtype=UINT))

            glBindBuffer(GL_ARRAY_BUFFER, lm.vbo)
            shader.prepareDraw()
            glDrawElementsInstanced(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None, len(group["sources"]))

        FrameBuffer.unbind()


def postRender(screen_shader):
    """screen shader - Shader from Shaders module with 'ScreenShader' prefix
    Shader that will be used to render full scene to screen"""

    # MY FRAME BUFFER
    fbuff = frameBufferGeometry
    lbuff = frameBufferLight

    # DEFAULT FRAME BUFFER
    renderLights(camera)
    clearDisplay()

    screen_shader.use()
    glBindBuffer(GL_ARRAY_BUFFER, fbuff.vbo)

    # DISABLE STUFF 1
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glDisable(GL_DEPTH_TEST)

    # SHADER
    screen_shader.prepareDraw()

    # DRAW SCENE AND GUI
    fbuff.bind_texture(0)        # bind scene texture
    lbuff.bind_texture(1)        # bind light texture
    fbuff.bind_depth_texture(2)  # bind depth texture
    glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None)


def clearDisplay():
    # fully clearing display
    glClearColor(*clear_color)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
