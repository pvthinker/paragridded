from parameters import Param
import rgdf
import matplotlib.pyplot as plt
import time
import glob
import schwimmbad
import numpy as np
from netCDF4 import Dataset
import iotools
import datetime

plt.ion()

# load the paragridded parameters
param = Param()

param.dirgigabin = "/ccc/store/cont003/gch0401/gch0401/GIGATL1_1h_tides/BIN_1h_JG"

param.dirgrid = "/ccc/scratch/cont003/ra4735/gulaj/GIGATL1/INIT_N100_100_100/GRD3"
param.dirgrid = "/ccc/scratch/cont003/gen12051/groullet/giga/GRD"

# setup readers 
rgdf.setup_predefine_readers(param)

# list of tiles in region 7
reg7 = [t for t,r in param.subdmap.items() if r==7]

def get_alldates(datadir, subd):
    """ return the dates converted into dat file"""
    files = glob.glob(f"{datadir}/{subd:02}/*.dat")
    dates = [f.split("_")[-2] for f in files]
    return sorted(dates)

ncfile = "../mooring/gmacmd_cut_uniqindeces.nc"

jr = []
ir = []
ju = []
iu = []
jv = []
iv = []
with Dataset(ncfile) as nc:
    for k in range(3):
        jr += [nc.variables[f"jr{k}"][:]]
        ir += [nc.variables[f"ir{k}"][:]]

        ju += [nc.variables[f"ju{k}"][:]]
        iu += [nc.variables[f"iu{k}"][:]]

        jv += [nc.variables[f"jv{k}"][:]]
        iv += [nc.variables[f"iv{k}"][:]]

nmoorings = len(ir[0])

ny = 140
nx = 105

def loc2tile(i,j):
    return (i // nx) + (j//ny)*100


tiles = [(i // nx) + (j//ny)*100 for i,j in zip(ir[0], jr[0])]
tile1 = [(i // nx) + (j//ny)*100 for i,j in zip(ir[1], jr[1])]
tile2 = [(i // nx) + (j//ny)*100 for i,j in zip(ir[2], jr[2])]

subds = [param.subdmap[t] for t in tiles]


subd = 8
dates = get_alldates(param.dirgigabin, subd)
reader = rgdf.predefined_readers[subd]

nworkers = 16

def get_status_date(datadir, date, subd):
    filename = rgdf.datafilename(datadir, date, subd)
    return rgdf.get_filestatus(filename)

def myreader(args):
    tile, loc, date, varname = args
    return reader.read_ts(tile, loc, [date], varname)

pool = schwimmbad.MultiPool(processes=nworkers+1)

ks = [k for k in range(nmoorings) if subds[k]==subd]

k = ks[0]
tile = tiles[k]
assert tile1[k] == tile
assert tile2[k] == tile


loc = (jr[0][k] % ny, ir[0][k] %nx)
varname = "zeta"



tasks = [(tile, loc, date, varname) for date in dates]



tic = time.time()
result = pool.map(myreader,tasks)
data = np.concatenate(result)
toc = time.time()
elapsed = toc-tic
print(f"time to read the time series ({len(data)} elements): {elapsed:.3g} s")

exit()


attrs = {"title": "mooring time series from gigatl 1",
         "mooringindex": k,
         "time_resolution": "1 hour",
     }

def decode_date(date):
    y,m,d = date.split("-")
    y = int(y)
    m = int(m)
    d = int(d)
    return (y,m,d)

if subd == 8:
    dates = dates[:-2]
    
decoded_dates = [decode_date(d) for d in dates]
d0 = datetime.date(2008,1,1)
times = [(datetime.date(y,m,d)-d0).days for y,m,d in decoded_dates]

d0 = datetime.date(2008,1,1)
dstart = datetime.date(*decode_date(dates[0]))

dshift = (dstart-d0).days

assert np.allclose(np.diff(times), 1.)

nt = len(dates)*24
nz = 100

time = dshift+np.arange(nt)/24

dims = [("time", nt), ("hindex", 3), ("level", nz), ("w_level", nz+1)]



infos = [
    ("time", ("time",), "date", "days since 2008-01-01"),
    ("jr", ("hindex",), "j-index @ r-point" ,"", "i"),
    ("ir", ("hindex",), "i-index @ r-point" ,"", "i"),
    ("ju", ("hindex",), "j-index @ u-point" ,"", "i"),
    ("iu", ("hindex",), "i-index @ u-point" ,"", "i"),
    ("jv", ("hindex",), "j-index @ v-point" ,"", "i"),
    ("iv", ("hindex",), "i-index @ v-point" ,"", "i"),
    ("zeta", ("time", "hindex"), "SSH", "m"),
    ("ubar", ("time", "hindex"), "along-i barotropic velocity", "m s^-1"),
    ("vbar", ("time", "hindex"), "along-j barotropic velocity", "m s^-1"),
    ("temp", ("time", "hindex", "level"), "temperature", "deg C"),
    ("salt", ("time", "hindex", "level"), "salinity", "psu"),
    ("AKv", ("time", "hindex", "w_level"), "vertical mixing coefficient", "m^2 s^-1"),
    ("u", ("time", "hindex", "level"), "along-i velocity", "m s^-1"),
    ("v", ("time", "hindex", "level"), "along-j velocity", "m s^-1"),
]

varinfos = [iotools.VariableInfo(*info) for info in infos]

mooringfile = f"mooring_{k:03}.nc"

nc=iotools.NetCDF_tools(mooringfile, attrs, dims, varinfos)
nc.create()
nc.write({"time": time})
irs = np.asarray([ir[hindex][k] for hindex in range(3)])
jrs = np.asarray([jr[hindex][k] for hindex in range(3)])
ius = np.asarray([iu[hindex][k] for hindex in range(3)])
jus = np.asarray([ju[hindex][k] for hindex in range(3)])
ivs = np.asarray([iv[hindex][k] for hindex in range(3)])
jvs = np.asarray([jv[hindex][k] for hindex in range(3)])
nc.write({"ir": irs, "jr": jrs})
nc.write({"iu": ius, "ju": jus})
nc.write({"iv": ivs, "jv": jvs})
#exit()

varname = "zeta"

varnames = ["zeta", "temp", "salt", "AKv"]

# for varname in varnames:
#     shape = reader.variable_shape[varname]
#     if len(shape) == 2:
#         data = np.zeros((3, nt))
#         extraloc = ()
        
#     elif len(shape) == 3:
#         nz = shape[0]
#         data = np.zeros((3, nt, nz))
#         extraloc = (...,)

#     for hindex in range(3):
#         print(f"variable: {varname} / hindex: {hindex}")
#         loc = extraloc + (jr[hindex][k] % ny, ir[hindex][k] %nx)

        # tasks = [(tile, loc, date, varname) for date in dates]

        # result = pool.map(myreader,tasks)
        # data[hindex] = np.concatenate(result)

        # nc.write({varname:data})

def readlocs(args):
    """ read time series for several locations at a time
    if varname is a 3D variable then the whole vertical is return"""
    reader, tile, date, varname, locs = args
    jdx, idx = locs
    nlocs = len(jdx)
    shape = reader.variable_shape[varname]
    if len(shape)==3:
        nz = shape[0]
        result = np.zeros((24, nlocs, nz))
    else:
        result = np.zeros((24, nlocs))
    for hour in range(24):
        data=reader.read(tile, date, hour, varname)
        for k in range(nlocs):
            result[hour, k, ...] = data[..., jdx[k], idx[k]]
    return result

pool = schwimmbad.MultiPool(processes=nworkers+1)

jdx = list(jus%ny)
idx = list(ius%nx)
locs = (jdx,idx)

for varname in ["u","ubar"]:
    print(f"processing {varname}")
    tasks = [(reader, tile, date, varname, locs) for date in dates]
    result = pool.map(readlocs,tasks)
    data = np.concatenate(result)
    nc.write({varname:data})

jdx = list(jvs%ny)
idx = list(ivs%nx)
locs = (jdx,idx)

for varname in ["v","vbar"]:
    print(f"processing {varname}")
    tasks = [(reader, tile, date, varname, locs) for date in dates]
    result = pool.map(readlocs,tasks)
    data = np.concatenate(result)
    nc.write({varname:data})

jdx = list(jrs%ny)
idx = list(irs%nx)
locs = (jdx,idx)

for varname in varnames:
    print(f"processing {varname}")
    tasks = [(reader, tile, date, varname, locs) for date in dates]
    result = pool.map(readlocs,tasks)
    data = np.concatenate(result)
    nc.write({varname:data})

