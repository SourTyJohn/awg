# from core.rendering.Textures import EssentialTextureStorage, DynamicTextureStorage
# from core.rendering.PyOGL import GlTexture
# Ets, Dts = EssentialTextureStorage, DynamicTextureStorage
#
#
# MaterialStorage = {}
#
#
# class Material:
#     """ Texture for Physical Body with mass and other physical params.
#     All material are loaded with starting the game and stored in MaterialStorage. """
#
#     texture: GlTexture
#
#     unit_mass: int
#     friction: int
#     bouncy: int
#
#     def __init__(self, texture, unit_mass, friction, bouncy):
#         self.texture = texture
#         self.unit_mass = unit_mass
#         self.friction = friction
#         self.bouncy = bouncy
#
#         MaterialStorage[texture.name] = self
#
#
# Material(Ets['LevelOne/r_pebble_grass_1'], 1, 1, 1)
