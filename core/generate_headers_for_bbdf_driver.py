

import xarray as xr
import numpy as np
import bBDF
import glob
import os

#targrid = "/ccc/store/cont003/gch0401/gch0401/GIGATL1_1h_tides/GRD"
dirgrid = "/ccc/scratch/cont003/gen12051/groullet/giga/HIS_1h"

hisdate = "2009-08-28"
experiment = "with tides"

varlist = ["u", "v", "temp", "salt", "AKv",
           "zeta", "ubar", "vbar"]  # , "scrum_time"]
vattrs = ["long_name", "units"]
gattrs = ['type', 'title', 'date', 'experiment', 'VertCoordType', 'theta_s', 'theta_s_expl', 'theta_b', 'theta_b_expl', 'Tcline', 'Tcline_expl', 'Tcline_units', 'hc', 'hc_expl',
          'hc_units', 'ndtfast', 'dt', 'dtfast', 'nwrt', 'Zob', 'Zob_expl', 'Zob_units', 'Cdb_max', 'Cdb_min', 'Cdb_expl', 'rho0', 'rho0_expl', 'rho0_units', 'gamma2', 'gamma2_expl']


def get_netcdf_from_store(subd):
    tarfile = f"{targrid}/{subd:02}/gigatl1_grd_masked.{subd:02}.tar"
    ierr = os.system(f"ccc_hsm status {tarfile}")
    os.system(f"cp {tarfile} {dirgrid}/{subd:02}/")
    os.system(f"cd {dirgrid}/{subd:02} ; tar xvf {tarfile}")


def get_infos(subd):

    files = glob.glob(f"{dirgrid}/{subd:02}/gigatl1_his.000048.*.nc")
    tiles = sorted([int(f.split(".")[2]) for f in files])
    ntiles = len(files)

    hours = [i for i in range(24)]

    grdfile = files[0]

    ds = xr.load_dataset(grdfile)

    headersize = 29400*4
    stripes = {"size": 177848320*4, "roundingsize": 65536}

    date = "YYYY-MM-DD"

    #dims = {"chunk": ntiles//100+1, "tile": 100}
    dims = {"tile": ntiles, "hour": 24}
    unfixed_attrs = {key: ds.attrs[key]
                     if key in ds.attrs else ""
                     for key in gattrs
                     }
    attrs = fix_numpy_float_int(unfixed_attrs)
    attrs["date"] = date
    attrs["experiment"] = experiment
    #varlist = list(ds.variables)

    # attrs.pop("_NCProperties")

    variables = {}
    for name in varlist:
        var = ds.variables[name]
        shape = var.shape
        if len(shape) == 1:
            shape = 1
        else:
            shape = shape[1:]
        variables[name] = {"shape": shape,
                           "dtype": var.dtype.name}

        vattrs = fix_numpy_float_int(var.attrs)
        variables[name].update(vattrs)

    infos = {}
    infos["headersize"] = headersize
    infos["stripes"] = stripes
    infos["date"] = date
    infos["dimensions"] = dims
    infos["variables"] = variables
    infos["attrs"] = attrs
    infos["hour"] = hours
    infos["tile"] = tiles
    return infos


def fix_numpy_float_int(attrs):
    vattrs = {key: attrs[key] for key in attrs}
    for key, value in attrs.items():
        if isinstance(value, np.float64) or isinstance(value, np.float32):
            vattrs[key] = float(value)
        if isinstance(value, np.int32):
            vattrs[key] = int(value)
    return vattrs


def allocate_empty_binfile(binfile, filesize):
    if os.path.isfile(binfile):
        print(f"Warning {binfile} already exist")
    else:
        command = f"dd if=/dev/zero of={binfile} bs=1 count=0 seek={filesize}"
        print(command)
        os.system(command)


def convert_grd(subd):
    infos = get_infos(subd)

    target_grid = f"{dirgrid}/{subd:02}/grd_gigatl1_{subd:02}.dat"
    newds = bBDF.Dataset(target_grid)
    newds.set_structure(infos)

    # os.remove(target_grid)
    allocate_empty_binfile(target_grid, newds.filesize)
    newds.write_header()

    tiles = infos["tiles"]

    for k in range(len(tiles)):
        tile = tiles[k]
        idx = (k//100, k % 100)

        grdfile = f"{dirgrid}/{subd:02}/gigatl1_grd_masked.{tile:04}.nc"
        ds = xr.open_dataset(grdfile)

        for name in infos["variables"]:
            print(f"\rtile {tile:04} {name:>20}", end="")
            data = np.asarray(ds.variables[name][:])
            newds.write_variable(name, data, idx)


def read(self, name, tile):
    # function to be attached to an bBDF.Dataset
    tiles = self.infos["tiles"]
    assert tile in tiles
    k = tiles.index(tile)
    idx = (k//100, k % 100)

    return self.read_variable(name, idx)


def read_region(name, subd):
    gridfile = f"{dirgrid}/{subd:02}/grd_gigatl1_{subd:02}.dat"

    ds = bBDF.Dataset(gridfile)
    # let's attach a new function to this object
    # NOT RECOMMENDED at all but does the job
    ds.read = read.__get__(ds)
    infos = ds.get_structure()
    print(infos)

    tiles = infos["tiles"]

    ny, nx = 140, 105
    data = np.zeros((ny*100, nx*100))
    # no need for parallelization, super fast in scalar mode
    for tile in tiles:
        print(f"\rtile:{tile}", end="")
        j0, i0 = ny*(tile//100), nx*(tile % 100)
        data[j0:j0+ny, i0:i0+nx] = ds.read("h", tile)
    return data


def read_regions(name, subds):

    ny, nx = 140, 105
    data = np.zeros((ny*100, nx*100))

    for subd in subds:
        gridfile = f"{dirgrid}/{subd:02}/grd_gigatl1_{subd:02}.dat"

        ds = bBDF.Dataset(gridfile)
        # let's attach a new function to this object
        # NOT RECOMMENDED at all but does the job
        ds.read = read.__get__(ds)
        infos = ds.get_structure()
        # print(infos)

        tiles = infos["tiles"]

        # no need for parallelization, super fast in scalar mode
        for tile in tiles:
            print(f"\rsubd:{subd:02} tile:{tile}", end="")
            j0, i0 = ny*(tile//100), nx*(tile % 100)
            data[j0:j0+ny, i0:i0+nx] = ds.read("h", tile)
    return data


def convert_allgrids():
    for subd in range(1, 14):

        get_netcdf_from_store(subd)
        # really super fast to convert
        convert_grd(subd)


def create_all_headers():
    """
    Create the header files each region

    Headers are stored in yaml files
    """
    subd = 12

    infos = get_infos(subd)

    print(infos)

    header = bBDF.generate_header(infos)
    headerfile = f"header_his_{subd:02}.yaml"
    with open(headerfile, "w") as fid:
        fid.write(header)

    for subd in range(1, 14):
        tiles = [tile for tile, s in param.subdmap.items() if s == subd]
        infos["tile"] = tiles
        infos["dimensions"]["tile"] = len(tiles)
        header = bBDF.generate_header(infos)
        headerfile = f"header_his_{subd:02}.yaml"
        with open(headerfile, "w") as fid:
            fid.write(header)


def test_read():
    subd = 7
    headerfile = f"header_his_{subd:02}.yaml"
    with open(headerfile, "r") as fid:
        header = fid.readlines()
        header = "".join(header)
    print(header)

    dirbin = "/ccc/store/cont003/gch0401/gch0401/GIGATL1_1h_tides/BIN_1h_JG"
    hisdate = "2009-08-14"
    hisdatefile = f"{dirbin}/{subd:02}/giga_{hisdate}_{subd:02}.dat"

    ds = bBDF.Dataset(hisdatefile)
    infos = bBDF.retrieve_infos(header)
    ds.set_structure(infos)
    return ds, infos


def test_newdriver():
    """
    check that the new bBDF driver and the new header
    
    allow to retrieve the same arrays as the previous rgdf drivers did
    """
    subd = 7

    rgdf.setup_predefine_readers(param)
    reader = rgdf.predefined_readers[subd]

    ds, infos = test_read()

    itile = infos["dimensions"]["tile"]-20
    tile = ds.infos["tile"][itile]
    date = ds.filename.split("_")[-2]
    hour = 6
    name = "temp"

    d0 = ds.read_variable(name, (itile, hour))
    off0 = ds.get_offset(name, (itile, hour))

    d1 = reader.read(tile, date, hour, name)
    off1 = reader.get_offset(tile, hour, name)
    fig, ax = plt.subplots(1, 2, sharey=True)
    ax[0].imshow(d0[-1], origin="lower", cmap=cmap)
    im = ax[1].imshow(d1[-1], origin="lower", cmap=cmap)

    print(f"offset[ds]: {off0} offset[reader]: {off1} {off1*4} (x4)")
    print(f"arrays are equal: {np.allclose(d0, d1)}")


if __name__ == "__main__":
    import matplotlib.pyplot as plt
    from parameters import Param
    import rgdf

    plt.ion()

    cmap = "RdBu_r"

    param = Param()
    param.dirgigabin = "/ccc/store/cont003/gch0401/gch0401/GIGATL1_1h_tides/BIN_1h_JG"

    create_all_headers()
