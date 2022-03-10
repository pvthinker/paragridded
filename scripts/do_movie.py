"""
Show how to build a movie

The IO and the plot is multi-threaded

In addition this script can be launched with MPI
"""
import bindatasets as bd
from time import time as cputime
import itertools
import movietools
from mpi4py import MPI
import schwimmbad
import numpy as np
import gigatl
import matplotlib as mpl
mpl.use('Agg')


comm = MPI.COMM_WORLD

myrank = comm.Get_rank()
nworkers = comm.Get_size()
ismaster = (myrank == 0)

print(f"rank: {myrank:02}/{nworkers}", flush=True)

nthreads = 12
ndays_per_batch = 2

# plt.ion()

if ismaster:
    print("open HIST")
ds = bd.Dataset()
if ismaster:
    print("open GRID")
grid = bd.GDataset()

domain = [(-40, 46), (0, 60)]
domain = [(-40, 50), (0, 65)]
#domain = [(-30, 50), (-20, 60)]
tiles = gigatl.get_tiles_inside(domain)
subds = gigatl.get_subds_from_tiles(tiles)


def proceed_tile(args):
    tile, hour, date = args
    temp = ds.read(("temp", tile, hour, date))
    data = temp[-1]-temp[-2]
    return data


def get_data(tiles, date, hour):
    if ismaster:
        print(
            f"read HIST {date}:{hour:02} #tiles: {len(tiles)} in {subds}", flush=True)
    tasks = [(tile, hour, date) for tile in tiles]
    pool = schwimmbad.MultiPool(processes=nthreads)
    data = pool.map(proceed_tile, tasks)
    pool.close()
    return data


if ismaster:
    print(f"read GRID #tiles: {len(tiles)} in {subds}")
lons = grid.pread(("lon_rho", tiles))
lats = grid.pread(("lat_rho", tiles))

dates = ds.dates

k0 = 100 + myrank
k1 = k0 + ndays_per_batch*nworkers
mydates = dates[k0:k1:nworkers]

vmin = 6.
vmax = 16.
varname = "temp"

vmin = -0.015
vmax = 0.015
varname = "dtemp"

# vmin = -1.
# vmax = 1.
# varname = "zeta"


cmap = "RdBu_r"
axis = gigatl.domaintoaxis(domain)


def analyze(temps):
    return [temp[-1]-temp[-2]
            for temp in temps]


if False:
    hmap = movietools.HorizMap(1080)
    hmap._createdir()
    hmap.setup_colorbar((vmin, vmax, cmap))
    hmap.setup_domain((axis, lons, lats))

    date = dates[0]
    for hour in range(24):
        data = get_data(tiles, date, hour)
        hmap.plot_frame((data, date, hour))
        hmap.save_frame()

else:
    thm = movietools.ThreadedHorizMap(720, 12)
    thm.check()
    thm.setup_colorbar((vmin, vmax, cmap))
    time_read = 0.
    time_video = 0.
    time_total = 0.
    nframes = 0
    for date, hour in itertools.product(mydates, range(24)):
        t0 = cputime()
        assert ds.is_datetiles_online(tiles, date), comm.Abort()
        data = get_data(tiles, date, hour)
        t1 = cputime()
        thm.do_frame((axis, lons, lats), (data, date, hour))
        t2 = cputime()
        time_read += t1-t0
        time_video += t2-t1
        time_total += t2-t0
        nframes += 1
        if True:
            print(
                f"myrank: {myrank} io:{time_read:.1f} video:{time_video:.1f} total:{time_total:.1f} nframes:{nframes} timeperframe:{time_total/nframes:.2f}")
    thm.close()
# pool.close()
print(f"myrank: {myrank} DONE")
