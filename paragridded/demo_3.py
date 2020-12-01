import nctools as nct
import giga_tools as giga
import giga_subdomains as gs
import croco as croco
import matplotlib.pyplot as plt
import matplotlib.colorbar as cb

rc = plt.rc
font = {'family': "Comic Sans MS",
        'size': 16}
rc('font', **font)

plt.ion()

# define a block of tiles (this one below is Florida)
tileblock = (range(80, 85), range(20, 25))

block = {"partition": giga.partition,
         "tileblock": tileblock}

subds = gs.get_subds_from_block(block)
for subd in subds:
    giga.mount(subd)

halow = 10

grid = croco.load_grid(giga.grdfiles, block, giga.dimpart,
                       giga.nsigma, halow=halow)


# the grid MDataset is needed to get the sizes of the possibly
# missing tiles in the history files
ncgrid = nct.MDataset(giga.grdfiles, block, giga.dimpart, halow=halow)

# ncgrid.sizes is sent to the Surface MDataset
ncs = nct.MDataset(giga.surffiles, block, giga.dimpart,
                   halow=halow, gridsizes=ncgrid.sizes)

# let's inspect the objects
print(grid)
print(ncgrid)
print(ncs)

# read time from ncs
time = ncs.variables["time"][:]

# read SSH
zeta0 = ncs.variables["zeta"][:]

# zeta is a plain ndarray, without metadata
# if we want to have a marray
zeta = croco.ncread(ncs, grid, "zeta")

# these are the two same data
assert ((zeta0-zeta) == 0).all()

# but zeta is richer, it has its metadata
print(zeta)


# get grid coordinates @ f-point
xf = grid.xi(stagg=croco.fpoint)
yf = grid.eta(stagg=croco.fpoint)

zeta0 = zeta[0]
cmap = "RdBu_r"

# time index
kt = 10

plt.figure(figsize=(7, 7))
plt.pcolormesh(xf, yf, zeta[kt]-zeta0, vmin=-0.5, vmax=0.5, cmap=cmap)

# TODO transform time[kt] into a datetime
plt.title(f"time = {time[kt]:.2f}")
hc = plt.colorbar(orientation="horizontal")
cb.ColorbarBase.set_label(hc, r"$\Delta$SSH [m]")

plt.xlabel("Longitude")
plt.ylabel("Latitude")
plt.tight_layout()
plt.savefig("../figures/demo_3.png")
