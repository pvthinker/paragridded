import numpy as np
import marray as ma
from pretty import BB, GR

debug = False


class Grid():
    """`Grid` provides functions to perform differential calculus on grid
    aware Marrays

    """

    def __init__(self, coords, dims, depth=None, halow=0, mask=None, **kwargs):
        self.coords = coords
        self.dims = dims
        # https://stackoverflow.com/questions/3431676/creating-functions-in-a-loop
        for coord in coords.keys():
            def fcoord(coord=coord, stagg={}):
                return coordfunc(self, coord, stagg=stagg)
            setattr(self, coord, fcoord)

        sizes = {}
        for coord in coords.values():
            sizes.update(coord.sizes)
        self.sizes = sizes
        self.depth = depth
        self.halow = halow

    def __repr__(self):
        string = []
        string += [GR("<class 'paragridded.grid.grid'>")]
        string += [BB("* Dimensions:") + f"{self.dims}"]

        string += [BB("* Coordinates:")]
        maxlen = max([len(v) for v in self.coords.keys()])
        maxlen += 1
        for k, v in self.coords.items():
            string += [f"  - {k:{maxlen}s} : {v.sizes}"]

        string += [BB("* Corners:")]
        y = getattr(self, self.dims[-2])()
        x = getattr(self, self.dims[-1])()
        string += [f"  - West-South : {y[0,0]}, {x[0,0]}"]
        string += [f"  - East-South : {y[0,-1]}, {x[0,-1]}"]
        string += [f"  - West-North : {y[-1,0]}, {x[-1,0]}"]
        string += [f"  - East-North : {y[-1,-1]}, {x[-1,-1]}"]

        string += [BB("* Halo width: ")+f"{self.halow}"]
        return "\n".join(string)

    def get_sizes(self, staggering):
        sizes = {}
        for dim, stagg in staggering.items():
            if stagg:
                sizes[dim] = self.sizes[dim]+1
            else:
                sizes[dim] = self.sizes[dim]
        return sizes

    def avg(self, marray_in, dim):
        """ two-points averaging along dim"""

        if isinstance(dim, list) or isinstance(dim, tuple):
            out = marray_in
            for d in dim:
                out = self.avg(out, d)
            return out

        stagg_out = flip_stagg(marray_in.stagg, dim)
        sizes = self.get_sizes(stagg_out)
        marray_out = ma.zeros(sizes, stagg=stagg_out,
                              attrs=marray_in.attrs,
                              dims=marray_in.dims)
        extend = int(marray_out.stagg[dim])
        idx = marray_in.dims.index(dim)
        if debug:
            print("in :", marray_in.stagg)
            print("out:", marray_out.stagg)
            print("extend=", extend)
            print("idx=", idx)
        twoptavg(marray_in, marray_out, idx, extend)
        return marray_out


def coordfunc0(grid, coord, stagg=None):
    """ old one : to remove"""
    assert coord in grid.coords
    if stagg is None:
        return grid.coords[coord]
    else:
        dim = list(stagg.keys())[0]
        return grid.avg(grid.coords[coord], dim)


def coordfunc(grid, coord, stagg={}):
    assert coord in grid.coords
    c = grid.coords[coord]
    sk = stagg.keys()
    dims = [d for d in c.dims if d in sk and stagg[d]]
    return grid.avg(c, dims)


def twoptavg(x_in, x_out, axis, extend):
    shape = x_in.shape
    dim = x_in.dims[axis]
    p, s, xi = ma.flat2d(x_in, dim)
    p, s, xo = ma.flat2d(x_out, dim)
    if extend == 1:
        xo[0] = 1.5*xi[0]-0.5*xi[1]
        xo[1:-1] = 0.5*(xi[1:]+xi[:-1])
        xo[-1] = 1.5*xi[-1]-0.5*xi[-2]
    elif extend == 0:
        xo[:] = 0.5*(xi[1:]+xi[:-1])

    x_out.flat = ma.unflat2d(p, s, xo)



def flip_stagg(stagg_in, dim):
    assert dim in stagg_in
    stagg_out = stagg_in.copy()
    stagg_out[dim] = not(stagg_in[dim])
    return stagg_out



def attachgrid(grid, marray, **kwargs):
    setattr(marray, "grid", grid)
    slicedims = [d for d in grid.dims if not(d in marray.dims)]
    if debug:
        print(slicedims)
    slicedindex = {}
    for d in slicedims:
        assert d in kwargs.keys()
        idx = kwargs[d]
        assert 0 <= idx < grid.sizes[d]
        slicedindex = {d: idx}
    setattr(marray, "slicedindex", slicedindex)


def gridslice(grid, marray, sliceindex):
    """
    To return the surface level

    sliceindex = {"sigma": -1}
    """
    dims = [d for d in marray.dims if not(d in sliceindex.keys())]
    out = ma.Marray(marray[-1], dims=dims)
    return out
    
if __name__ == "__main__":

    debug = False
    ma.debug = False

    dims = ("t", "sigma", "eta", "xi")
    hdims = dims[2:]
    vdims = dims[1]
    tdims = dims[0]
    sdims = dims[1:]

    nt, nz, ny, nx = 4, 2, 3, 5

    lon, lat = np.meshgrid(range(nx), range(ny))

    zeta = np.zeros((ny, nx))
    depth = ma.Marray(np.ones((ny, nx)), dims=hdims)
    lat = ma.Marray(lat, dims=hdims, attrs={"name": "latitude"})
    lon = ma.Marray(lon, dims=hdims, attrs={"name": "longitude"})
    sigma = ma.Marray((np.arange(nz)+0.5)/nz, dims=vdims)
    time = ma.Marray(np.arange(nt), dims=tdims)

    coords = {"t": time, "sigma": sigma, "eta": lat, "xi": lon}
    g = Grid(coords, dims, depth=depth)

    space = {d: g.sizes[d] for d in sdims}

    # define a 3D spatial array (no time)
    temp = ma.Marray(ma.zeros(space), dims=sdims,
                     attrs={"name": "temperature",
                            "units": "degC"})
    temp.flat = range(nz*ny*nx)

    salt = temp*0
    ma.copymeta(temp, salt)
    p, s, t = ma.flat2d(temp, "eta")
    salt.flat = ma.unflat2d(p, s, t)

    to = g.avg(g.avg(temp, "eta"), "xi")

    to = g.avg(temp, ("eta", "xi"))
