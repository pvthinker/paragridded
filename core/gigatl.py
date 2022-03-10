import numpy as np
import os
from shapely.geometry.polygon import Polygon, Point
import pickle
import matplotlib.pyplot as plt
from matplotlib import colors
from matplotlib import cm


def get_corners_from_domain(domain):
    """Returns the 4 corners (x,y) of a domain

    where domain is (lowerleft, topright)

    and lowerleft and topright are (x,y)
    """
    lowerleft, topright = domain
    xa, ya = lowerleft
    xb, yb = topright
    return [(xa, ya), (xa, yb), (xb, yb), (xb, ya)]


def get_tiles_inside(domain):
    """ Returns the list of tiles having grid points in domain """
    domain_corners = get_corners_from_domain(domain)
    p = Polygon(domain_corners)
    return [tile
            for tile, q in polygon_tiles.items()
            if p.intersects(q)]


def get_subds_from_tiles(tiles):
    return set([subdmap[t] for t in tiles])


def draw_tiles(ax, tiles, domain=None, fill=False, **kwargs):
    """ Draw the list of tiles n in ax

    polygons can be filled or not
    the enclosed domain can be superimposed

    """
    if "color" in kwargs:
        color = kwargs.pop("color")
        is_colorimposed = True
    else:
        vmin = 0
        vmax = 12
        normalize = colors.Normalize(vmin=vmin, vmax=vmax)
        cmap = cm.Set3
        is_colorimposed = False

    for tile in tiles:
        p = polygon_tiles[tile]
        if fill:
            if not is_colorimposed:
                color = cmap(normalize(tile % 12))
            ax.fill(*p.exterior.xy,
                    color=color,
                    **kwargs)
        else:
            ax.plot(*p.exterior.xy, **kwargs)

    if domain is not None:
        domain_corners = get_corners_from_domain(domain)
        p = Polygon(domain_corners)
        ax.plot(*p.exterior.xy,
                lw=2,
                color="k")


def draw_gigatl_regions():
    fig, ax = plt.subplots()
    vmin = 1
    vmax = 20
    normalize = colors.Normalize(vmin=vmin, vmax=vmax)
    cmap = cm.tab20
    for subd in range(1, 14):
        tiles = [tile
                 for tile, s in subdmap.items()
                 if (tile in polygon_tiles) and (s == subd)]
        color = cmap(normalize(subd))
        draw_tiles(ax, tiles, fill=True, color=color)


def domaintocoords(domain):
    lowerleft, topright = domain
    xa, ya = lowerleft
    xb, yb = topright
    return np.asarray([xa, ya, xb, yb])


def coordstodomain(coords):
    xa, ya, xb, yb = coords
    return [(xa, ya), (xb, yb)]


def domaintoaxis(domain):
    lowerleft, topright = domain
    xa, ya = lowerleft
    xb, yb = topright
    return (xa, xb, ya, yb)


def traveling(domain0, domain1, nt):
    """Generator for a traveling sequence

    yield nt (tiles, domain) between domain0 and domain1.

    Note: this function can be used for a traveling sequence or a
    zoom/unzoom sequence or a conjunction of the two.

    """
    c0 = domaintocoords(domain0)
    c1 = domaintocoords(domain1)
    for t in np.linspace(0, 1, nt):
        c = c1*t+(1-t)*c0
        domain = coordstodomain(c)
        tiles = get_tiles_inside(domain)
        yield tiles, domain


def find_tile_at_point(lon, lat):
    """Retrieve the tile where the point (lon, lat) sits. """
    # this function is 20 times faster than by testing with the
    # Polygon.contains() method
    loc = np.asarray((lon, lat))
    dist = np.sum((centers-loc)**2, 1)
    return np.argmin(dist)


def find_tile_at_point_slow(lon, lat):
    """Retrieve the tile where the point (lon, lat) sits.

    WARNING: this is an approximative algo. The tiles boundaries are
    curved.  A point inside a tile ain't necessarily inside the
    quadrilateral formed with the four corners...

    """
    point = Point(lon, lat)
    tile0 = -1
    for tile, p in polygon_tiles.items():
        if p.contains(point):
            tile0 = tile
            break
    return tile0


def test_traveling():
    domain0 = [(-18, 41), (2, 52)]
    domain1 = [(-72, 28), (-54, 40)]

    nt = 30
    fig, ax = plt.subplots()
    for tiles, domain in traveling(domain0, domain1, nt):
        ax.cla()
        draw_tiles(ax, tiles, fill=True, domain=domain)
        ax.axis(domaintoaxis(domain))
        ntiles = len(tiles)
        t = set(tiles)
        subds = [s
                 for s in range(1, 14)
                 if len(regions[s].intersection(t)) > 0]
        ax.set_title(f"#tiles: {ntiles} / regions: {subds}")

        fig.canvas.draw()
        plt.pause(1e-6)


def test_basic():
    domain = [(-18, 41), (2, 52)]

    tiles = get_tiles_inside(domain)
    print(f"#tiles in domain {domain}: {len(tiles)}")

    fig, ax = plt.subplots()
    draw_tiles(ax, tiles, fill=True, domain=domain)


def corners2center(corner):
    c = np.asarray(corner)
    return c.mean(axis=0)


# print(__file__)
# path to where giga_tools.py sits
dirmodule = __file__  # os.path.dirname(pretty.__file__)
sep = os.path.sep
# path to pickle GIGATL data files
dirdata = sep.join(dirmodule.split(sep)[:-2] + ["data"])

print(f"dirmodule: {dirmodule}")
print(f"dirdata: {dirdata}")

# corners and submap are stored in pickle files
with open(f"{dirdata}/giga_corners.pkl", "rb") as f:
    corners = pickle.load(f)
msg = "something is wrong with data/giga_corners.pkl"
assert len(corners) == 6582, msg

with open(f"{dirdata}/giga_subdmap.pkl", "rb") as f:
    subdmap = pickle.load(f)
msg = "something is wrong with data/giga_subdmap.pkl"
assert len(subdmap) == 6582, msg

polygon_tiles = {tile: Polygon(c)
                 for tile, c in corners.items()}

regions = {subd: set([tile
                      for tile, s in subdmap.items()
                      if s == subd])
           for subd in range(1, 14)}

centers = np.zeros((10_000, 2))+999.
for tile, c in corners.items():
    centers[tile, :] = corners2center(c)

if __name__ == "__main__":
    plt.ion()

    # draw_gigatl_regions()
