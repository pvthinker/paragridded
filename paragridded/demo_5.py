"""
Demo 5: same as demo 4 but in parallel mode + a more rectangular domain

Time to read and interpolate:  6.96s on 89 tiles
"""
import numpy as np
import nctools as nct
import giga_tools as giga
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

halow = 0


def get_temp(tile):
    blocks = {"partition": giga.partition,
              "tileblock": tile}

    g = croco.load_grid(giga.grdfiles, blocks, giga.dimpart,
                        giga.nsigma, halow=halow)

    ncgrid = nct.MDataset(giga.grdfiles, blocks, giga.dimpart, halow=halow)

    nch = nct.MDataset(giga.hisfiles, blocks, giga.dimpart,
                       halow=halow, gridsizes=ncgrid.sizes)

    g.sizes["t"] = 1

    # read temp as marray (only one snapshot)
    temp = croco.ncread(nch, g, "temp", elem=kt)
    time = nch.variables["time"]

    zr = croco.sigma2z(g)

    # interpolate a depths `zout`
    temp_z = vinterp.Vinterp3d(g, temp, zr[0], zout)

    # get grid coordinates @ f-point
    xf = g.xi(stagg=croco.fpoint)
    yf = g.eta(stagg=croco.fpoint)
    temp_z[temp_z == 999.] = np.nan
    return (tile, (xf, yf, temp_z[kz]))


cmap = "YlGnBu_r"

# set target depths
zout = np.asarray([-2000, -1000, -500, -200, -100])
kt = 0
kz = 2

# Gulf Stream region
domain = giga.LLTP2domain((-79., 27.), (-69., 35.))
tileslist = giga.find_tiles_inside(domain, giga.corners)

# pool the interpolation with as many threads as number of cores
pool = schwimmbad.MultiPool()
t0 = time.time()
res = pool.map(get_temp, tileslist)
t1 = time.time()
elapsed = t1-t0
print(f"elapsed time: {elapsed:.2f}s on {len(tileslist)} tiles")

plt.figure(figsize=(10, 7))
for r in res:
    t, data = r
    plt.pcolormesh(*data, vmin=10, vmax=32, cmap=cmap)

hc = plt.colorbar(orientation="horizontal")
cb.ColorbarBase.set_label(hc, f"Temperature [°C] at {zout[kz]:.0f} m")

plt.xlabel("Longitude")
plt.ylabel("Latitude")
plt.tight_layout()
plt.savefig("../figures/demo_5.png")
