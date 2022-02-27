import xarray as xr
import numpy as np
import bBDF
import glob
import os

targrid = "/ccc/store/cont003/gch0401/gch0401/GIGATL1_1h_tides/GRD"
dirgrid = "/ccc/scratch/cont003/gen12051/groullet/giga/GRD"


def get_netcdf_from_store(subd):
    tarfile = f"{targrid}/{subd:02}/gigatl1_grd_masked.{subd:02}.tar"
    ierr = os.system(f"ccc_hsm status {tarfile}")
    os.system(f"cp {tarfile} {dirgrid}/{subd:02}/")
    os.system(f"cd {dirgrid}/{subd:02} ; tar xvf {tarfile}")


def get_infos(subd):

    files = glob.glob(f"{dirgrid}/{subd:02}/*nc")
    tiles = sorted([int(f.split(".")[1]) for f in files])
    ntiles = len(files)

    grdfile = files[0]

    ds = xr.load_dataset(grdfile)

    headersize = 29400
    stripes = {"size": 177848320, "roundingsize": 1024}

    dims = {"chunk": ntiles//100+1, "tile": 100}
    attrs = ds.attrs
    varlist = list(ds.variables)

    attrs.pop("_NCProperties")
    attrs["partition_ucla"] = [0, 10000,     1,     1]
    varlist.remove("spherical")

    variables = {}
    for name in varlist:
        var = ds.variables[name]
        variables[name] = {"shape": list(var.shape),
                           "dtype": var.dtype.name}

        vattrs = var.attrs
        for key, value in var.attrs.items():
            if isinstance(value, np.float64):
                vattrs[key] = float(value)
            if isinstance(value, np.int32):
                vattrs[key] = int(value)
        variables[name].update(vattrs)

    infos = {}
    infos["headersize"] = headersize
    infos["stripes"] = stripes
    infos["dimensions"] = dims
    infos["variables"] = variables
    infos["attrs"] = attrs
    infos["tiles"] = tiles
    return infos


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


if __name__ == "__main__":
    from matplotlib import pyplot as plt
    plt.ion()

    convert_allgrids()

    h = read_regions("h", list(range(1, 14)))
    plt.imshow(h, origin="lower")
