import numpy as np

from ctypes import POINTER, c_void_p, c_int, c_char, c_double, c_int8, byref, cdll


def ptr(array):
    return array.ctypes.data_as(POINTER(c_double))


class CArray(np.ndarray):
    # https://stackoverflow.com/questions/33881694/overloading-the-operator-in-python-class-to-refer-to-a-numpy-array-data-membe#33882066
    def __new__(cls, arg, fill_value=0, dtype=float, attrs={}):
        if isinstance(arg, np.ndarray):
            if arg.dtype != dtype:
                data = np.asarray(arg, dtype=dtype)
            else:
                data = arg

            shape = data.shape

        elif isinstance(arg, tuple):
            shape = arg
            data = np.full(shape, fill_value, dtype=dtype)

        else:
            raise ValueError("arg must a ndarray or a tuple (shape)")

        obj = np.asarray(data).view(cls)
        obj.fill_value = fill_value
        obj.attrs = attrs
        obj.ptr = ptr(data)
        size = np.prod(shape)
        obj.Nptr = byref(c_int(size))
        obj.shapeptr = tuple([byref(c_int(size)) for size in shape])
        return obj

    def reset(self, fill_value=None):
        if fill_value is not None:
            self.fill_value = fill_value

        self.fill(self.fill_value)


if __name__ == "__main__":

    shape = (3, 5)
    a = np.zeros(shape)
    c = CArray(shape)
