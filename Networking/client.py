import socket
import json
from collections import namedtuple

import Networking.network_packets as np

class Client():
    """Client class"""
    def __init__(self, ip: bytes, port, timeout: int):
        self.MySock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.MySock.connect((ip, port))
        self.MySock.settimeout(timeout)
        self.MySock.setblocking(False)

    def __del__(self):
        NPacket = np.NET_Packet(None, np.DISCONNECT)
        self.SendPacket(NPacket)
        self.MySock.close()

    def ListenPort(self):
        try:
            data = self.MySock.recv(1024)

            dict_str = data.decode("UTF-8")
            NPacket_dict = json.loads(dict_str)
            NPacket = namedtuple("NET_Packet", NPacket_dict.keys())(*NPacket_dict.values())

            if NPacket.type == np.CONNECTION_ACCEPTED:
                print("Client has connected succefully!")
            #elif NPacket.type == np.SYNC:
            #    print("SYNC CLIENT")

            return NPacket
        except socket.timeout:
            print("Client don't get any package")

    def SendPacket(self, packet: np.NET_Packet):
        np_dict = dict(packet)
        self.MySock.send(json.dumps(np_dict).encode("UTF-8"))