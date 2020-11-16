"""
Demo 4: illustrate how to do a vertical interpolation, from sigma
coordinates to specified depths

"""
import numpy as np
import nctools as nct
import giga_tools as giga
import croco as croco
import vinterp
import matplotlib.pyplot as plt
import matplotlib.colorbar as cb

rc = plt.rc
font = {'family': "Comic Sans MS",
        'size': 16}
rc('font', **font)

plt.ion()

# define a block of tiles (this one below is Gulf Stream)
tileblock = (range(78, 83), range(25, 32))

blocks = {"partition": giga.partition,
          "tileblock": tileblock}

halow = 10

g = croco.load_grid(giga.grdfiles, blocks, giga.dimpart,
                    giga.nsigma, halow=halow)


# the grid MDataset is needed to get the sizes of the possibly
# missing tiles in the history files
ncgrid = nct.MDataset(giga.grdfiles, blocks, giga.dimpart, halow=halow)

# ncgrid.sizes is sent to the Surface MDataset
nch = nct.MDataset(giga.hisfiles, blocks, giga.dimpart,
                   halow=halow, gridsizes=ncgrid.sizes)

# restrict grid to have only one element in time
g.sizes["t"] = 1


kt = 0
# read temp as marray (only one snapshot)
temp = croco.ncread(nch, g, "temp", elem=kt)
time = nch.variables["time"]

# set target depths
zout = np.asarray([-2000, -1000, -500, -200, -100])
zr = croco.sigma2z(g)

# interpolate a depths `zout`
temp_z = vinterp.Vinterp3d(g, temp, zr[0], zout)

# get grid coordinates @ f-point
xf = g.xi(stagg=croco.fpoint)
yf = g.eta(stagg=croco.fpoint)

cmap = "YlGnBu_r"

kz = 2
plt.figure(figsize=(10, 7))
plt.pcolormesh(xf, yf, temp_z[kz], vmin=10, vmax=32, cmap=cmap)

# TODO transform time[kt] into a datetime
plt.title(f"time = {time[kt]:.2f}")
hc = plt.colorbar(orientation="horizontal")
cb.ColorbarBase.set_label(hc, f"Temperature [°C] at {zout[kz]:.0f} m")

plt.xlabel("Longitude")
plt.ylabel("Latitude")
plt.tight_layout()
plt.savefig("../figures/demo_4.png")
