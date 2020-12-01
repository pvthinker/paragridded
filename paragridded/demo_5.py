"""
Demo 5: same as demo 4 but in parallel mode + a more rectangular domain

Time to read and interpolate:  6.96s on 89 tiles
"""
import numpy as np
import nctools as nct
import giga_tools as giga
import giga_subdomains as gs
import croco as croco
import vinterp
import matplotlib.pyplot as plt
import matplotlib.colorbar as cb
import schwimmbad
import time

rc = plt.rc
font = {'family': "Comic Sans MS",
        'size': 16}
rc('font', **font)

plt.ion()



def get_temp(iblock):
    block = blocks[iblock]

    grid = croco.load_grid(giga.grdfiles, block, giga.dimpart,
                        giga.nsigma, halow=halow)

    ncgrid = nct.MDataset(giga.grdfiles, block, giga.dimpart, halow=halow)

    nch = nct.MDataset(giga.hisfiles, block, giga.dimpart,
                       halow=halow, gridsizes=ncgrid.sizes)

    grid.sizes["t"] = 1

    # read temp as marray (only one snapshot)
    temp = croco.ncread(nch, grid, "temp", elem=kt)
    time = nch.variables["time"]

    zr = croco.sigma2z(grid)

    # interpolate a depths `zout`
    temp_z = vinterp.Vinterp3d(grid, temp, zr[0], zout)

    # get grid coordinates @ f-point
    xf = grid.xi(stagg=croco.fpoint)
    yf = grid.eta(stagg=croco.fpoint)
    temp_z[temp_z == 999.] = np.nan
    return (iblock, (xf, yf, temp_z[kz]))


cmap = "YlGnBu_r"

# set target depths
zout = np.asarray([-2000, -1000, -500, -200, -100])
kt = 0
kz = 2

halow = 0
blocksize = 3

# Gulf Stream region
domain = gs.LLTR2domain((-79., 27.), (-69., 35.))
tileslist = gs.find_tiles_inside(domain)
subds, blocks = gs.get_blocks_subds_from_tiles(tileslist, blocksize)

if giga.rank == 0:
    # check out the figure to understand tileslist and blocks
    gs.plot_blocks(domain, tileslist, blocks, "../figures/demo_5_blocks.png")

for subd in subds:
    # don't forget to mount the history tar files
    giga.mount(subd)

# pool the interpolation with as many threads as number of cores
pool = schwimmbad.MultiPool()
t0 = time.time()
res = pool.map(get_temp, range(len(blocks)))
t1 = time.time()
elapsed = t1-t0
print(f"elapsed time: {elapsed:.2f}s on {len(tileslist)} tiles")

plt.figure(figsize=(10, 7))
for r in res:
    iblock, data = r
    plt.pcolormesh(*data, vmin=10, vmax=32, cmap=cmap)

hc = plt.colorbar(orientation="horizontal")
cb.ColorbarBase.set_label(hc, f"Temperature [°C] at {zout[kz]:.0f} m")

plt.xlabel("Longitude")
plt.ylabel("Latitude")
plt.tight_layout()
plt.savefig("../figures/demo_5.png")
