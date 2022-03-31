import gigatl
import bindatasets as bd
from variables import Varinfos, Variable, Domain, Time, Space
#import vinterp

import numpy as np
import schwimmbad
#import multiprocessing as mp

staggering = {'u': 'ur',
              'v': 'vr',
              'temp': 'rr',
              'salt': 'rr',
              'AKv': 'rw',
              'zeta': 'r',
              'ubar': 'u',
              'vbar': 'v',
              'angle': 'r',
              'h': 'r',
              'hraw': 'r',
              'f': 'f',
              'pm': 'r',
              'pn': 'r',
              'lon_rho': 'r',
              'lat_rho': 'r',
              'mask_rho': 'r',
              'lon_psi': 'f',
              'lat_psi': 'f',
              'xl': 'r',
              'el': 'r',
              'lon_u': 'u',
              'lat_u': 'u',
              'lon_v': 'v',
              'lat_v': 'v'}


class Gigatl:

    def __init__(self, halowidth=0, nthreads=12, debug=False):
        self.halowidth = halowidth
        self.nthreads = nthreads
        #self.pool = mp.Pool(processes=self.nthreads)
        self.hist = bd.Dataset()
        self.grid = bd.GDataset()
        self.toc = {}
        self.toc.update(self.hist.toc)
        self.toc.update(self.grid.toc)
        # buffer to store the grid arrays
        self.buffer = {name: {}
                       for name in self.grid.toc}
        self.histbuffer = {name: {}
                           for name in self.hist.toc}
        self.histbuffer_domain = Domain()
        self.histbuffer_time = Time()
        self.debug = debug

    def restart_pool(self):
        pass
        # self.pool.close()
        # self.pool.terminate()
        # self.pool = mp.Pool(processes=self.nthreads)

    def read(self, var: Varinfos):
        """ Parallel multi tiles read"""
        if var.varname in self.grid.toc:
            reader = self.grid.read_tile
            tiles = set(var)
            buffered = set(self.buffer[var.varname])
            missing = sorted(tiles.difference(buffered))

        elif var.varname in self.hist.toc:
            reader = self.hist.read_tile
            tiles = set(var)
            if ((var.domain == self.histbuffer_domain)
                    and (var.time == self.histbuffer_time)):
                buffered = set(self.histbuffer[var.varname])
                missing = sorted(tiles.difference(buffered))
            else:
                # purge hist buffer
                for name in self.hist.toc:
                    self.histbuffer[name] = {}
                buffered = {}
                missing = tiles
        else:
            raise ValueError(f"variable {var.varname} is not in the database")

        if len(missing) > 0:
            tasks = iter([(var, tile) for tile in missing])
            print(
                f"read from binary files {var.varname} ({len(missing)} missing tiles)")
            if self.debug:
                date = var.time.date

                def myreader(task):
                    print(
                        f"\r{date} reading tile: {task[-1]}", end="", flush=True)
                    return reader(task)
                arrays = [myreader(task) for task in tasks]
                print(" DONE!")
            else:
                # with mp.Pool(processes=self.nthreads) as pool:
                with schwimmbad.MultiPool(processes=self.nthreads) as pool:
                    arrays = pool.map(reader, tasks)

        else:
            print(f"load from buffer {var.varname} ({len(tiles)} tiles)")
            arrays = []

        if var.varname in self.grid.toc:
            var._arrays = {tile: array
                           for tile, array in zip(missing, arrays)}
            self.buffer[var.varname].update(
                {tile: array
                 for tile, array in zip(missing, arrays)})

            buff = {tile: self.buffer[var.varname][tile]
                    for tile in buffered}
            var._arrays.update(buff)

        else:
            var._arrays = {tile: array
                           for tile, array in zip(missing, arrays)}
            self.histbuffer[var.varname].update(
                {tile: array
                 for tile, array in zip(missing, arrays)})

            self.histbuffer_domain = var.domain.copy()
            self.histbuffer_time = var.time.copy()

            buff = {tile: self.histbuffer[var.varname][tile]
                    for tile in buffered}
            var._arrays.update(buff)

        self.set_staggering(var)

        if self.halowidth > 0:
            var.add_halo()

    def set_staggering(self, var):
        stagg = staggering[var.varname]
        horiz = stagg[0]
        vert = stagg[1] if len(stagg) == 2 else ""
        var.staggering.horiz = horiz
        var.staggering.vert = vert


if __name__ == "__main__":
    import hmap
    import matplotlib.pyplot as plt
    plt.ion()

    from variables import Varinfos, Time, Space, Domain, Variable

    #giga = Gigatl()

    christmas = Time("2008-12-25", 12)
    springtime = Time("2009-03-21", 12)

    surface = Space(Space.LEVEL, 10)
    z1000 = Space(Space.DEPTH, -1000.)
    lucky = Space(Space.PROFILE, [45, 33])
    gridpoint = Space(Space.POINT, [12, 130, 95])

    brittany = Domain([(-12, 45), (4, 52)])

    #ssh = Varinfos("zeta", brittany, christmas)

    giga = Gigatl()
    # ilon=Varinfos("lon_psi",brittany)
    # ilat=Varinfos("lat_psi",brittany)
    # lon=giga.read(ilon)
    # lat=giga.read(ilat)
    # isst=Varinfos("temp",brittany,christmas,Space(Spacemode.level, [-1]))
    # sst=giga.read(isst)
    sst = Variable("temp", brittany, christmas, Space(Space.LEVEL, -1))
    giga.read(sst)

    # plt.clf()

    # for tile in sst:
    #     x = lon[tile]
    #     y = lat[tile]
    #     z = sst[tile]
    #     plt.pcolormesh(x, y, z[:-1,:-1], vmin=4, vmax=14, cmap="RdBu_r")

    colorbar = (4, 14, "RdBu_r")
    f = hmap.Pcolormesh(giga)
    f.draw(sst, colorbar)
