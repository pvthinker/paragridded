import numpy as np
from ctypes import POINTER, c_void_p, c_int, c_char, c_float, c_double, c_int8, c_int32, byref, cdll


def ptr(obj):
    if isinstance(obj, np.ndarray):
        if obj.dtype == np.float32:
            return obj.ctypes.data_as(POINTER(c_float))

        elif obj.dtype == np.float64:
            return obj.ctypes.data_as(POINTER(c_double))

        elif obj.dtype == np.int8:
            return obj.ctypes.data_as(POINTER(c_int8))

        elif obj.dtype == np.int32:
            return obj.ctypes.data_as(POINTER(c_int32))

        else:
            raise ValueError(f"dtype {obj.dtype} is not implemented")

    elif isinstance(obj, int):
        return byref(c_int(obj))

    elif isinstance(obj, float):
        return byref(c_double(obj))


if __name__ == "__main__":

    shape = (3, )
    a = np.zeros(shape)
    b = np.zeros(shape, dtype="f")
    c = np.zeros(shape, dtype="f")
    p = ptr(a)
    q = ptr(b)
    r = ptr(c)

    print(p)
    print(q)
    print(r)

    nz = 10
    print(ptr(nz))
    x = 1.
    print(ptr(x))
