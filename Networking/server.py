import socket
import json
from collections import namedtuple

import Networking.network_packets as np

class Server():
    """Server class"""

    clients: list = []

    IDs: int = 0

    currentPort: int = 0

    def __init__(self, port, timeout: int):
        self.sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.sock.bind(('localhost', port))
        self.sock.settimeout(timeout)
        self.currentPort = port
        self.sock.setblocking(True)
        # self.sock.setblocking(False)
        # self.sock.listen(MaxPlayersRecive)

    def __del__(self):
        NPacket = np.NET_Packet(None, np.FORCE_DISCONNECT)
        self.BroadCoast(NPacket)
        self.sock.close()

    def ListenPort(self):
        try:
            data, address = self.sock.recvfrom(1024)
            
            dict_str = data.decode("UTF-8")
            NPacket_dict = json.loads(dict_str)
            NPacket = namedtuple("NET_Packet", NPacket_dict.keys())(*NPacket_dict.values())

            if NPacket.type == np.CONNECT:
                print("Another client connected")
                self.clients.insert(self.IDs, address)
                self.IDs += 1

                NPacket = np.NET_Packet(None, np.CONNECTION_ACCEPTED)
                self.SendPacket(address, NPacket)

            elif NPacket.type == np.SYNC:
                # We sync in game.py
                pass

            return NPacket

        except socket.timeout:
            print("Packet lost")

    def Update():
        pass

    def BroadCoast(self, packet):
        for i, ii in enumerate(self.clients):
            self.SendPacket(self.clients[i], packet)

    def SendPacket(self, address, packet: np.NET_Packet):
        np_dict = dict(packet)
        self.sock.sendto(json.dumps(np_dict).encode("UTF-8"), address)