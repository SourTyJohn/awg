from utils.files import load_map

MAX_GAME_CONTEST_IDS = 65_536


class GameContext:
    """
    object id
    NRT-like int
    N - is id taken from _free_ids
    T - type of object: 0 - physic,

    """

    _objects: dict
    _to_update_ids: tuple


def loadMap():
    pass
