from core.Constants import DLL_USE
from platform import architecture

if not DLL_USE:
    dll_collision = None

else:
    from utils.files import get_full_path as fpath
    import ctypes as ct

    #  DLL CONFIGURATION

    #  get os architecture
    arch = architecture()

    if arch[0] == '64bit':
        #  collision 64 bit
        path = fpath('collision64.dll', file_type='dll')
        dll_collision = ct.CDLL(path)
    else:
        #  collision 32 bit
        path = fpath('collision32.dll', file_type='dll')
        dll_collision = ct.CDLL(path)

    dll_collision.fill_one_element.restype = ct.c_void_p
    dll_collision.fill_one_element.argtypes = [ct.c_int, ct.c_int, ct.c_int, ct.c_int]
