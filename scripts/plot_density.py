"""
Read one tile at a given (date, hour)
Compute the density (-> eos)
Compute the temperature @ 1000m (-> vertical interpolation)

Plot the density in the bottom level
Plot the temperature @ 1000m
"""
import gigatl
import croco_functions as croco
import vert_coord
import vinterp
from carrays import CArray
import numpy as np

from matplotlib import pyplot as plt
import bindatasets as bd


plt.ion()


rho0 = 1027.4000244140625

nz, ny, nx = 100, 140, 105
N, hmin, Tcline, theta_s, theta_b = vert_coord.gigatl()

Cs_w = CArray((nz+1,))
Cs_r = CArray((nz,))

hc, cs_w, cs_r = vert_coord.set_scoord(nz, hmin, Tcline, theta_s, theta_b)
Cs_w[:] = cs_w
Cs_r[:] = cs_r

z_r = CArray((nz, ny, nx))
z_w = CArray((nz+1, ny, nx))
rho = CArray((nz, ny, nx))


lon, lat = -36.17, 37.18  # LS
lon, lat = -12, 48


tile = gigatl.find_tile_at_point(lon, lat)
subd = gigatl.subdmap[tile]


ds = bd.Dataset()
grid = bd.GDataset()


h = CArray(grid.read(("h", tile)))

dates = ds.dates

zout = CArray((1, ny, nx))
zout[:] = -1000

date = "2008-12-25"
hour = 12


temp = CArray(ds.read(("temp", tile, hour, date)), dtype="d")
salt = CArray(ds.read(("salt", tile, hour, date)), dtype="d")
zeta = CArray(ds.read(("zeta", tile, hour, date)), dtype="d")

croco.zlevs(h, zeta, hc, Cs_r, Cs_w, z_r, z_w)
croco.rho_eos(temp, salt, z_r, z_w, rho0, rho)

fig, ax = plt.subplots()
im = ax.imshow(rho[-1], origin="lower")
ax.set_xlabel("Longitude")
ax.set_ylabel("Latitude")
ax.set_title(f"{date} : {hour:02}:00")
fig.colorbar(im)

isoT = vinterp.vinterp3d(z_r, temp, zout)

fig, ax = plt.subplots()
im = ax.imshow(isoT[0], origin="lower")
ax.set_xlabel("Longitude")
ax.set_ylabel("Latitude")
ax.set_title(f"{date} : {hour:02}:00")
fig.colorbar(im)
