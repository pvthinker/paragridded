import numpy as np
import marray as ma
import grid as gr
import nctools as nct
import croco as croco
import giga_tools as giga
import matplotlib.pyplot as plt
import matplotlib.colorbar as cb
import schwimmbad
import time

rc = plt.rc
font = {'family': "Comic Sans MS",
        'size': 16}
rc('font', **font)

plt.ion()


def get_sst(tile):
    blocks = {"partition": giga.partition,
              "tileblock": tile}

    g = croco.load_grid(giga.grdfiles, blocks, giga.dimpart,
                        giga.nsigma, halow=halow)
    # the grid MDataset is needed to get the sizes of the possibly
    # missing tiles in the history files
    ncgrid = nct.MDataset(giga.grdfiles, blocks, giga.dimpart, halow=halow)
    
    # ncgrid.sizes is sent to the history MDataset
    nch = nct.MDataset(giga.hisfiles, blocks, giga.dimpart,
                       halow=halow, gridsizes=ncgrid.sizes)

    # because of nelem=5, ncread extracts the timeindex=5
    # from nch and returns a 3D array. slice(-1) extracts
    # the top level, hence the sst
    sst = croco.ncread(nch, g, "temp", elem=5).slice(-1)

    # to access grid coordinates use the functions the `stagg` keyword
    # returns the coordinate at the correct location, here at f-point
    xf = g.xi(stagg=croco.fpoint)
    yf = g.eta(stagg=croco.fpoint)
    return (tile, (xf, yf, sst))


halow = 0

# Gibraltar region
domain = giga.LLTP2domain((-10, 32), (0, 40))
tileslist = giga.find_tiles_inside(domain, giga.corners)

# pool the SST read with as many threads as number of cores
pool = schwimmbad.MultiPool()
t0 = time.time()
res = pool.map(get_sst, tileslist)
t1 = time.time()
elapsed = t1-t0
print(f"elapsed time: {elapsed:.2f}s")

# Do the figure
cmap = "YlGnBu_r"
plt.figure(figsize=(7, 7))
for r in res:
    t, data = r
    plt.pcolormesh(*data, vmin=17, vmax=25, cmap=cmap)

hc = plt.colorbar(orientation="horizontal")
cb.ColorbarBase.set_label(hc, "SST [°C]")
plt.xlabel("Longitude")
plt.ylabel("Latitude")
plt.tight_layout()
plt.savefig("../figures/demo_1.png")
