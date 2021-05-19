""""
tools to handle Gigatl subdomains
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colorbar as cb
import matplotlib.cm as cm
import pickle
from shapely.geometry.polygon import Polygon
from shapely.geometry.point import Point
import shapely.ops as so
#from descartes import PolygonPatch
import giga_tools as giga
import croco
import topology as topo


def get_corner(tile):
    # for tile in list(subdmap.keys()):
    #     print(f"tile: {tile}")
    block = {"partition": giga.partition, "tileblock": tile}
    grid = croco.load_grid(giga.grdfiles, block,
                           giga.dimpart, giga.nsigma, halow=0)
    xf = grid.xi(stagg=croco.fpoint)
    yf = grid.eta(stagg=croco.fpoint)
    idxcorners = [(0, 0), (-1, 0), (-1, -1), (0, -1)]
    print(tile, flush=True)
    return [(xf[i], yf[i]) for i in idxcorners]


alltiles = range(100*100)
missing = [False if tile in giga.subdmap else True for tile in alltiles]


def get_allcorners():
    import schwimmbad

    pool = schwimmbad.MultiPool()
    res = pool.map(get_corner, alltiles)
    pool.close()
    corners = {}
    for tile in alltiles:
        corners[tile] = res[tile]
    return corners


def get_subds_from_block(block):
    tileblock = block["tileblock"]
    tiles = topo.tilesfromblock(block)
    if "int" in str(type(tileblock)):
        i, j = topo.tile2coord(tileblock, block["partition"])
        i0 = i1 = i
        j0 = j1 = j
    else:
        irange, jrange = tileblock[0], tileblock[1]
        i0, i1 = irange.start, irange.stop
        j0, j1 = jrange.start, jrange.stop

    i0 = max(0, i0-1)
    i1 = min(100, i1+1)
    j0 = max(0, j0-1)
    j1 = min(100, j1+1)

    tileblock = (range(i0, i1), range(j0, j1))
    eblock = {"partition": block["partition"],
              "tileblock": tileblock}
    tiles = topo.tilesfromblock(eblock)
    subds = list(set([giga.subdmap[tile]
                      for tile in tiles.flat if tile in giga.subdmap]))
    return subds


def get_blocks_subds_from_tiles(tileslist, blocksize):
    block = {"partition": giga.partition}
    tl = set(tileslist)
    blocks = []
    subds = set([])

    for j in range(0, 100, blocksize):
        for i in range(0, 100, blocksize):
            block["tileblock"] = (range(j, min(j+blocksize, 100)),
                                  range(i, min(i+blocksize, 100)))
            tiles = topo.tilesfromblock(block)
            intersection = tl.intersection(set(tiles.flat))
            if len(intersection) == 0:
                pass
            else:
                subds = subds.union(get_subds_from_block(block))
                blocks += [block.copy()]

    print(f"number of tiles  : {len(tileslist)}")
    print(f"number of blocks : {len(blocks)}")
    print(f"subdomains       : {subds}")

    return (subds, blocks)


def plot_blocks(domain, tileslist, blocks, filename=None):
    """ produce the control plot showing tiles and blocks"""
    plt.figure()
    ax = plt.axes()
    plot_subdomains(tileslist, fill=True, fc="#555555")
    tl = set(tileslist)
    n = 0
    for block in blocks:
        tiles = topo.tilesfromblock(block)
        intersection = tl.intersection(set(tiles.flat))
        if len(intersection) == 0:
            pass
        else:
            color = cm.tab20(n % 20)
            n += 1
            plot_subdomains(tiles, fill=True, color=color, alpha=0.5)
    reso = 2
    lltr = (domain[0], domain[2])
    plt.axis([lltr[0][0]-reso, lltr[1][0]+reso,
              lltr[0][1]-reso, lltr[1][1]+reso])
    plt.grid(True)
    if not (filename is None):
        plt.savefig(filename)


def plot_block(block, **kwargs):
    tiles = topo.tilesfromblock(block)
    plot_subdomains(tiles, number=True, **kwargs)


def plot_subdomains(tiles, fill=False, number=False, **kwargs):
    for tile in np.asarray(tiles).flat:
        if tile in giga.corners:
            p = Polygon(giga.corners[tile])
            if fill:
                plt.fill(*p.exterior.xy, **kwargs)
            else:
                plt.plot(*p.exterior.xy, **kwargs)
            if number:
                x, y = p.centroid.coords.xy
                plt.text(x[-1], y[-1], f"{tile}",
                         ha="center", va="center", fontsize=10)


def LLTR2domain(lowerleft, topright):
    """Convert the two pairs of (lower, left), (top, right) in (lat, lon)
    into the four pairs of (lat, lon) of the corners """
    xa, ya = lowerleft
    xb, yb = topright
    domain = [(xa, ya), (xa, yb), (xb, yb), (xb, ya)]
    return domain


def find_tiles_inside(domain, oceanonly=True):
    """Determine which tiles are inside `domain`

    The function uses `corners` the list of corners for each tile
    """
    p = Polygon(domain)
    tileslist = []
    for tile, c in giga.corners.items():
        if (not oceanonly) or (not giga.missing[tile]):
            q = Polygon(c)
            if p.overlaps(q) or p.contains(q):
                tileslist += [tile]
    return tileslist


def generate_tile_poly():
    for tile, corner in giga.corners.items():
        yield (tile, Polygon(corner))


def find_coord_in_tile(tile, lon, lat, grid=None):
    if grid is None:
        block = {"partition": giga.partition, "tileblock": tile}
        grid = croco.load_grid(giga.grdfiles, block,
                               giga.dimpart, giga.nsigma, halow=0)
    hw = grid.halow
    lonc, latc = grid.xi(), grid.eta()
    dist = (lon-lonc)**2 + (lat-latc)**2
    j, i = np.unravel_index(np.argmin(dist, axis=None), dist.shape)
    return (j-hw, i-hw)


def find_tile_at_point(lon, lat):
    """retrieve the (tile, subd) where the point (lon, lat) sits

    approximative algo: the tiles boundaries are curved.
    A point inside a tile ain't necessarily inside the quadrilateral
    formed with the four corners...

    needs a second pass to decide whether it is the good tile or its
    neighbour

    """
    point = Point(lon, lat)
    res = [tile for tile, poly in generate_tile_poly()
           if poly.contains(point)]

    if len(res) == 0:
        return -1, 0
    elif len(res) == 1:
        tile = res[0]
        if tile in giga.subdmap:
            subd = giga.subdmap[tile]
        else:
            subd = -1
        return tile, subd
    else:
        raise ValueError(f"problem: I found {len(res)} tiles")


def extract_blocks_inside(domain, blocksize=1):
    pass


def plot_gigatl():
    """ plot gigatl subdomains (13 of them) """
    fig = plt.figure(figsize=(12, 9))
    clrs = ['#6F4C9B', '#6059A9', '#5568B8', '#4E79C5', '#4D8AC6',
            '#4E96BC', '#549EB3', '#59A5A9', '#60AB9E', '#69B190',
            '#77B77D', '#8CBC68', '#A6BE54', '#BEBC48', '#D1B541',
            '#DDAA3C', '#E49C39', '#E78C35', '#E67932', '#E4632D',
            '#DF4828', '#DA2222']
    for tile in alltiles:
        if tile in giga.subdmap:
            subd = giga.subdmap[tile]
        else:
            subd = 0
        j, i = topo.tile2coord(tile, giga.partition)
        if (i % 10) == 0 or (j % 10) == 0:
            lw = 2
        else:
            lw = 1
        color = clrs[(subd*22)//14]
        plot_subdomains(tile, color=color, lw=lw)

    plt.grid(True)
    plt.savefig("giga_subdomains.png")
    plt.savefig("giga_subdomains.pdf")
