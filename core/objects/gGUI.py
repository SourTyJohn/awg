from core.rendering.PyOGL import StaticRenderComponent
from core.rendering.Textures import EssentialTextureStorage as Ets


class GUIHeroHealthBar(StaticRenderComponent):
    TEXTURES = (Ets['GUI/ingame_health_bar'], )
    size = (800, 64)
