from core.rendering.PyOGL import RenderObjectStatic
from core.rendering.Textures import EssentialTextureStorage as Ets


class GUIHeroHealthBar(RenderObjectStatic):
    TEXTURES = (Ets['GUI/ingame_health_bar'], )
    size = (800, 64)
