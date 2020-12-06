""" Croco specific tools
"""
import numpy as np
import marray as ma
import grid as gr
import nctools as nct

debug = False

dims = ("t", "sigma", "eta", "xi")

hdims = dims[2:]
vdims = dims[1]
tdims = dims[0]
sdims = dims[1:]

tiledims = ("eta", "xi")

tpoint = {"sigma": False, "eta": False, "xi": False}
upoint = {"sigma": False, "eta": False, "xi": True}
vpoint = {"sigma": False, "eta": True, "xi": False}
wpoint = {"sigma": True, "eta": False, "xi": False}
fpoint = {"sigma": False, "eta": True, "xi": True}
qpoint = {"sigma": True, "eta": True, "xi": True}
uwpoint = {"sigma": True, "eta": False, "xi": True}
vwpoint = {"sigma": True, "eta": True, "xi": False}

variables = {"temp": tpoint,
             "salt": tpoint,
             "zeta": tpoint,
             "u": upoint,
             "v": vpoint,
             "w": wpoint}


def fill_halo(z2d, halow):
    z2d[halow-1, :] = 2*z2d[halow, :]-z2d[halow+1, :]
    z2d[-halow, :] = 2*z2d[-halow-1, :]-z2d[-halow-2, :]

    z2d[:, halow-1] = 2*z2d[:, halow]-z2d[:, halow+1]
    z2d[:, -halow] = 2*z2d[:, -halow-1]-z2d[:, -halow-2]

    z2d[halow-1, halow-1] = 2*z2d[halow-1, halow-1]-z2d[halow+1, halow-1]
    z2d[-halow, halow-1] = 2*z2d[-halow-1, halow-1]-z2d[-halow-2, halow-1]
    z2d[halow-1, -halow] = 2*z2d[halow-1, -halow-1]-z2d[halow-1, -halow-2]
    z2d[-halow, -halow] = 2*z2d[-halow-1, -halow]-z2d[-halow-2, -halow]


def load_grid(grdfiles, blocks, dimpart, nsigma, **kwargs):
    """Setup a `grid` by reading `grdfiles` on `blocks`
    """
    ncgrid = nct.MDataset(grdfiles, blocks, dimpart, **kwargs)

    # dummy time, to be updated later
    time = ma.Marray(np.arange(10), dims=tdims)

    lat = nct.readmarray(ncgrid, "lat_rho", hdims)
    lon = nct.readmarray(ncgrid, "lon_rho", hdims)

    if ncgrid.halow > 0:
        halow = ncgrid.halow
        # extend lon-lat on the halow=1 to infer correctly @ f-points
        fill_halo(lat, halow)
        fill_halo(lon, halow)

    depth = nct.readmarray(ncgrid, "h", hdims)
    sigma = ma.Marray((np.arange(nsigma)+0.5)/nsigma, dims=vdims)

    coords = {"t": time, "sigma": sigma, "eta": lat, "xi": lon}

    return gr.Grid(coords, dims, depth=depth, **kwargs)


def convert_netcdf_dim_to_var(vardims, gdims, mapping):
    """Transform NetCDF dims into grid dims using the mapping
    """
    for k in range(len(vardims)):
        ddd = vardims[k]
        if ddd in mapping:
            vardims[k] = mapping[ddd]


def ncread(mdataset, grid, varname, elem=slice(None)):
    """Read a variable from a MDataset and returns it as a Marray
    consistent with `grid`
    """
    assert varname in variables, f"this `{varname}` is not implemented"
    var = mdataset.variables[varname]
    # data = var[elem]
    attrs = var.attrs
    stagg = variables[varname]

    vardims = list(var.infos["dims"])
    if isinstance(elem, int):
        attrs[vardims[0]] = elem
        vardims = vardims[1:]

    convert_netcdf_dim_to_var(vardims, grid.dims, mdataset.mapping)

    sizes = grid.get_sizes(stagg)

    shape_horiz_data = var.shape[-2:]
    shape_horiz_grid = [sizes[vardims[-2]], sizes[vardims[-1]]]
    #shape[-2] = sizes[vardims[-2]]
    #shape[-1] = sizes[vardims[-1]]
    #shape = tuple(shape)

    if shape_horiz_grid != shape_horiz_data:
        # fix shape
        # the fix is only on "eta" and "xi"
        jj0 = shape_horiz_grid[-2]-shape_horiz_data[-2]
        ii0 = shape_horiz_grid[-1]-shape_horiz_data[-1]
        if debug:
            print(f"grid {shape_horiz_grid} != data {shape_horiz_data} start index {jj0}, {ii0}")

        if isinstance(elem, int):
            shape = var.shape[1:-2]+shape_horiz_grid
        else:
            shape = var.shape[:-2]+shape_horiz_grid
        if debug:
            print(f"target shape {shape}")
        data = np.zeros(shape)

        if jj0 < 2:
            jslice = slice(jj0, None)
        elif jj0 == 2:
            jslice = slice(1, -1)

        if ii0 < 2:
            islice = slice(ii0, None)
        elif ii0 == 2:
            islice = slice(1, -1)

        data[..., jslice, islice] = var[elem]
    else:
        data = var[elem]

    return ma.Marray(data, attrs=attrs, dims=vardims, stagg=stagg)


def sigma2z(grid, zeta=0, stagg={}):
    """ compute depth from sigma coordinates
    """
    staggering = {}
    for d in grid.dims:
        staggering[d] = (d in stagg) and stagg[d]
    sizes = grid.get_sizes(staggering)
    z = ma.Marray(ma.zeros(sizes),
                  dims=grid.dims,
                  attrs={"name": "depth"},
                  stagg=staggering)
    staggdims = tuple(
        [d for d in grid.dims if staggering[d] and d in grid.depth.dims])
    if isinstance(zeta, int):
        timeison = False
        hinv = ma.Marray(zeta+grid.depth, dims=grid.depth.dims)
    else:
        timeison = True
        hinv = ma.Marray(zeta+grid.depth, dims=zeta.dims)

    hinv2 = grid.avg(hinv, staggdims)
    h = ma.Marray(grid.depth, dims=grid.depth.dims)
    h2 = grid.avg(h, staggdims)
    sigma = grid.sigma(stagg=staggering)
    if debug:
        print(hinv2.shape, h2.shape, staggering, sigma, z.shape)
    if "t" in grid.sizes:
        for kt in range(grid.sizes["t"]):
            if timeison:
                htot = hinv2[kt]
            else:
                htot = hinv
            for k in range(grid.sizes["sigma"]):
                z[kt, k] = -h2 + sigma[k]*htot
    else:
        for k in range(grid.sizes["sigma"]):
            z[k] = -h2 + sigma[k]*hinv2
    return z
