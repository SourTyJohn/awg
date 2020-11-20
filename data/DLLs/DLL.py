from core.Constants import DLL_USE
import platform

if not DLL_USE:
    dll_collision = None

else:
    from utils.files import get_full_path as fpath
    import ctypes as ct

    #  DLL CONFIGURATION

    arch = platform.architecture()

    if arch[0] == '64bit':
        #  collision 64
        path = fpath('collision64.dll', file_type='dll')
        dll_collision = ct.cdll.LoadLibrary(path)
        print("Loaded 64 bit collision dll")
    else:
        #  collision 32
        path = fpath('collision32.dll', file_type='dll')
        dll_collision = ct.cdll.LoadLibrary(path)
        print("Loaded 32 bit collision dll")