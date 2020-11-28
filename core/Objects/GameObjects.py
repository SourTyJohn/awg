"""
THIS MODUlE CONTAINS ALL GAME OBJECTS THAT CAN BE USED IN GAME (screens.game)
"""

from core.physic.Physics import GameObjectFixed, GameObjectDynamic, Hitbox, LimitedVector2f, Vector2f
from core.rendering.Textures import EssentialTextureStorage as Ets
from pygame.sprite import Sprite


fixed = GameObjectFixed
dynamic = GameObjectDynamic


class DirectAccessObject:
    rect = None

    def __repr__(self):
        return f'<Direct obj: {self.__class__.__name__}> at pos: {self.rect[:2]}'


"""Direct access means that object complete and ready to be placed on level"""
d = DirectAccessObject


class Mortal:
    lethal_fall_velocity: int = -1
    # [y] velocity that will cause calling die()
    # if set to -1, object can not get damage from falling
    # if velocity[y] >= lethal_fall_velocity // 4 -> damage

    health: int
    max_health: int

    stamina: int
    max_stamina: int

    def init_mortal(self, cls, health='max'):
        if health == 'max':
            self.health = cls.max_health

    def fell(self, power):
        if self.lethal_fall_velocity == -1:
            return

        damage = abs(power / self.lethal_fall_velocity)

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


"""Mortal means that object have .health: int and if .health <= 0 object will .die()
   Apply this to every destructable object """
m = Mortal


class WorldRectangleRigid(fixed):
    # This class represents base level geometry with rigid body

    TEXTURES = Ets

    def __init__(self, gr, pos, size, tex_offset=(0, 0), texture='Devs/r_devs_1'):
        hitbox = Hitbox([0, 0], size)
        super().__init__(gr, pos, size=size, tex_offset=tex_offset, texture=texture, hitbox=hitbox)


class Background(Sprite):
    pass


class Character(dynamic):
    WALKING_SPEED = 0

    def __init__(self, max_walking_speed, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.walkVelocity = LimitedVector2f(0, 0, max_walking_speed)

        self.walk_direction = 0  # may be -1 - move to  the left, 0 - standing, 1 - move to the right
        self.walking_speed = self.__class__.WALKING_SPEED

        self.grab_distance = 60
        self.grabbed_object = None

    def walk(self, direction):
        self.walkVelocity.add(direction)

    def _doMove(self, dt):
        move_vector = self.velocity.sum(self.walkVelocity)
        self.move_by(move_vector * dt)

    def getVelocity(self):
        return self.velocity.sum(self.walkVelocity)

    def friction_apply(self, dt, k):
        self.velocity.friction(k * dt)
        self.walkVelocity.friction(k * dt)

    def update(self, *args, **kwargs) -> None:
        #  args[0] - delta_time
        self.walk(Vector2f.xy(self.walking_speed * self.walk_direction * args[0], 0))

        #  grabbed object update
        if self.grabbed_object:
            pass

    def grab(self, target):
        self.grabbed_object = object

#


class MainHero(Character, d, m):
    # unique
    MAX_JUMPS = 2
    WALKING_SPEED = 2
    JUMP_VECTOR = Vector2f.xy(0, 36)
    MANY_JUMPS_DELAY = 12

    # character
    MAX_WALKING_SPEED = 16

    #  static
    TEXTURES = [Ets['LevelOne/r_pebble_grass_1'], ]
    size = [64, 144]
    hitbox = Hitbox([0, 0], size)

    #  dynamic
    mass = 2

    #  mortal
    max_health = 200
    lethal_fall_velocity = 256

    #  Main Hero is Singleton. __instance stores only MainHero object
    __instance = None

    def __init__(self, gr, pos):
        super().__init__(MainHero.MAX_WALKING_SPEED, gr, pos, MainHero.size)

        self.jumps = 0
        self.jump_delay_current = 0

        self.init_mortal(self.__class__)

    def __new__(cls, *args, **kwargs):
        if cls.__instance:
            cls.__instance.delete()
        cls.__instance = super(MainHero, cls).__new__(cls)
        return cls.__instance

    def update(self, *args, **kwargs):
        # args[0] - delta time

        # jump delay update
        if self.jump_delay_current < MainHero.MANY_JUMPS_DELAY:
            self.jump_delay_current += args[0]

        # character.update()
        super().update(*args, **kwargs)

    def jump(self):
        if self.jumps < MainHero.MAX_JUMPS and self.jump_delay_current >= MainHero.MANY_JUMPS_DELAY:

            self.addVelocity(MainHero.JUMP_VECTOR)
            self.jumps += 1
            self.jump_delay_current = 0

    def fell(self):
        Mortal.fell(self, self.velocity[1])
        self.jumps = 0

    def addVelocity(self, vector):
        super().addVelocity(vector)


class WoodenCrate(dynamic, d, m):
    # static
    TEXTURES = [Ets['LevelOne/r_tile_grey_1'], ]
    size = [64, 64]
    hitbox = Hitbox([0, 0], size)

    # dynamic
    mass = 1

    # mortal
    max_health = 10
    lethal_fall_velocity = 64

    def __init__(self, gr, pos):
        super().__init__(gr, pos, WoodenCrate.size, max_velocity=64)
        self.init_mortal(self.__class__)

    def fell(self):
        Mortal.fell(self, self.velocity[1])


class MetalCrate(WoodenCrate, d, m):
    TEXTURES = [Ets['LevelOne/r_orange_bricks_1'], ]
    mass = 10


#


"""Storage of all Direct objects. Can be accessed by WorldEditor, LevelLoader and create_object() function"""
allObjects = {}


for x in DirectAccessObject.__subclasses__():
    allObjects[x.__name__] = x
