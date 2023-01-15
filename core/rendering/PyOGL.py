import warnings

from OpenGL.GL import *

import core.rendering.Shaders as Shaders
import core.math.linear as lin
from core.rendering.Lighting import __LightingManager
from core.rendering.PyOGL_utils import *
from core.Constants import *
from core.Typing import *
from core.rendering.Textures import GlTexture
from core.rendering.Textures import EssentialTextureStorage as Ets
from core.rendering.Materials import EssentialMaterialStorage as Ems

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
class RenderUpdateGroup:
    __slots__ = (
        '_visible', 'objects', 'updatable', 'frame_buffer', 'shader', 'depth_write'
    )
    """Container for in-game Objects"""

    def __init__(self, shader="DefaultShader", visible=True, depth_write=True):
        self.objects: dict = {}
        self.updatable = {}
        self.depth_write = depth_write

        self.shader = Shaders.shaders.get(shader)
        if self.shader is None:
            raise Error(f"There is no shader with name: {shader}")
        self._visible = visible

    def __repr__(self):
        return f'<RenderUpdateGroup({len(self.objects)})>'

    def add(self, *objs: [T_RENDER_OBJECT, ]):
        """You can redefine how objects are added and how they are sorted
        by changing _get_object_key and _add_one of child classes"""
        for obj in objs:
            key = self._get_object_key(obj)
            uid = self._add_one(obj, key)
            if hasattr(obj, "update"): self.updatable[uid] = obj

    @staticmethod
    def _get_object_key(obj):
        """This function basically defines principle in which objects in group will be sorted
        In this scenario, objects will be sorted be Texture"""
        try:
            key = obj.curr_image().key
        except AttributeError as _:
            key = 0
        return key

    def _add_one(self, obj, key):
        uid = obj.UID
        if key not in self.objects.keys():
            self.objects[key] = {}
        self.objects[key][uid] = obj
        return uid

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


class RenderUpdateGroup_Instanced(RenderUpdateGroup):
    def __init__(self, shader="DefaultInstancedShader", visible=True, depth_write=True):
        self.changed_vbo_lists = set()
        super().__init__(shader, visible, depth_write)

    @staticmethod
    def _get_object_key(obj):
        return obj.vbo

    def _add_one(self, obj, key):
        uid = obj.UID
        second_key = obj.curr_image().key

        if key not in self.objects.keys():
            self.objects[key] = {}
        if second_key not in self.objects[key].keys():
            self.objects[key][second_key] = []

        self.objects[key][second_key].append( obj )
        return uid

    def draw_all(self, object_ids=()):
        """
        to_draw:: Set of Physic Objects body hash, that should be rendered
        If None, all object will be rendered"""
        if not self.pre_draw(): return

        for vbo, objects_by_tex in self.objects.items():
            tex_slot = 0
            objects_added = 0

            for tex, objects in objects_by_tex.items():
                glActiveTexture(GL_TEXTURE0 + tex_slot)
                glBindTexture(GL_TEXTURE_2D, tex)
                self.shader.passTexture(f"Textures[{tex_slot}]", tex_slot)

                Transform = np.asfortranarray( [obj.get_transform() for obj in objects], dtype=FLOAT32)
                self.shader.passMat4V(f"Transform[{objects_added}]", Transform)
                InstanceTex = np.asfortranarray( [tex_slot for _ in range(len(objects))], dtype=UINT )
                self.shader.passUIntV(f"InstanceTex[{objects_added}]", InstanceTex)

                tex_slot += 1
                objects_added += len(objects)

            glBindBuffer(GL_ARRAY_BUFFER, vbo)
            self.shader.prepareDraw()
            glDrawElementsInstanced(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None, objects_added)


class RenderUpdateGroup_Materials(RenderUpdateGroup):
    def __init__(self, shader="DefaultMaterialShader", visible=True, depth_write=True):
        super().__init__(shader, visible, depth_write)

    def add(self, *objs: [T_RENDER_OBJECT, ]):
        """You can redefine how objects are added and how they are sorted
        by changing _get_object_key and _add_one of child classes"""
        for obj in objs:
            uid = obj.UID
            self.objects[uid] = obj
            if hasattr(obj, "update"): self.updatable[uid] = obj

    def draw_all(self, object_ids=None):
        if not self.pre_draw(): return
        Ems.bind()

        Transform = []
        Scales = []
        Layers = []

        obj = None
        for uid, obj in self.objects.items():
            Transform.append( obj.get_transform() )
            Scales.append( obj.scale )
            Layers.append( obj.tex_layer )

        if not obj: return
        obj_count = len(Transform)

        Transform = np.asfortranarray(Transform, dtype=FLOAT32)
        self.shader.passMat4V(f"Transform[0]", Transform)

        Scales = np.asfortranarray(Scales, dtype=FLOAT32)
        self.shader.passVec2fV(f"Scale[0]", Scales)

        Layers = np.asfortranarray(Layers, dtype=FLOAT32)
        self.shader.passUIntV(f"Layer[0]", Layers)

        glBindBuffer(GL_ARRAY_BUFFER, obj.vbo)
        self.shader.prepareDraw()
        glDrawElementsInstanced(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None, obj_count)


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
class RenderObject:
    """Base render object.
    Provides possibility for drawing given texture: GLTexture within given rect: Rect4f
    For :args info check in __init__"""

    # public
    visible = True
    group: Union["RenderUpdateGroup", "RenderUpdateGroup_Instanced"]

    _size: tuple = None
    _colors: np.array = [ np.array([1.0, 1.0, 1.0, 1.0], dtype=np.float32) for _ in range(4) ]
    _vbo: int = 0

    _y_rotation: int
    _scaleX: FLOAT32
    _scaleY: FLOAT32

    _UID: int = 0  # It will be auto set if object is InGameObject's child

    def __init__(self, group, size=None, orientation=1, drawdata='auto', layer=5, instanced=False):
        # if False object wont be rendered
        self.visible = True

        #  -1 for left   1 for right
        self._y_rotation = INT64( orientation )
        if drawdata != "auto" and instanced:
            instanced = False
            warnings.warn("You can not use instanced rending with given drawdata")
        self._instanced = instanced
        self._size = size if size else self.__class__._size
        self._layer = layer

        if instanced:  # Instanced rendering
            if not self.__class__._vbo:  # If there is VBO for this type of objects, this instance will use ready VBO
                self.__class__._vbo = self.bufferize()
            self._vbo = self.__class__._vbo

        else:
            if drawdata == "auto":
                self.bufferize()
            else:
                self.bufferize_given_drawdata(drawdata)

        if group is not None:
            group.add(self)
        self.group = group

        self._scaleX = FLOAT32( 1.0 )
        self._scaleY = FLOAT32( 1.0 )

    def __repr__(self):
        return f'<{self.__class__.__name__}>'

    def bufferize(self, vbo=None):
        """
        y_rotation::if None, then object will be bufferized as it have y_rotation
        vbo::if given, object won't change, but save its new VBO data to given <vbo>
        """
        drawdata = drawData(self._size, self._colors, layer=self._layer)
        if vbo is None:
            self._vbo = bufferize(drawdata, self._vbo)
            return self._vbo
        else:
            return bufferize(drawdata, vbo)

    def bufferize_given_drawdata(self, drawdata, vbo=None):
        if vbo is None:
            self._vbo = bufferize(drawdata, self._vbo)
            return self._vbo
        else:
            return bufferize(drawdata, vbo)

    # DELETE
    def delete(self):
        glBindBuffer(GL_ARRAY_BUFFER, self._vbo)
        glBufferData(GL_ARRAY_BUFFER, 0, None, GL_STATIC_DRAW)
        glDeleteBuffers(1, np.array(self._vbo, ))
        if self.group is not None:
            self.group.remove(self)

    def get_transform(self) -> TYPE_MAT:
        """Redefined in child classes"""
        pass

    def draw_single(self, shader):
        """Draws only this object to screen, using one draw call"""
        if not self.visible: return

        glBindBuffer(GL_ARRAY_BUFFER, self._vbo)
        shader.prepareDraw(camera=camera, transform=self.get_transform(), fbuffer=FB_Geometry)
        glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None)

    @property
    def vbo(self):
        return self._vbo

    @property
    def scale(self):  # Dynamic
        return [self._scaleX, self._scaleY]

    @scale.setter
    def scale(self, value: Union[TYPE_VEC, list, tuple]):
        self._scaleX = FLOAT32( value[0] )
        self._scaleY = FLOAT32( value[1] )

    def set_color(self, new_color, vertex=None):
        """
        It is not recommended to use this on Instanced objects
        """

    @property
    def orientation(self):
        return self._y_rotation

    @orientation.setter
    def orientation(self, new_rotation: Union[int, INT64]):
        if not new_rotation: return
        assert abs(new_rotation) == 1
        if self._y_rotation == new_rotation: return
        self._y_rotation = INT64(new_rotation)


class RenderObjectPlaced(RenderObject):
    """Alternative for RenderObjectPhysic
    This object will be rendered in place, taken from self.pos"""

    def __init__(
            self,
            group, pos, size=None, orientation=1, drawdata='auto', layer=5, instanced=False
    ):
        super().__init__(group, size, orientation, drawdata, layer, instanced)
        self.rect = Rect4f(*pos, *self.__class__._size if not size else size)

    def __repr__(self):
        return f'<ROP: {super().__repr__()}' \
               f'_vbo:{self._vbo}' \
               f'_texture:{self.curr_image() if hasattr(self, "curr_image") else None}>'

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

    def get_transform(self):
        x_, y_ = self.rect.pos
        return lin.FullTransformMat(
            x_, y_, camera.get_matrix(), FLOAT32(0), self._y_rotation, self._scaleX, self._scaleY
        )


class RenderObjectPhysic(RenderObject):
    """Alternative for RenderObjectPlaced
    This object will be rendered in place, taken from its physic body pos (self.body.pos)
    It will also take orientation from physic body"""

    def __init__(
            self,
            group, body, size=None, orientation=1, drawdata='auto', layer=5, instanced=False
    ):
        super().__init__(group, size, orientation, drawdata, layer, instanced)
        self.body = body

    def __repr__(self):
        return f'<ROP: {super().__repr__()}' \
               f'_vbo:{self._vbo}' \
               f'_texture:{self.curr_image() if hasattr(self, "curr_image") else None}>'

    @property
    def z_rotation(self):
        return lin.degreesFromNormal(self.body.rotation_vector)

    def get_transform(self):
        x_, y_ = self.body.pos_FLOAT32
        return lin.FullTransformMat(
            x_, y_, camera.get_matrix(), FLOAT32(-self.z_rotation), self._y_rotation, self._scaleX, self._scaleY
        )


# RENDER COMPONENT
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


class MaterialRenderComponent:
    _material: INT64

    @property
    def tex_layer(self):
        return self._material

    def initialize(self, material_texture, material_preset=None):
        preset, self._material = Ems.get(material_preset, material_texture)
        return preset


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
            obj.orientation(rotation)

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
        size = STN_WINDOW_RESOLUTION

        self.key = glGenFramebuffers(1)
        glBindFramebuffer(GL_FRAMEBUFFER, self.key)

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
        clearDisplay()

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
        size = STN_WINDOW_RESOLUTION
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


FB_Geometry: FrameBufferDepth
FB_Lighting: FrameBuffer
LightingManager: __LightingManager


# DISPLAY
def initDisplay(size=STN_WINDOW_RESOLUTION):
    global camera, FB_Geometry, FB_Lighting, FIRST_EBO, LightingManager

    #  Display flags
    flags = pygame.OPENGL | pygame.DOUBLEBUF | pygame.HWSURFACE | pygame.SRCALPHA
    flags = flags | pygame.FULLSCREEN if FULL_SCREEN else flags
    pygame.display.set_mode(size, flags=flags)
    
    #  OpenGL Version requirement
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 4)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 0)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)

    #  Initialize render engine modules
    Shaders.init()
    LightingManager = __LightingManager()

    #  Preparing frame buffers
    FB_Geometry = FrameBufferDepth()
    FB_Lighting = FrameBuffer()
    clearDisplay()

    #  Initializing camera
    camera = Camera()

    #  Setting up GL states
    glClearColor(*clear_color)
    glDepthFunc(GL_LEQUAL)

    glScissor(0, 0, *WINDOW_SIZE)
    glEnable(GL_SCISSOR_TEST)

    setDefaultBlendFunc()
    glEnable(GL_BLEND)

    # Order of vertexes when drawing
    setupIndices()


def setupIndices():
    global FIRST_EBO

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


def bindEBO(offset=0):
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, FIRST_EBO + offset)


def preRender(do_depth_test=True):
    # MY FRAME BUFFER
    camera.prepare_matrix()
    FB_Geometry.bind()

    if do_depth_test:
        glEnable(GL_DEPTH_TEST)


def drawGroupsFinally(object_ids, *groups):
    # THE ONLY WAY TO DRAW ON SCREEN
    # Drawing each object in each group

    for group in groups:
        group.draw_all(object_ids)


def renderLights(camera_, ):
    lm = LightingManager
    if not lm.do_render:
        return

    shader = lm.shader
    glBlendFunc(GL_ONE, GL_ONE)
    glDisable(GL_DEPTH_TEST)

    FB_Lighting.bind()
    shader.use()

    light_groups = lm.generate_groups()
    previous_tex = -1
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
    setDefaultBlendFunc()


def postRender(screen_shader):
    """screen shader - Shader from Shaders module with 'ScreenShader' prefix
    Shader that will be used to render full scene to screen"""

    # MY FRAME BUFFER
    fbuff = FB_Geometry
    lbuff = FB_Lighting

    # DEFAULT FRAME BUFFER
    renderLights(camera)
    clearDisplay()

    screen_shader.use()
    glBindBuffer(GL_ARRAY_BUFFER, fbuff.vbo)
    glDisable(GL_DEPTH_TEST)
    screen_shader.prepareDraw()

    # DRAW SCENE AND GUI
    fbuff.bind_texture(0)        # bind scene texture
    lbuff.bind_texture(1)        # bind light texture
    fbuff.bind_depth_texture(2)  # bind depth texture
    glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None)


def clearDisplay():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)


def clearDepth():
    glClear(GL_DEPTH_BUFFER_BIT)


def setDefaultBlendFunc():
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
