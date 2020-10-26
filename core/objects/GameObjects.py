from core.physic.Physics import GameObjectFixed, Hitbox
from core.rendering.Textures import EssentialTextureStorage as Ets


class WorldRectangle(GameObjectFixed):
    textures = Ets

    friction = 1
    bouncy = 1

    def __init__(self, gr, pos, size, tex_offset=(0, 0), texture='Devs/r_devs_1'):
        super().__init__(gr, pos, size=size, tex_offset=tex_offset, texture=texture)


#
# class MainHero(GameObject):
#     dynamic = True
#     hitbox = Hitbox([0, 0], [64, 144])
#
#     def __init__(self, group, rect):
#         super().__init__(group, rect)
