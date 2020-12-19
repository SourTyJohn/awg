from core.physic.Physics import new_triggers, WorldInterface
import core.physic.Physics as Phys

from core.rendering.PyOGL import camera, GLObjectGroupRender, drawGroups

from user.KeyMapping import *

from core.Objects.GameObjects import *

from Networking.server import Server
from Networking.client import Client
import Networking.network_packets as np

import copy
import threading
import time

import pygame
from pymunk.vec2d import Vec2d

background_gr = GLObjectGroupRender(g_name='g_background', shader='BackgroundShader')
obstacles_gr = GLObjectGroupRender(g_name='g_obstacle')
characters_gr = GLObjectGroupRender(g_name='g_characters')
player_gr = GLObjectGroupRender(g_name='g_player')

triggers_gr = GLObjectGroupRender(g_name='g_triggers')

# Server defines
IS_DEDICATED: bool
IS_SERVER: bool
DEFAULT_PORT = 30576

sv: Server
cl: Client

hero_inited = False
hero: MainHero  # MainHero object
heroSvPos: Vec2d
heroCl: MainHeroCl # Cl main hero

scene = []
sceneRecive = []

backward_user_move: int = 0

#  Keys that player is holding
holding_keys = {
    K_MOVE_RIGHT: False,
    K_MOVE_LEFT: False,
    K_MOVE_UP: False,
    K_MOVE_DOWN: False
}

def render():
    camera.focusTo(*heroCl.getPos())
    background_gr.update(1, camera)
    draw_groups()

def render_dedicated():
    pass

def update(dt):
    # USER EVENTS
    if not IS_DEDICATED:
        exit_code = user_input()
        if exit_code:
            return exit_code

    """new_triggers - set of Trigger objects from Physics.py,
    that were added recently and needs to be added to object group
    Physic.py module can't access object groups from game module
    so it pass new triggers through new_triggers set, to add it to group here"""
    while new_triggers:
        triggers_gr.add(new_triggers.pop())

    #if not IS_DEDICATED and not t.is_alive():
    #    t = threading.Timer(0.5, Sync)
    #    t.start()
    #    t.join()
    #else:
    #    t = threading.Timer(0.5, Sync)
    #    t.start()
    #    t.join()

    if not IS_DEDICATED:
        update_groups(dt)

    # PHYSIC AND UPDATE (VAX: WE ADD "IS SERVER")
    if IS_SERVER:
        Phys.worldInterface.GetWorld().step(dt)

def Sync():
 while True:
    global sceneRecive, heroSvPos

    if IS_SERVER:
        vector = hero.getPos()
        packet = sv.ListenPort([scene, [vector.x, vector.y]])
        if packet.type == np.SYNC:
            for i in range(len(packet.Data)):
                if packet.Data[i][0] == 'move_hero':
                    if packet.Data[i][1] != 0:
                        print('WALK PACKET RECIVED')
                    hero.walk_direction = packet.Data[i][1]
                elif packet.Data[i][0] == 'jump':
                    print('JUMP PACKET RECIVED')
                    hero.jump()

    NPacket = np.NET_Packet([scene, [vector.x, vector.y]], np.SYNC)
    sv.BroadCoast(NPacket)

    time.sleep(0.2)

    NPacket = np.NET_Packet(None, np.YOU_ARE_HERE)
    sv.BroadCoast(NPacket)

    if not IS_DEDICATED:
        packet = cl.ListenPort()

        if packet.type == np.CONNECTION_ACCEPTED:
            sceneRecive = copy.deepcopy(packet.Data[0])
            heroSvPos = packet.Data[1]
        elif packet.type == np.YOU_ARE_HERE:
            NPacket = np.NET_Packet(None, np.YES)
            cl.SendPacket(NPacket)
        elif packet.type == np.SYNC:
            sceneRecive = packet.Data[0]
            heroSvPos = packet.Data[1]
    else:
        packet = cl.ListenPort()

        if packet.type == np.CONNECTION_ACCEPTED:
            # Here we need say somthing to server because server got stuck if we don't
            NPacket = np.NET_Packet(None, np.YES)
            cl.SendPacket(NPacket)
        elif packet.type == np.YOU_ARE_HERE:
            NPacket = np.NET_Packet(None, np.YES)
            cl.SendPacket(NPacket)
        elif packet.type == np.SYNC:
            pass
    time.sleep(0.05)

def user_input():
    global backward_user_move

    # USER INPUT
    SyncIds = 0

    commands_for_sv = []

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return 'Quit'

        elif event.type == pygame.KEYDOWN:
            key = event.key

            if key in holding_keys.keys():
                holding_keys[key] = True

            elif key == K_MOVE_JUMP:
                # NEED ID!
                commands_for_sv.insert(SyncIds+1, ['jump'])
                SyncIds =+ 1
                #cl.SendPacket(NPacket)

            elif key == pygame.K_q:
                cr = WoodenCrate(obstacles_gr, pos = hero.getPos())
                vector = cr.getPos()
                scene.insert(len(scene)+1, [vector.x, vector.y])
                WoodenCrateCl(obstacles_gr, id = len(scene)+1, pos = heroCl.getPos())

            elif key == K_CLOSE:
                close()
                return 'menu'

        elif event.type == pygame.KEYUP:
            key = event.key

            if key in holding_keys.keys():
                holding_keys[key] = False

    if not IS_DEDICATED:
        hero_movement = update_hero_movement()

        if hero_movement != backward_user_move:
            commands_for_sv.insert(SyncIds+1, ['move_hero', hero_movement])
            SyncIds =+ 1
            backward_user_move = hero_movement
        else:
            pass

        NPacket = np.NET_Packet(commands_for_sv, np.SYNC)
        cl.SendPacket(NPacket)

    return None

def update_hero_movement():
    if holding_keys[K_MOVE_RIGHT]:
        heroCl.walk_direction = 1
        return 1
    elif holding_keys[K_MOVE_LEFT]:
        heroCl.walk_direction = -1
        return -1
    else:
        heroCl.walk_direction = 0
        return 0

def draw_groups():
    # drawing all GLSprite groups
    drawGroups(background_gr, obstacles_gr, characters_gr, player_gr)

def update_groups(dt):    
    global sceneRecive
    # updating all GLSprite groups
    player_gr.update(dt, pos = heroSvPos)
    # Hero manualy update (I'm to lazy for solve this shit)
    hero.update(dt)
    obstacles_gr.update(dt, objs = sceneRecive )
    background_gr.update(dt, camera)
    triggers_gr.update(dt)

def init_screen(hero_life=False, first_load=False, is_server=False, is_dedicated=False):

    InitNET(is_server, is_dedicated)

    global hero, heroCl, heroSvPos, hero_inited, scene, sceneRecive

    BackgroundColor(background_gr)

    OBJs: int = 0

    if IS_SERVER:
        #CL & SV
        WorldRectangleRigid(obstacles_gr, pos=[0, 500], size=[4100, 100])
        WorldRectangleRigidCl(obstacles_gr, pos=[0, 500], size=[4100, 100])
        WorldRectangleRigid(obstacles_gr, pos=[850, 700], size=[200, 200])
        WorldRectangleRigidCl(obstacles_gr, pos=[850, 700], size=[200, 200])

        a = WorldRectangleRigid(obstacles_gr, pos=[-500, 575], size=[800, 50])
        WorldRectangleRigidCl(obstacles_gr, pos=[-500, 575], size=[800, 50])
        a.bfriction = 0.0

        WorldRectangleRigid(obstacles_gr, pos=[1600, 1200], size=[50, 900])
        WorldRectangleRigidCl(obstacles_gr, pos=[1600, 1200], size=[50, 900])
        WorldRectangleRigid(obstacles_gr, pos=[2000, 1000], size=[50, 900])
        WorldRectangleRigidCl(obstacles_gr, pos=[2000, 1000], size=[50, 900])

        mc = MetalCrate(obstacles_gr, pos=[700, 800])
        vector = mc.getPos()
        scene.insert(OBJs, [vector.x, vector.y])

        MetalCrateCl(obstacles_gr, OBJs, pos=[700, 800])
        OBJs += 1

        hero = MainHero(player_gr, pos=[500, 800])
        heroCl = MainHeroCl(player_gr, pos=[500, 800])
        heroSvPos = Vec2d(0, 0)
    else:
        #CL
        WorldRectangleRigidCl(obstacles_gr, pos=[0, 500], size=[4100, 100])
        WorldRectangleRigidCl(obstacles_gr, pos=[850, 700], size=[200, 200])

        a = WorldRectangleRigidCl(obstacles_gr, pos=[-500, 575], size=[800, 50])
        a.bfriction = 0.0

        WorldRectangleRigidCl(obstacles_gr, pos=[1600, 1200], size=[50, 900])
        WorldRectangleRigidCl(obstacles_gr, pos=[2000, 1000], size=[50, 900])

        MetalCrateCl(obstacles_gr, pos=[700, 800])
        heroCl = MainHeroCl(player_gr, pos=[500, 800])
        heroSvPos = Vec2d(0, 0)

def close():
    obstacles_gr.delete_all()
    triggers_gr.delete_all()
    DeinitNET()

def InitNET(IsConnect: bool, IsDedicated=False):
    
    global IS_DEDICATED, IS_SERVER, sv, cl

    IS_DEDICATED = IsDedicated

    if not IsConnect:
        sv = Server(DEFAULT_PORT, 0)
        IS_SERVER = True
    else:
        IS_SERVER = False
    
    cl = Client('localhost', DEFAULT_PORT, 0.1)

    Phys.worldInterface = WorldInterface(IS_SERVER)

    NPacket = np.NET_Packet(None, np.CONNECT)
    cl.SendPacket(NPacket)

    t = threading.Timer(0.5, Sync)
    t.start()

def DeinitNET():
    global cl, sv
    del cl
    del sv