"""
Show how to plot SST on a subdomain

"""
import numpy as np
import marray as ma
import grid as gr
import nctools as nct
import croco as croco
import giga_tools as giga
import giga_subdomains as gs
import matplotlib.pyplot as plt
import matplotlib.colorbar as cb
import schwimmbad
import time

rc = plt.rc
font = {'family': "Comic Sans MS",
        'size': 16}
rc('font', **font)

plt.ion()


def get_sst(iblock):
    """ process the`iblock`-th block from `blocks` list"""
    block = blocks[iblock]
    grid = croco.load_grid(giga.grdfiles, block, giga.dimpart,
                           giga.nsigma, halow=halow)
    # the grid MDataset is needed to get the sizes of the possibly
    # missing tiles in the history files
    ncgrid = nct.MDataset(giga.grdfiles, block, giga.dimpart, halow=halow)

    # ncgrid.sizes is sent to the history MDataset
    nch = nct.MDataset(giga.hisfiles, block, giga.dimpart,
                       halow=halow, gridsizes=ncgrid.sizes)

    # because of nelem=5, ncread extracts the timeindex=5
    # from nch and returns a 3D array. slice(-1) extracts
    # the top level, hence the sst
    sst = croco.ncread(nch, grid, "temp", elem=5).slice(-1)

    # to access grid coordinates use the functions the `stagg` keyword
    # returns the coordinate at the correct location, here at f-point
    xf = grid.xi(stagg=croco.fpoint)
    yf = grid.eta(stagg=croco.fpoint)
    return (iblock, (xf, yf, sst))


# halo width set to zero because we don't need any halo in this case
halow = 0

# parallelization is done on blocks of 3x3 tiles
blocksize = 3

# Gibraltar region ((lon west, lat south), (lon east, lat north))
domain = gs.LLTR2domain((-10, 32), (0, 40))
tileslist = gs.find_tiles_inside(domain)

# blocks is the list of blocks
# subds is the list of subdomains that need to be mounted
subds, blocks = gs.get_blocks_subds_from_tiles(tileslist, blocksize)

if giga.rank == 0:
    # check out the figure to understand tileslist and blocks
    gs.plot_blocks(domain, tileslist, blocks, "../figures/demo_1_blocks.png")

for subd in subds:
    # don't forget to mount the history tar files
    giga.mount(subd)

# pool the SST read with as many threads as number of cores
pool = schwimmbad.MultiPool()
t0 = time.time()

res = pool.map(get_sst, range(len(blocks)))
# don't forget, if pool is not closed then no worker will
# go beyond that point

t1 = time.time()
elapsed = t1-t0
print(f"elapsed time: {elapsed:.2f}s")

# Do the figure
cmap = "YlGnBu_r"
plt.figure(figsize=(7, 7))
for r in res:
    iblock, data = r
    plt.pcolormesh(*data, vmin=17, vmax=25, cmap=cmap)

hc = plt.colorbar(orientation="horizontal")
cb.ColorbarBase.set_label(hc, "SST [°C]")
plt.xlabel("Longitude")
plt.ylabel("Latitude")
plt.tight_layout()
plt.savefig("../figures/demo_1.png")
