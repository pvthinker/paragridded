"""
Define a domain encompassing many tiles (382), over two regions

Read the temperature at a given (date, hour) using "pread" the multi-threaded reader

Plot the SST
"""
import matplotlib as mpl
import gigatl
import numpy as np

from matplotlib import pyplot as plt
import bindatasets as bd

plt.ion()

print("open HIST")
ds = bd.Dataset()

print("open GRID")
grid = bd.GDataset()

#domain = [(-40, 46), (0, 60)]
domain = [(-40, 50), (0, 65)]
tiles = gigatl.get_tiles_inside(domain)
subds = gigatl.get_subds_from_tiles(tiles)


print(f"read GRID #tiles: {len(tiles)} in {subds}")
lons=grid.pread(("lon_rho", tiles))
lats=grid.pread(("lat_rho", tiles))
axis = gigatl.domaintoaxis(domain)



vmin = 2.
vmax = 14.
varname = "temp"
date="2008-12-31"
hour = 23


print(f"read HIST {date} #tiles: {len(tiles)} in {subds}")
assert ds.is_datetiles_online(tiles, date)
data = ds.pread((varname, tiles, hour, date))


print("plot")
figsize = (640, 480)
figsize = (1280, 720)
#figsize = (1920, 1080)
dpi = 100
width, height = figsize

if height == 1080:
    mpl.rcParams["font.size"] = 16
elif height == 720:
    mpl.rcParams["font.size"] = 13

axposition = [0.06, 0.08,
              0.80, 0.88]
cbposition = [0.87, 0.08,
              0.10, 0.88]

cmap = "cividis"

fig,ax=plt.subplots(figsize=(width/dpi, height/dpi), dpi=dpi)
for lon, lat, temp in zip(lons, lats, data): 
    im = ax.pcolormesh(lon, lat, temp[-1], vmin=vmin, vmax=vmax, cmap=cmap)
ax.set_xlabel("Longitude")
ax.set_ylabel("Latitude")
ax.axis(axis)
ax.set_title(f"{date} : {hour:02}:00")
cb = fig.colorbar(im)
ax.set_position(axposition)
cb.ax.set_position(cbposition)
ax.grid()

