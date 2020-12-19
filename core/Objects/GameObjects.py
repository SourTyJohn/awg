"""
THIS MODUlE CONTAINS ALL GAME OBJECTS THAT CAN BE USED IN GAME (screens.game)
"""

from core.physic.Physics import DynamicObject, StaticObject, Trigger
from core.rendering.PyOGL import GLObjectBase
from core.rendering.Textures import EssentialTextureStorage as Ets
from core.Constants import WINDOW_SIZE

from pymunk.vec2d import Vec2d
from pymunk import inf

import numpy as np

fixed = StaticObject
dynamic = DynamicObject
base = GLObjectBase

class DirectAccessObject:
    """Direct access means that object complete and ready to be placed on level
       Subclasses of this class will be added to allObjects dict"""
    rect = None

    def __repr__(self):
        return f'<Direct obj: {self.__class__.__name__}> at pos: {self.rect[:2]}'

d = DirectAccessObject

class WorldRectangleRigid(fixed):
    # This class represents base level geometry with rigid body

    #TEXTURES = Ets

    def __init__(self, gr, pos, size, tex_offset=(0, 0), texture='Devs/r_devs_1'):
        hitbox = (0, 0, *size)
        super().__init__(gr, pos, collision_type='obstacle', size=size,
                         tex_offset=tex_offset, texture=texture, hitbox=hitbox)

class WorldRectangleRigidCl(fixed, base):
    # This class represents base level geometry with rigid body

    TEXTURES = Ets

    def __init__(self, gr, pos, size, tex_offset=(0, 0), texture='Devs/r_devs_1'):
        hitbox = (0, 0, *size)
        super().__init__(gr, pos, collision_type='obstacle', size=size,
                         tex_offset=tex_offset, texture=texture, hitbox=hitbox)
        base.__init__(self, gr, rect=[*pos, *size], tex_offset=tex_offset)
        self.setTexture(texture)

class BackgroundColor(GLObjectBase):
    # Texture is not actually visible. Only color
    TEXTURES = (Ets['Devs/error'], )

    # BackgroundColor
    color: np.array = [0.35, 0.35, 0.5, 1.0]

    # Singleton
    __instance = None

    def __init__(self, gr):
        self.texture = 0
        super().__init__(gr, rect=[0, 0, *WINDOW_SIZE], color=BackgroundColor.color)

    def __new__(cls, *args, **kwargs):
        cls.__instance = super(BackgroundColor, cls).__new__(cls)
        return cls.__instance

    def update(self, *args, **kwargs) -> None:
        # args[1] - camera
        self.rect.pos = args[1].getPos()

class Mortal:
    """Mortal means that object have .health: int and if .health <= 0 object will .die()
       Apply this to every DESTRUCTABLE OBJECT"""

    lethal_fall_velocity: int = -1
    """[y] velocity that will cause calling die()
    if set to -1, object can not get damage from falling
    if velocity[y] >= lethal_fall_velocity // 4 -> damage"""

    # health
    health: int
    max_health: int

    # stamina
    stamina: int
    max_stamina: int

    def init_mortal(self, cls, health='max'):
        """You need to call this in constructor of subclasses
        to fully integrate Mortal functionality"""
        if health == 'max':
            self.health = cls.max_health

    def update(self, *args, **kwargs):
        pass

    def fall(self, vec):
        if self.lethal_fall_velocity == -1:
            return

        damage = abs(vec.length / self.lethal_fall_velocity)

        if damage < 0.35:
            return

        damage = round(damage ** 2 * self.max_health)
        self.get_damage(damage)

    def get_damage(self, amount):
        self.health -= amount
        if self.health <= 0:
            self.die()

    def die(self):
        pass

m = Mortal

class Character(dynamic, base):
    MAX_JUMPS = 2
    WALKING_VEC = 0
    JUMP_VECTOR = Vec2d(0, 0)
    MANY_JUMPS_DELAY = 12
    MAX_WALKING_SPEED = 0
    IN_AIR_MOVE = 0.8  # sec

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Walking, Running
        self.walk_direction = 0  # may be -1 - move to  the left, 0 - standing, 1 - move to the right
        self.walking_vec = self.__class__.WALKING_VEC
        self.max_walking_speed = self.__class__.MAX_WALKING_SPEED

        # Jumping
        self.jumps = 0
        self.jump_delay_current = 0
        self.max_jumps = self.__class__.MAX_JUMPS
        self.many_jump_delay = self.__class__.MANY_JUMPS_DELAY
        self.jump_vec = self.__class__.JUMP_VECTOR

        # Grab
        self.grab_distance = 60
        self.grabbed_object = None

        # Blocks rotation. Characters stand on their feet
        self.body.moment = inf

        # Standing on ground trigger
        self.on_ground_trigger = Trigger(self.touch_ground, 'trigger_obstacle', self.untouch_ground,
                                         bound_to=self, offset=(0, -self.size[1] // 2), size=(self.size[0] // 2 - 1, 6))
        self.on_ground = False  # is Character standing on solid floor
        self.in_air = 0  # How long din't Character touch solid flour

    def update(self, *args, **kwargs) -> None:
        dt = args[0]

        super().update(*args, **kwargs)

        # Grabbed object update
        if self.grabbed_object:
            pass

        if not self.on_ground:
            self.in_air += dt

        # Walking
        self.walk(dt)

    # Moving around
    def walk(self, dt):
        if not self.walk_direction or (self.body.velocity.length > self.max_walking_speed):
            return

        if self.on_ground:
            self.body.apply_force_at_local_point(
                self.walking_vec * self.walk_direction * dt, self.body.center_of_gravity)

        elif self.in_air < self.IN_AIR_MOVE:
            self.body.apply_force_at_local_point(
                self.walking_vec * self.walk_direction * dt * 0.2, self.body.center_of_gravity)

        # self.rotY(self.walk_direction)

    def jump(self):
        if self.jumps < self.max_jumps:
            self.body.apply_impulse_at_local_point(self.jump_vec)
            self.jumps += 1

    # Grabbed object
    def grab(self, target):
        #  TODO: GRAB
        self.grabbed_object = target

    # Legs Trigger
    def touch_ground(self, *args):
        # actor - ground, owner - self, world - world
        self.jumps = 0
        self.on_ground = True
        self.in_air = 0

    def untouch_ground(self, *args):
        if len(self.on_ground_trigger.entities) == 0:
            self.on_ground = False

class MainHero(Character, d, m):
    #  static
    TEXTURES = [Ets['LevelOne/r_pebble_grass_1'], ]
    size = (64, 144)
    hitbox_data = (0, 0, *size)
    friction = 2

    #  dynamic
    mass = 10.0

    # character
    JUMP_VECTOR = Vec2d(0, 700 * mass)
    WALKING_VEC = Vec2d(384_000 * mass, 0)
    MAX_WALKING_SPEED = 120 * mass

    #  mortal
    max_health = 200
    lethal_fall_velocity = 256

    #  Main Hero is Singleton. __instance stores only MainHero object
    __instance = None

    def __init__(self, gr, pos):
        Character.__init__(self, gr, pos, 'mortal', MainHero.size)
        self.init_mortal(self.__class__)

    def __new__(cls, *args, **kwargs):
        if cls.__instance:
            cls.__instance.delete()
        cls.__instance = super(MainHero, cls).__new__(cls)
        return cls.__instance

    def update(self, *args, **kwargs):
        # args[0] - delta time
        super().update(*args, **kwargs)

        # jump delay update
        if self.jump_delay_current < MainHero.MANY_JUMPS_DELAY:
            self.jump_delay_current += args[0]

#class MainHeroCl(CharacterCl, d, m, base):
class MainHeroCl(d, m, base):
    #  static
    TEXTURES = [Ets['LevelOne/r_pebble_grass_1'], ]
    size = (64, 144)
    hitbox_data = (0, 0, *size)
    friction = 2

    #  dynamic
    mass = 10.0

    # character
    JUMP_VECTOR = Vec2d(0, 700 * mass)
    WALKING_VEC = Vec2d(384_000 * mass, 0)
    MAX_WALKING_SPEED = 120 * mass

    #  mortal
    max_health = 200
    lethal_fall_velocity = 256

    #  Main Hero is Singleton. __instance stores only MainHero object
    __instance = None

    def __init__(self, gr, pos):
        #CharacterCl.__init__(self, gr, pos, 'mortal', MainHeroCl.size)
        base.__init__(self, gr, rect=[*pos, *self.size])
        self.init_mortal(self.__class__)

    def __new__(cls, *args, **kwargs):
        if cls.__instance:
            cls.__instance.delete()
        cls.__instance = super(MainHeroCl, cls).__new__(cls)
        return cls.__instance

    def update(self, *args, **kwargs):
        # args[0] - delta time
        vector = kwargs['pos']
        cur_pos = self.getPos()
        if cur_pos[0] == vector[0] and cur_pos[1] == vector[1]:
            #print("Curent pos and sv pos are same - do nothing")
            return
        self.move_to([vector[0], vector[1]])

        super().update(*args, **kwargs)
        # jump delay update
        #if self.jump_delay_current < MainHeroCl.MANY_JUMPS_DELAY:
        #    self.jump_delay_current += args[0]

class WoodenCrate(dynamic, d, m):
    # static
    TEXTURES = (Ets['LevelOne/r_tile_grey_1'], )
    size = (64, 64)
    hitbox_data = (0, 0, *size)

    # dynamic
    mass = 4.0

    # mortal
    max_health = 10
    lethal_fall_velocity = 64

    def __init__(self, gr, pos):
        super().__init__(gr, pos, collision_type='mortal', size=self.__class__.size)
        print("Created Crate on SV")
        self.init_mortal(self.__class__)
        
class WoodenCrateCl(d, m, base):
    # static
    TEXTURES = (Ets['LevelOne/r_tile_grey_1'], )
    size = (64, 64)
    hitbox_data = (0, 0, *size)

    # dynamic
    mass = 4.0

    # mortal
    max_health = 10
    lethal_fall_velocity = 64

    def __init__(self, gr, id, pos):
        # super().__init__(gr, pos, collision_type='mortal', size=self.__class__.size)
        base.__init__(self, gr, rect=[*pos, *self.size])
        self.id = id
        print(f"Created Crate on CL with id {self.id}")
        self.init_mortal(self.__class__)

    def update(self, *args, **kwargs):
        # args[0] - delta time
        objects = kwargs['objs']
        if objects == []:
            return
        Pos = objects[self.id]

        cur_pos = self.getPos()
        if cur_pos[0] == Pos[0] and cur_pos[1] == Pos[1]:
            #print("Curent pos and sv pos are same - do nothing")
            return
        self.move_to([vector[0], vector[1]])

        self.move_to([Pos[0], Pos[1]])

class MetalCrate(WoodenCrate, d, m):
    # static
    TEXTURES = (Ets['LevelOne/r_orange_bricks_1'], )
    size = (128, 128)
    hitbox_data = (0, 0, *size)

    # dynamic
    mass = 60.0

    # mortal
    max_health = 32

class MetalCrateCl(WoodenCrateCl, d, m):
    # static
    TEXTURES = (Ets['LevelOne/r_orange_bricks_1'], )
    size = (128, 128)
    hitbox_data = (0, 0, *size)

    # dynamic
    mass = 60.0

    # mortal
    max_health = 32


"""Storage of all Direct objects. Can be accessed by WorldEditor, LevelLoader and create_object() function"""
allObjects = {}

for x in DirectAccessObject.__subclasses__():
    allObjects[x.__name__] = x
