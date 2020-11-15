""" Croco specific tools
"""
import numpy as np
import marray as ma
import grid as gr
import nctools as nct

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


def load_grid(grdfiles, blocks, dimpart, nsigma, **kwargs):
    """Setup a `grid` by reading `grdfiles` on `blocks`
    """
    ncgrid = nct.MDataset(grdfiles, blocks, dimpart, **kwargs)

    # dummy time, to be updated later
    time = ma.Marray(np.arange(10), dims=tdims)

    lat = nct.readmarray(ncgrid, "lat_rho", hdims)
    lon = nct.readmarray(ncgrid, "lon_rho", hdims)
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
            vardims[k] = gdims[-2+mapping[ddd]]


def ncread(mdataset, grid, varname, elem=slice(None)):
    """Read a variable from a MDataset and returns it as a Marray
    consistent with `grid`
    """
    assert varname in variables, f"this `{varname}` is not implemented"
    var = mdataset.variables[varname]
    data = var[elem]
    attrs = var.attrs
    stagg = variables[varname]

    vardims = list(var.infos["dims"])
    if isinstance(elem, int):
        attrs[vardims[0]] = elem
        vardims = vardims[1:]


    convert_netcdf_dim_to_var(vardims, grid.dims, mdataset.mapping)

    sizes = grid.get_sizes(stagg)
    shape = list(data.shape)
    shape[-2] = sizes[vardims[-2]]
    shape[-1] = sizes[vardims[-1]]
    shape = tuple(shape)

    if shape != data.shape:
        # fix shape
        # the fix is only on "eta" and "xi"
        print(f"grid {shape} != data {data.shape}")
        jj0 = shape[-2]-data.shape[-2]
        ii0 = shape[-1]-data.shape[-1]
        fixdata = np.zeros(shape)
        fixdata[..., jj0:, ii0:] = data
        data = fixdata

    return ma.Marray(data, attrs=attrs, dims=vardims, stagg=stagg)
