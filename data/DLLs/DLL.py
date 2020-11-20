from core.Constants import DLL_USE
import platform

if not DLL_USE:
    dll_collision = None

else:
    from utils.files import get_full_path as fpath
    import ctypes as ct
    from numpy.ctypeslib import ndpointer
    import numpy as np

    #  DLL CONFIGURATION

    arch = platform.architecture()

    if arch[0] == '64bit':
        #  collision
        path = fpath('collision64.dll', file_type='dll')
        dll_collision = ct.CDLL(path)
    else:
        #  collision
        path = fpath('collision32.dll', file_type='dll')
        dll_collision = ct.CDLL(path)

    # dll_collision.getMinkovskiDifference.restype = ndpointer(dtype=ct.c_int, shape=(4,))
    # dll_collision.getMinkovskiDifference.argtypes = \
    #     [ct.c_int, ct.c_int, ct.c_int, ct.c_int, ct.c_int, ct.c_int, ct.c_int, ct.c_int]
    #
    # ND_POINTER_INT = np.ctypeslib.ndpointer(dtype=np.int64, ndim=1, flags="C")
    # ND_POINTER_BOOL = np.ctypeslib.ndpointer(dtype=np.bool, ndim=1, flags="C")

    dll_collision.fill_one_element.restype = ct.c_void_p
    dll_collision.fill_one_element.argtypes = [ct.c_int, ct.c_int, ct.c_int, ct.c_int]
    #

    #
