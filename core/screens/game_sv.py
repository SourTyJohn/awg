from core.physic.Physics import new_triggers, WorldInterface
import core.physic.Physics as Phys

from core.Objects.GameObjects import *

from Networking.server import Server
from Networking.client import Client

import Networking.network_packets as np

# Server defines
IS_DEDICATED: bool
IS_SERVER: bool
DEFAULT_PORT = 30576

sv: Server
cl: Client

hero_inited = False
hero: MainHero  # MainHero object
heroCl: MainHeroCl # Cl main hero

#  Keys that player is holding
holding_keys = {
    K_MOVE_RIGHT: False,
    K_MOVE_LEFT: False,
    K_MOVE_UP: False,
    K_MOVE_DOWN: False
}


def update(dt):
    # USER EVENTS
    exit_code = user_input()
    if exit_code:
        return exit_code

    # PHYSIC AND UPDATE (VAX: WE ADD "IS SERVER")
    global IS_SERVER
    if IS_SERVER:
        Phys.worldInterface.GetWorld().step(dt)

    """new_triggers - set of Trigger objects from Physics.py,
    that were added recently and needs to be added to object group
    Physic.py module can't access object groups from game module
    so it pass new triggers through new_triggers set, to add it to group here"""
    #while new_triggers:
    #    triggers_gr.add(new_triggers.pop())

    #update_groups(dt)

    sv.ListenPort()
    sv.BroadCoast(np.SYNC)

def init_screen(hero_life=False, first_load=False, is_server=False, is_dedicated=False):

    InitNET()

    global hero, hero_inited

    WorldRectangleRigid(obstacles_gr, pos=[0, 500], size=[4100, 100])
    WorldRectangleRigid(obstacles_gr, pos=[850, 700], size=[200, 200])

    a = WorldRectangleRigid(obstacles_gr, pos=[-500, 575], size=[800, 50])
    a.bfriction = 0.0

    WorldRectangleRigid(obstacles_gr, pos=[1600, 1200], size=[50, 900])
    WorldRectangleRigid(obstacles_gr, pos=[2000, 1000], size=[50, 900])

    MetalCrate(obstacles_gr, pos=[700, 800])
    hero = MainHero(player_gr, pos=[500, 800])


def close():
    DeinitNET()

def InitNET():
    
    global sv

    sv = Server(DEFAULT_PORT, 0.05)

    Phys.worldInterface = WorldInterface(True)

def DeinitNET():
    global sv
    del sv
