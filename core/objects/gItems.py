from core.rendering.TextRender import LocalizedText

"""
# DroppedItem class in gObjects

ITEM TYPES
0 - key
1 - usable
2 - consumable
3 - equipment

EQUIP SLOTS
0 - armor
1 - weapon
2 - trinket
"""


"""
    [INVENTORY]
"""


class InventoryAndItemsManager:
    all_items: dict  # item id: item class
    hero_inventory: dict  # item id: [int amount, bool is_equipped]

    def __init__(self):
        self.all_items = {}
        for x in GameItem.__subclasses__():
            x._name = LocalizedText(f"item_{x.__name__}")
            x._description = LocalizedText(f"item_des_{x.__name__}")
            self.all_items[x.__name__] = x
        self.hero_inventory = {}

    def itemClass(self, item_id: str):
        return self.all_items[item_id]

    def heroGetItem(self, item_id: str):
        if item_id in self.hero_inventory.keys():
            self.hero_inventory[item_id] += 1
        else:
            self.hero_inventory[item_id] = 1

    def heroLostItem(self, item_id: str):
        if self.hero_inventory[item_id] == 1:
            del self.hero_inventory[item_id]
        else:
            self.hero_inventory[item_id] -= 1


"""
    [INVENTORY ITEMS]
"""


class InventoryItem:
    item_type: int
    """Item with no functionality"""
    cost: int  # if cost == -1, item can not be sold
    icon: str

    _name: LocalizedText
    _description: LocalizedText

    @property
    def name(self):
        return self._name()

    @property
    def description(self):
        return self._description()


class KeyItem(InventoryItem):
    item_type = 0


class UsableItem(InventoryItem):
    item_type = 1

    def use(self, actor):
        pass


class ConsumableItem(UsableItem):
    #  deletes itself after use
    item_type = 2

    def use(self, actor):
        pass


class EquipmentItem(InventoryItem):
    item_type = 3
    equip_slot: int

    def equip(self, actor):
        pass


class Armor(EquipmentItem):
    equip_slot = 0


class Weapon(EquipmentItem):
    equip_slot = 1
    animations: list
    damage: int


class Trinket(EquipmentItem):
    equip_slot = 2


class GameItem:
    """This mark means that marked item is ready to in game use
    Items without this mark can not be used in game"""
    pass


"""
    [ITEM CLASSES]
"""


class RustySword(Weapon, GameItem):
    cost = 5
    icon = 'Item/test_sword'


InventoryAndItemsManager = InventoryAndItemsManager()
