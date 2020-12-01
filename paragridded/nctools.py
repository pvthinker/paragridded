import os
import numpy as np
from netCDF4 import Dataset
import marray as ma
import topology as topo
from pretty import BB, MD, VA

debug = False


class MDataset():
    """
    Open a subset of distributed NetCDF files

    - Concatenate subdomains in a single array.
    - The returned array may have a halo. The halo is filled
      using the neighbourings tiles

    Parameters
    ----------
    dimpart: dict, tells which netCDF dimensions are to be concatenated

    halow: int, halo with
    """

    def __init__(self, nctemplate, blocks, dimpart, halow=0, gridsizes={}, **kwargs):
        self.domainpartition = dimpart["domainpartition"]
        mapping = {}
        for k, v in dimpart["netcdfdimnames"].items():
            for d in v:
                mapping[d] = k
        self.mapping = mapping
        self.netcdfdimnames = dimpart["netcdfdimnames"]
        self.blocks = blocks
        self.tileblock = blocks["tileblock"]
        self.tiles = process_tileblock(blocks["tileblock"], blocks["partition"])
        # if isinstance(blocks["tileblock"], int):
        #     # block is just one tile
        #     tile = blocks["tileblock"]
        #     self.tileblock = [[tile]]*2
        #     self.tiles = np.asarray([[tile]])
        # else:
        #     self.tileblock = blocks["tileblock"]
            

        self.nctemplate = nctemplate
        self.halow = halow
        self.kwargs = kwargs

        self.missing = self._get_missing(**kwargs)

        if self.missing.all():
            self.toc = {}
            # tileblock has no data
            self.dims = []
            self.sizes = {}
            self.variables = {}
        else:
            self.toc = self._get_toc(**kwargs)
            self.dims = self._get_dims(**kwargs)
            self.sizes = self._get_sizes(gridsizes, **kwargs)

            self.variables = self._get_vars(**kwargs)


    def __repr__(self):
        partition = self.blocks["partition"]
        string = []
        string += [MD("<class 'paragridded.nctools.MDataset'>")]

        if self.missing.all():
            string += ["empty dataset, all tiles are missing"]
        else:
            tiles = self.tiles.copy()
            tiles[self.missing] = -1
            tile0 = get_one_tile(tiles, self.missing)
            ncfile = getncfile(self.nctemplate, tile0, **self.kwargs)

            string += [BB("* filename: ")+f"(for tile=={tile0})"]
            string += [f"  - {ncfile}"]
            string += [BB("* partition: ")+f"{partition}"]
            string += [BB("* tiles:")+f" {self.tiles.shape}"]
            string += [tiles.__repr__()]
            string += [BB("* dims: ")+f"{self.dims}"]
            string += [BB("* sizes:")]
            string += [f"  - {k}: {v}" for k, v in self.sizes.items()]
            string += [BB("* variables:")]
            string += [f"  - {k}: {v}" for k, v in self.toc.items()]
            string += [BB("* Halo width: ")+f"{self.halow}"]
        return "\n".join(string)

    def _get_vars(self, **kwargs):
        mdkeys = ["blocks", "nctemplate", "missing", "halow", "tiles"]
        variables = {}
        for varname, dims in self.toc.items():
            infos = {k: self.__dict__[k] for k in mdkeys}
            sizes = {d: v for d, v in self.sizes.items() if d in dims}

            infos["dims"] = dims
            infos["sizes"] = sizes
            if debug:
                print(varname, infos)
            variables[varname] = Variable(varname, infos, **kwargs)

        return variables

    def _get_missing(self, **kwargs):
        tiles = self.tiles
        tileblock = self.tileblock
        npy, npx = tiles.shape#len(list(tileblock[0]))
        #npx = len(list(tileblock[1]))
        missing = np.ones((npy, npx), dtype=bool)
        for j in range(npy):
            for i in range(npx):
                tile = tiles[j, i]
                ncfile = getncfile(self.nctemplate, tile, **kwargs)#self.nctemplate(tile)#.format(tile=tile, **kwargs)
                if os.path.isfile(ncfile):
                    missing[j, i] = False

        return missing

    def _get_sizes(self, gridsizes, **kwargs):
        sizes = {}
        tile = get_one_tile(self.tiles, self.missing)
        nby, nbx = self.tiles.shape

        for dim in self.dims:
            if dim in self.mapping:
                griddimname = self.mapping[dim]
            else:
                griddimname = dim
            if griddimname in self.domainpartition:
                if dim in gridsizes:
                    size = gridsizes[dim]
                else:
                    partindex = self.domainpartition.index(griddimname)
                    nblocks = self.tiles.shape[partindex]
                    size = []
                    for i in range(nblocks):
                        if partindex == 0:
                            j = 0
                            while (j<nbx) and (self.missing[i,j]):
                                j+=1
                            if (j==nbx):
                                tile = -1
                            else:
                                tile = self.tiles[i, j]
                        elif partindex == 1:
                            j = 0
                            while (j<nby) and (self.missing[j,i]):
                                j+=1
                            if (j==nby):
                                tile = -1
                            else:
                                tile = self.tiles[j, i]

                        if tile>-1:
                            ncfile = getncfile(self.nctemplate, tile, **kwargs)
                            with Dataset(ncfile) as nc:
                                size += [len(nc.dimensions[dim])]

            else:
                ncfile = getncfile(self.nctemplate, tile, **kwargs)#self.nctemplate(tile)#.format(tile=tile, **kwargs)
                with Dataset(ncfile) as nc:
                    size = len(nc.dimensions[dim])

            sizes[dim] = size

        return sizes

    def _get_dims(self, **kwargs):
        tile = get_one_tile(self.tiles, self.missing)
        ncfile = getncfile(self.nctemplate, tile, **kwargs)#self.nctemplate(tile)#.format(tile=tile, **kwargs)
        with Dataset(ncfile) as nc:
            dims = [dim for dim in nc.dimensions]
        return dims

    def _get_toc(self, **kwargs):
        nctemplate = self.nctemplate
        tiles = self.tiles
        toc = {}
        ok = False
        for tile in tiles.flat:
            ncfile = getncfile(self.nctemplate, tile, **kwargs)#nctemplate(tile)#.format(tile=tile, **kwargs)
            if os.path.isfile(ncfile):
                with Dataset(ncfile) as nc:
                    for var in nc.variables:
                        if debug:
                            print(ncfile, var)
                        toc[var] = nc.variables[var].dimensions
                ok = True
                break

        if not ok:
            raise Warning("No variables on this grid")
        return toc


def get_one_tile(tiles, missing):
    return [t for t, m in zip(tiles.flat, missing.flat) if not m][0]


class Variable():
    def __init__(self, varname, infos, **kwargs):
        self.varname = varname
        self.infos = infos
        self.kwargs = kwargs
        self.attrs = self._get_attrs()

    def _get_attrs(self):
        tiles = self.infos["tiles"]
        nctemplate = self.infos["nctemplate"]
        missing = self.infos["missing"]
        tile = get_one_tile(tiles, missing)
        ncfile = getncfile(nctemplate, tile, **self.kwargs)#nctemplate(tile)#.format(tile=tile, **self.kwargs)
        with Dataset(ncfile) as nc:
            v = nc.variables[self.varname]
            names = v.ncattrs()
            attrs = {key: v.getncattr(key) for key in names}
        return attrs

    def __repr__(self):
        dims = self.infos["dims"]
        sizes = self.infos["sizes"]
        halow = self.infos["halow"]
        shape = shape_from_sizes(sizes, dims, halow)
        string = []
        string += [VA("<class 'paragridded.nctools.Variable'>")]
        string += [BB("* name: ")+f"{self.varname}{dims}"]
        string += [BB("* attrs:")]
        string += [f"  - {k}: {v}" for k, v in self.attrs.items()]
        string += [BB("* shape : ")+f"{shape}"]
        string += [BB("* halo width: ")+f"{halow}"]
        return "\n".join(string)

    def __getitem__(self, elem=slice(None)):
        varname = self.varname
        sizes = self.infos["sizes"]
        dims = self.infos["dims"]
        halow = self.infos["halow"]
        tiles = self.infos["tiles"]
        nctemplate = self.infos["nctemplate"]
        missing = self.infos["missing"]

        if elem == slice(None):
            # read all
            outdims = dims
            iidx = [slice(None)]*len(dims)

        elif isinstance(elem, int):
            # assume it's time
            outdims = dims[1:]
            iidx = [slice(None)]*len(dims)
            iidx[0] = elem

        else:
            raise ValueError("pb with the slice")

        shape = [sizes[d] for d in outdims]

        multiple_files = any([isinstance(s, list) for s in shape])
        varshape = shape_from_sizes(sizes, outdims, halow)
        var = np.zeros(varshape)
        oidx = [slice(None)]*len(varshape)

        if multiple_files:
            oidx[-1] = slice(halow, -halow)
            oidx[-2] = slice(halow, -halow)
            if debug:
                print(shape)

            j0 = halow
            ny = shape[-2]
            nx = shape[-1]
            for j in range(len(ny)):
                i0 = halow
                for i in range(len(nx)):
                    if missing[j, i]:
                        pass
                    else:
                        tile = tiles[j, i]
                        ncfile = getncfile(nctemplate, tile, **self.kwargs)#nctemplate(tile)#.format(tile=tile, **self.kwargs)
                        oidx[-1] = slice(i0, i0+nx[i])
                        oidx[-2] = slice(j0, j0+ny[j])
                        with Dataset(ncfile) as nc:
                            var[tuple(oidx)] = nc.variables[varname][iidx]
                    i0 += nx[i]
                j0 += ny[j]

        else:
            tile = get_one_tile(tiles, missing)
            ncfile = getncfile(nctemplate, tile, **self.kwargs)#nctemplate(tile)#.format(tile=tile, **self.kwargs)
            with Dataset(ncfile) as nc:
                var[tuple(oidx)] = nc.variables[varname][iidx]

        if (halow > 0) and multiple_files:
            # fill the halo
            partition = self.infos["blocks"]["partition"]
            npy = len(ny)
            npx = len(nx)
            for j in range(npy):
                for i in range(npx):
                    tile0 = tiles[j, i]
                    neighbours = topo.get_neighbours(tile0, partition)
                    direc = []
                    # loop over directions
                    for neighb in neighbours.keys():
                        dj, di = neighb
                        # check if there is a halo to be filled
                        # in this direction
                        if (0<=(j+dj)<npy) and (0<=(i+di)<npx):
                            # this neighbour is an interior tile
                            pass
                        else:
                            direc += [(dj, di)]
                    if debug:
                        print(f"{tile} directions to use {direc}")

                    for dj, di in direc:
                        shape = (ny[j], nx[i])
                        tile, hiidx, hoidx = topo.get_haloinfos(tile0, partition, shape, halow,
                                                                (dj, di))
                        hoidx = (shiftslice(hoidx[0], j*ny[j]),
                                 shiftslice(hoidx[1], i*nx[i]))
                        ncfile = getncfile(nctemplate, tile, **self.kwargs)
                        if os.path.isfile(ncfile):
                            with Dataset(ncfile) as nc:
                                if debug:
                                    print(tile0, tile, hoidx, hiidx)
                                oidx[-2:] = hoidx
                                iidx[-2:] = hiidx
                                var[tuple(
                                    oidx)] = nc.variables[varname][tuple(iidx)]
        return var


def readmarray(mfdataset, varname, dims, elem=slice(None)):
    """ Read `varname` and returns it as a Marray
    """
    v = mfdataset.variables[varname]
    data = v[elem]
    return ma.Marray(data, attrs=v.attrs, dims=dims)

def getncfile(nctemplate, tile, **kwargs):
    if isinstance(nctemplate, str):
        return nctemplate.format(tile=tile, **kwargs)
    else:
        return nctemplate(tile)

def shiftslice(myslice, shift):
    start = myslice.start + shift
    stop = myslice.stop + shift
    step = myslice.step
    return slice(start, stop, step)


def shape_from_sizes(sizes, dims, halow):
    shape = []
    for d in dims:
        s = sizes[d]
        if isinstance(s, int):
            shape += [s]
        else:
            shape += [np.sum(s)+2*halow]
    return shape


def process_tileblock(tileblock, partition):

    if "int" in str(type(tileblock)):
        tile = tileblock
        tilesarray = np.array(tile, dtype=int)
        tilesarray.shape = [1]*len(partition)

    elif isinstance(tileblock, tuple):
        assert len(tileblock) == len(partition) == 2
        ndims = len(partition)
        idx = [1]*ndims
        ntiles = 1
        for d in range(ndims):
            if isinstance(tileblock[d], int):
                idx[d] = [tileblock[d]]
            else:
                idx[d] = [i for i in tileblock[d]]
            ntiles *= len(idx[d])
        shape = (len(idx[0]), len(idx[1]))
        tilesarray = np.zeros(shape, dtype=int)
        for j in range(shape[0]):
            for i in range(shape[1]):
                coords = (idx[0][j], idx[1][i])
                tilesarray[j, i] = topo.coord2tile(coords, partition)
    else:
        raise TypeError("tileblock should be an int or a tuple")

    return tilesarray


# if __name__ == "__main__":
#     partition = (100, 100)
#     tileblock = (range(50, 54), range(44, 50))
#     tiles = process_tileblock(tileblock, partition)

#     blocks = {"partition": partition,
#               "tileblock": tileblock,
#               "tiles": tiles}

#     dimpart = {0: ("eta_rho", "eta_v"),
#                1: ("xi_rho", "xi_u")}

#     dirgrid = "/net/omega/local/tmp/1/gula/GIGATL1/GIGATL1_1h_tides/GRD"
#     grdfiles = "{dirgrid}/gigatl1_grd_masked.{tile:04}.nc"

#     dirhis = "/net/omega/local/tmp/1/gula/GIGATL1/GIGATL1_1h_tides/SURF/gigatl1_surf.2008-05-23"

#     hisfiles = "{dirhis}/gigatl1_surf.{tile:04}.nc"

#     ncg = MDataset(grdfiles, blocks, dimpart, dirgrid=dirgrid)
#     nch = MDataset(hisfiles, blocks, dimpart, dirhis=dirhis, halow=30)
