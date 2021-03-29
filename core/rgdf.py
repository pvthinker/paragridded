import numpy as np
from pretty import BB, MD, VA
from ruamel import yaml
from netCDF4 import Dataset as ncDataset
import os

debug = False


def roundup(x, y):
    return int(y*np.ceil(x/y))


kiB = 1024
MiB = 1024**2
GiB = 1024**3
kB = int(1e3)
MB = int(1e6)
GB = int(1e9)

floattypes = {4: np.float32, 8: np.float64}
floatsize = 4

hours = range(24)
quarters = range(4)
nz, ny, nx = 100, 140, 105


predefined_readers = {}
subdomains = {}

def setup_predefine_readers(param):
    subds = param.subdmap
    # trick to read the subdomains and make them global
    # for this module
    for key, val in subds.items():
        subdomains[key] = val

    for subd in range(1, 14):
        predefined_readers[subd] = Reader(param, subd)
        
class Reader(object):
    def __init__(self, param, subd):
        self.datadir = param.dirgigabin
        self.subd = subd
        yamfile = f"{param.dirmodule}/data/giga_{subd:02}.yaml"
        with open(yamfile) as f:
            data = yaml.load(f, yaml.RoundTripLoader)

        levels = data["levels"]
        nlevels = len(levels)

        filename = data["filename"]
        atom = tuple(data["atom"])
        atomsize = np.prod(atom)
        headersize = data["header"]*atomsize
        variable_level = levels.index("variable")
        variables = data["definitions"]["variable"]
        stripes = data["stripes"]

        varsizes = [data["variable_size"][var]*atomsize
                    for var in variables]

        offset = {}
        assert levels[-1] == "variable"
        assert levels[0] == stripes["level"]

        for level in levels[::-1]:

            nelem = len(data["definitions"][level])

            if level == "variable":
                varsize = data["variable_size"]
                sizes = [varsize[var]*atomsize for var in variables]
                variable_sizes = sizes

            elif level == stripes["level"]:
                # roundup prev size to upper value
                unit = stripes["unit"]
                nelemperstripe = stripes["nelements"]
                currentsize = headersize+prev_size*nelemperstripe
                # transform in bytes then back in number of float
                stripesize = roundup(currentsize*floatsize, unit)//floatsize
                paddingsize = stripesize-currentsize

                sizes = [prev_size]*nelemperstripe
                nstripes = nelem // nelemperstripe
                nelem_laststripe = nelem % nelemperstripe
                if nelem_laststripe > 0:
                    nstripes += 1

                filesize = nstripes*stripesize*floatsize
                if debug:
                    print(BB(f" stripe properties:"))
                    print(f"size is rounded up: {currentsize} -> {stripesize}")
                    print(f"      padding size: {paddingsize}")
                    print(
                        f"        stripesize: {stripesize*floatsize}  B  ({stripesize*floatsize//MB:.2f}  MB)")
                    print(f" number of stripes: {nstripes}")
                    print(BB(f"          filesize: {filesize/GB:.2f} GB"))

                assert (stripesize*floatsize) < 4*GB
            else:
                sizes = [prev_size]*nelem

            offset[level] = [0] + list(np.cumsum(sizes))
            prev_size = offset[level][-1]

        variable_shape = {}
        for varname in variables:
            natoms = data["variable_size"][varname]
            if natoms == 1:
                shape = atom
            else:
                shape = (natoms,) + atom
            variable_shape[varname] = shape
            
        self.levels = levels
        self.data = data
        self.atom = atom
        self.stripes = stripes
        self.nelemperstripe = nelemperstripe
        self.stripesize = stripesize
        self.headersize = headersize
        self.offset = offset
        self.variable_shape = variable_shape
        self.variables = variables

    def get_offset(self, *args, debug=False):
        # convert plain arguments to dict of index
        index = {}
        for k, level in enumerate(self.levels):
            index[level] = self.data["definitions"][level].index(args[k])

        lev = self.stripes["level"]
        stripeindex = index[lev] // self.nelemperstripe
        index[lev] = index[lev] % self.nelemperstripe
        if debug:
            print(index)
            print(f"stripeindex: {stripeindex}")

        offset = stripeindex*self.stripesize + self.headersize
        for level in self.levels:
            i = index[level]
            offset += self.offset[level][i]
        return offset

    def read(self, tile, date, hour, varname):
        offset = self.get_offset(tile, hour, varname)
        shape = self.variable_shape[varname]
        count = np.prod(shape)
        dtype = floattypes[floatsize]
        filename = datafilename(self.datadir, date, self.subd)
        data = np.fromfile(filename, count=count, offset=offset*floatsize, dtype=dtype)
        data.shape = shape
        return data

    def write(self, tile, date, hour, varname, data):
        offset = self.get_offset(tile, hour, varname)
        shape = self.variable_shape[varname]
        count = np.prod(shape)
        dtype = floattypes[floatsize]
        filename = datafilename(self.datadir, date, self.subd)
        with open(filename, "rb+") as fid:
            fid.seek(offset*floatsize) # <- conversion to bytes
            fid.write(data.tobytes())

    def read_ts(self, tile, loc, dates, varname):
        """ Read a timeseries at a given location

        Parameters
        ----------
        loc : tuple of index
            Location within the tile, either (j, i) or (k, j, i)
        dates : list of date
        """
        dtype = floattypes[floatsize]
        nt = len(dates)*24
        data = np.zeros((nt, ), dtype=dtype)
        shape = self.variable_shape[varname]

        if len(shape) == 2:
            j, i = loc
            location_offset = i+j*shape[-1]
        else:
            k, j, i = loc
            location_offset = i+(j+k*shape[-2])*shape[-1]
        kt = 0
        for date in dates:
            filename = datafilename(self.datadir, date, self.subd)
            for hour in range(24):
                offset = self.get_offset(tile, hour, varname) + location_offset
                data[kt] = np.fromfile(filename, count=1, offset=offset*floatsize, dtype=dtype)
                kt += 1
        return data

def datafilename(datadir, date, subd):
    filename = f"{datadir}/{subd:02}/giga_{date}_{subd:02}.dat"
    return filename

def touchfirstelement(*args):
    if len(args) == 5:
        subd, tile, date, hour, varname = args
    else:
        subd, tile, date, hour, varname = args[0]

    reader = predefined_readers[subd]
    offset = reader.get_offset(tile, hour, varname)
    filename = datafilename(reader.datadir, date, subd)
    data = np.fromfile(filename, count=1, offset=offset, dtype=np.float32)
    return None


def read(tile, date, hour, varname):
    subd = subdomains[tile]
    reader = predefined_readers[subd]
    return reader.read(tile, date, hour, varname)


def writesubd(date, tile, hisfiles):

    # allocate the buffer (largest one) that host the data
    # from the netCDF to the GDF file
    shape = (nz+1, ny, nx)
    data = np.zeros(shape, dtype=np.float32)


    subd = subdomains[tile]
    reader = predefined_readers[subd]
    datadir = reader.datadir
    filename = datafilename(datadir, date, subd)
    assert os.path.isfile(filename)

    for quarter in range(4):
        ncfile = hisfiles[quarter]
        with ncDataset(ncfile) as nc:
            for varname in reader.variables:
                varshape = reader.variable_shape[varname]
                ndim = len(varshape)
                ncshape = nc.variables[varname].shape

                vidx, oidx, iidx = set_indices(varshape, ncshape, tile)

                with open(filename, "rb+") as fid:
                    for kt in range(6):
                        hour = quarter*6+kt
                        data[vidx].flat = 0.
                        datain = nc.variables[varname][kt]
                        if ndim == 3:
                            data[(vidx,)+oidx] = datain[(vidx,)+iidx]
                        else:
                            data[(vidx,)+oidx] = datain[iidx]

                        offset = reader.get_offset(tile, hour, varname)
                        fid.seek(offset*floatsize)
                        fid.write(data[vidx].tobytes())
                print(f"\rwrite {date} {subd:02} {tile:04} {quarter} {varname}", end="", flush=True)
    print(f"\rwrite {date} {subd:02} {tile:04} -> done", flush=True)

def set_indices(varshape, ncshape, tile):
    ndim = len(varshape)
    if ndim == 2:
        vidx = 0
    else:
        vidx = slice(0, varshape[0])

    oidx = (slice(0, ny), slice(0, nx))
    iidx = (slice(0, ny), slice(0, nx))
    south = tile<100
    if south and ncshape[-2] > ny:
        iidx = (slice(1, ny+1), slice(0, nx))
        
    return vidx, oidx, iidx

