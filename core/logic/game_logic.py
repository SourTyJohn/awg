MAX_GAME_CONTEST_IDS = 65_536


class GameContext:
    """
    object id
    T
    """

    _free_ids: tuple
    _objects: dict

    _to_update_ids: tuple

