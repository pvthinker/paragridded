import numpy as np
import multiprocessing as mp
from numba import jit


def keeptoplevel(var):
    var._arrays = {tile: array[-1].copy()
                   for tile, array in var._arrays.items()}


class Curl:
    def __init__(self, reader, vinterp):
        self.reader = reader
        self.nthreads = 12
        self.vi = vinterp

    def compute(self, var):
        u = var.new("u")
        v = var.new("v")
        if var.space.is_depth:
            self.vi.compute(u)
            self.vi.compute(v)
        elif var.space.is_level:
            assert var.space.level == -1
            self.reader.read(u)
            self.reader.read(v)
            keeptoplevel(u)
            keeptoplevel(v)

        f = var.new("f")
        self.reader.read(f)

        dx = 1e3
        tasks = iter([(u[tile], v[tile], f[tile], dx)
                      for tile in var])
        print(f"compute curl {var.varname}")
        with mp.Pool(processes=self.nthreads) as pool:
            data = pool.starmap(curl2d_overf, tasks)

        var.update(data)

        var.staggering.horiz = "f"


@jit
def curl2d_overf(u, v, f, dx):
    ny, nx = u.shape
    vor = np.zeros(u.shape, dtype=u.dtype)
    for j in range(ny-1):
        for i in range(nx-1):
            cff = 1./(f[j, i]*dx)
            vor[j, i] = (v[j, i]-u[j, i]-v[j, i+1]+u[j+1, i])*cff
    return vor
