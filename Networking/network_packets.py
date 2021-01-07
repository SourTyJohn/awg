CONNECT = 1
CONNECTION_ACCEPTED = 2
CONNECTION_REJECTED = 3
DISCONNECT = 4
FORCE_DISCONNECT = 5
SYNC = 6
ADD_OBJECT = 7

class NET_Packet(object):
    """Network packet class"""
    def __init__(self, data, packet_type):
        self.type = packet_type
        self.Data = data

    def SetData(self, data):
        self.Data = data
    
    def __iter__(self):
        yield 'type', self.type
        yield 'Data', self.Data