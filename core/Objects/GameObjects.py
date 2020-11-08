from core.physic.Physics import GameObjectFixed, GameObjectDynamic, Hitbox, LimitedVector2f
from core.rendering.Textures import EssentialTextureStorage as Ets


class WorldRectangle(GameObjectFixed):
    textures = Ets

    friction = 1
    bouncy = 1

    def __init__(self, gr, pos, size, tex_offset=(0, 0), texture='Devs/r_devs_1'):
        hitbox = Hitbox([0, 0], size)

        super().__init__(gr, pos, size=size, tex_offset=tex_offset, texture=texture, hitbox=hitbox)


class Character(GameObjectDynamic):
    def __init__(self, max_walking_speed, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.walkVelocity = LimitedVector2f(0, 0, max_walking_speed)

    def walk(self, direction):
        self.walkVelocity.add(direction)

    def _doMove(self, dt):
        move_vector = self.velocity.sum(self.walkVelocity)
        self.move_by(move_vector)

    def getVelocity(self):
        return self.velocity.sum(self.walkVelocity)

    def _friction(self, dt, k):
        self.velocity.friction(k)
        self.walkVelocity.friction(k)


class MainHero(Character):
    textures = [Ets['LevelOne/r_pebble_grass_1'], ]

    mass = 40

    size = [64, 144]
    hitbox = Hitbox([0, 0], size)

    def __init__(self, gr, pos):
        super().__init__(16, gr, pos, MainHero.size)

    def draw(self, color=None):
        super().draw()

    def addVelocity(self, vector):
        super().addVelocity(vector)


class WoodenCrate(GameObjectDynamic):
    textures = [Ets['LevelOne/r_tile_grey_1'], ]

    mass = 10

    size = [64, 64]
    hitbox = Hitbox([0, 0], size)

    def __init__(self, gr, pos):
        super().__init__(gr, pos, WoodenCrate.size, max_velocity=20)
