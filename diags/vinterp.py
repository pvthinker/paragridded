from variables import Variable
import vert_coord as vc
import vinterp_tools

import numpy as np
import numbers
import multiprocessing as mp


class Vinterp:
    def __init__(self, reader):
        self.reader = reader
        self.nthreads = 12
        #self.pool = mp.Pool(processes=self.nthreads)
        nz = 100
        dtype = "f"
        N, hmin, Tcline, theta_s, theta_b = vc.gigatl()

        hc, Cs_w, Cs_r = vc.set_scoord(N, hmin, Tcline, theta_s, theta_b)

        self.hc = np.asarray(hc, dtype=dtype)
        self.s_r = -1+(np.arange(nz, dtype=dtype)+0.5)/nz
        self.cs_r = np.asarray(Cs_r, dtype=dtype)

        self.s_w = -1+np.arange(nz+1, dtype=dtype)/nz
        self.cs_w = np.asarray(Cs_w, dtype=dtype)

    def ddz(self, var, kz):
        zeta = Variable("zeta", var.domain, var.time)
        h = Variable("h", var.domain)
        self.reader.read(zeta)
        self.reader.read(h)
        self.reader.read(var)

        if var.staggering.vert == "w":
            sigma = self.s_w
            cs = self.cs_w
        else:
            sigma = self.s_r
            cs = self.cs_r

        hloc = {"r": 0, "u": 1, "v": 2, "f": 3}[var.staggering.horiz]

        tiles = var.domain.tiles

        tasks = iter([(tile, zeta[tile], h[tile],
                       self.hc.copy(), sigma.copy(), cs.copy(),
                       var[tile], hloc, kz)
                      for tile in tiles])

        with mp.Pool(processes=self.nthreads) as pool:
            data = pool.starmap(ddz3, tasks)

        var._arrays = {tile: d
                       for tile, d in data}

        var.staggering.vert = "w"

    def compute(self, var):
        assert var.space.is_depth

        zeta = Variable("zeta", var.domain, var.time)
        h = Variable("h", var.domain)

        self.reader.read(zeta)
        self.reader.read(h)
        self.reader.read(var)

        ntiles, ny, nx = zeta.shape
        tiles = zeta.domain.tiles

        assert isinstance(var.space.depth, numbers.Number)
        zout = np.asarray([var.space.depth], dtype="f")

        if var.staggering.vert == "w":
            sigma = self.s_w
            cs = self.cs_w
        else:
            sigma = self.s_r
            cs = self.cs_r

        hloc = {"r": 0, "u": 1, "v": 2, "f": 3}[var.staggering.horiz]

        tasks = iter([(tile, zeta[tile], h[tile],
                       self.hc, sigma, cs,
                       var[tile], zout, hloc)
                      for tile in tiles])

        if len(tiles) > self.nthreads:
            print(f"vertical interpolation {var.varname}")
            with mp.Pool(processes=self.nthreads) as pool:
                data = pool.starmap(vint3, tasks)
        else:
            data = [vint3(*task) for task in tasks]

        #print("data:", data[0][1].shape,len(data))
        var._arrays = {tile: d
                       for tile, d in data}
        # var.update(data)


def vint3(tile, zeta, h, hc, sigma, cs, phi, zout, hloc):
    nout = zout.shape[0]
    ny, nx = zeta.shape
    phiout = np.zeros((nout, ny, nx), dtype="f")
    vinterp_tools.vinterp3d_at_z(zeta, h.astype("f"),
                                 hc.copy(), sigma.copy(), cs.copy(),
                                 phi, zout.copy(), phiout, hloc)
    return (tile, phiout.squeeze())


def ddz3(tile, zeta, h, hc, sigma, cs, phi, loc, kz):
    ny, nx = zeta.shape
    phiout = np.zeros((ny, nx), dtype="f")
    dz = compute_dz(zeta, h, hc, sigma, cs, loc, kz)
    phiout[:] = (phi[kz+1]-phi[kz])/dz
    return (tile, phiout)


def compute_dz(ztop, depth, hc, sigma, cs, loc, kz):
    if (loc == 0):
        cff2 = (ztop+depth)/(depth+hc)
    else:
        raise ValueError("ddz not implemented at  other location that r-point")
    dz = cff2*(hc+depth*(cs[kz+1]-cs[kz]))
    return dz
