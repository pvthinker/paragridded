from shapely.geometry.polygon import Polygon

def find_tiles_inside(param, domain, oceanonly=True):
    """Determine which tiles are inside `domain`

    The function uses `corners` the list of corners for each tile
    """
    p = Polygon(domain)
    tileslist = []
    for tile, c in param.corners.items():
        if (not oceanonly) or (not param.missing[tile]):
            q = Polygon(c)
            if p.overlaps(q) or p.contains(q):
                tileslist += [tile]
    return tileslist

def LLTR2domain(lowerleft, topright):
    """Convert the two pairs of (lower, left), (top, right) in (lat, lon)
    into the four pairs of (lat, lon) of the corners """
    xa, ya = lowerleft
    xb, yb = topright
    domain = [(xa, ya), (xa, yb), (xb, yb), (xb, ya)]
    return domain
