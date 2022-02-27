"""
To illustrate how to use the datase let's generate a movie

SSH in the Gulf Stream for three days (72 frames)

"""
import numpy as np
import schwimmbad
import bindatasets as bd


def get_bounding_indices(tiles):
    ny, nx = 140, 105
    j0 = [ny*(tile//100) for tile in tiles]
    i0 = [nx*(tile % 100) for tile in tiles]
    bb = np.asarray([min(j0), max(j0)+ny, min(i0), max(i0)+nx])
    return bb


def crop(bb, data):
    j0, j1, i0, i1 = bb
    return data[..., j0:j1, i0:i1]


def readalltiles(reader, varname, hour, date, parallel=False):
    ny, nx = 140, 105
    data = np.zeros((ny*100, nx*100))

    ntiles = len(reader.tiles)

    if parallel:
        nworkers = 16
        pool = schwimmbad.MultiPool(processes=nworkers+1)
        tasks = [(varname, tile, hour, date) for tile in reader.tiles]
        chunk = pool.map(reader.read, tasks)
        pool.close()
    else:
        chunk = np.zeros((ntiles, ny, nx))
        for k, tile in enumerate(reader.tiles):
            print(f"\rsubd:{subd:02} tile:{tile}", end="")
            chunk[k] = reader.read(varname, tile, hour, date)

    for k, tile in enumerate(reader.tiles):
        j0, i0 = ny*(tile//100), nx*(tile % 100)
        data[j0:j0+ny, i0:i0+nx] = chunk[k]
    return data


if __name__ == "__main__":
    import matplotlib.pyplot as plt
    from time import time as cputime
    import giga_tools as gt
    import movietools

    plt.ion()

    cmap = "RdBu_r"

    subd = 10
    dirgigabin = "/ccc/store/cont003/gch0401/gch0401/GIGATL1_1h_tides/BIN_1h_JG"

    # this path should be changed, once the binary grid files have been
    # moved to their right place
    dirgrid = "/ccc/scratch/cont003/gen12051/groullet/giga/GRD"

    # the dataset to read the data in the binary format
    reader = bd.RegDataset(dirgigabin, subd)
    grid = bd.GridRegDataset(dirgrid, subd)

    domain = [(-72., 32.5), (-54, 43)]
    axis = [domain[0][0], domain[1][0], domain[0][1], domain[1][1]]
    tiles = gt.find_tiles_inside(gt.LLTP2domain(*domain), gt.corners)
    tiles = [t for t in tiles if t in grid.tiles]

    # we store the (lon,lat) arrays for each tile in a list
    lons = [grid.read("lon_rho", tile) for tile in tiles]
    lats = [grid.read("lat_rho", tile) for tile in tiles]

    vmin = -1.2
    vmax = 1.2

    nworkers = 32

    pool = schwimmbad.MultiPool(processes=nworkers+1)

    def get_ssh(hour, date):
        tasks = iter(("zeta", tile, hour, date) for tile in tiles)
        ssh = pool.map(reader.read, tasks)
        return ssh

    def do_image(hour, date, first):

        ssh = get_ssh(hour, date)
        
        plt.clf()
        for k, tile in enumerate(tiles):
            im = plt.pcolormesh(lons[k], lats[k], ssh[k],
                                cmap=cmap, vmin=vmin, vmax=vmax)
            if first and (k == 0):
                plt.xlabel("Longitude")
                plt.ylabel("Latitude")
                plt.axis(axis)
                plt.colorbar(im)
        plt.title(f"{date} : {hour:02}:00")

    fig = plt.figure()

    iframe = 0
    movie = movietools.Movie(
        fig, name='/ccc/scratch/cont003/gen12051/groullet/giga/ssh_gulfstream')

    for date in reader.dates[:3]:
        for hour in range(24):
            print(f"\rdate:{date}:{hour:02} frame:{iframe:04}", end="")
            
            ssh = get_ssh(hour, date)
            do_image(hour, date, iframe==0)
            
            fig.canvas.draw()
            movie.addframe()
            iframe += 1

    movie.finalize()
    pool.close()
