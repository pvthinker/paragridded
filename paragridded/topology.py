import itertools
import numpy as np

topology = "closed"


def tile2coord(tile, partition):
    i = tile % partition[1]
    j = tile // partition[1]
    return (j, i)


def coord2tile(coords, partition):
    tile = coords[1]+partition[1]*coords[0]
    return tile


def tilesfromblock(block):
    tileblock, partition = block["tileblock"], block["partition"]
    if "int" in str(type(tileblock)):
        tile = tileblock
        tilesarray = np.array(tile, dtype=int)
        tilesarray.shape = [1]*len(partition)

    elif isinstance(tileblock, tuple):
        assert len(tileblock) == len(partition) == 2
        ndims = len(partition)
        idx = [1]*ndims
        ntiles = 1
        for d in range(ndims):
            if isinstance(tileblock[d], int):
                idx[d] = [tileblock[d]]
            else:
                idx[d] = [i for i in tileblock[d]]
            ntiles *= len(idx[d])
        shape = (len(idx[0]), len(idx[1]))
        tilesarray = np.zeros(shape, dtype=int)
        for j in range(shape[0]):
            for i in range(shape[1]):
                coords = (idx[0][j], idx[1][i])
                tilesarray[j, i] = coord2tile(coords, partition)
    else:
        raise TypeError("tileblock should be an int or a tuple")

    return tilesarray


def get_neighbours(tile, partition, level=2):
    alldirec = [(a, b) for a, b in itertools.product(
                [-1, 0, 1], [-1, 0, 1])]

    sumdir = [abs(a)+abs(b) for a, b in alldirec]
    directions = [d for d, s in zip(
        alldirec, sumdir) if (s <= level) and (s > 0)]

    j, i = tile2coord(tile, partition)
    ny, nx = partition
    ngs = {}
    for dj, di in directions:
        ng = 1
        if 'x' in topology:
            pass
        else:
            if ((i+di) < 0) or ((i+di) >= nx):
                ng = None

        if 'y' in topology:
            pass
        else:
            if ((j+dj) < 0) or ((j+dj) >= ny):
                ng = None

        if ng is None:
            # don't even keep track of that direction
            pass
        else:
            coord = [(j+dj) % ny, (i+di) % nx]
            ng = coord2tile(coord, partition)
            ngs[(dj, di)] = ng
    return ngs


def setup_halo(tile, partition, shape, nh, debug=False, **kwargs):
    ndim = len(shape)
    neighbours = get_neighbours(tile, partition, **kwargs)

    iidx = []
    for l in range(2):
        idx = {}
        idx[-1] = slice(-nh, None)
        idx[1] = slice(None, nh)
        idx[0] = slice(0, shape[l])
        iidx += [idx]

    # define outer domain slices
    oidx = []
    # self.oidx has the same structure
    # slice sweeps in the halo domain = places where to fill halo
    # with known x from the neighbour's interior domain
    for l in range(2):
        idx = {}
        idx[-1] = slice(0, nh)
        idx[1] = slice(shape[l]+nh, shape[l]+2*nh)
        idx[0] = slice(nh, shape[l]+nh)
        oidx += [idx]

    halo = []
    for neighb, ntile in neighbours.items():
        dj, di = neighb
        idx_input = (iidx[0][dj], iidx[1][di])
        idx_output = (oidx[0][dj], oidx[1][di])
        halo += [(ntile, idx_input, idx_output)]
        if debug:
            print(f"{ntile} -> {tile} : {idx_input} -> {idx_output}")
    return halo


def get_haloinfos(tile0, partition, shape, halow, direction, **kwargs):
    neighbours = get_neighbours(tile0, partition, **kwargs)
    tile = neighbours[direction]

    nh = halow
    iidx = []
    for l in range(2):
        idx = {}
        idx[-1] = slice(-nh, None)
        idx[1] = slice(None, nh)
        idx[0] = slice(0, shape[l])
        iidx += [idx]

    # define outer domain slices
    oidx = []
    # self.oidx has the same structure
    # slice sweeps in the halo domain = places where to fill halo
    # with known x from the neighbour's interior domain
    for l in range(2):
        idx = {}
        idx[-1] = slice(0, nh)
        idx[1] = slice(shape[l]+nh, shape[l]+2*nh)
        idx[0] = slice(nh, shape[l]+nh)
        oidx += [idx]

    dj, di = direction
    hiidx = (iidx[0][dj], iidx[1][di])
    hoidx = (oidx[0][dj], oidx[1][di])
    return tile, hiidx, hoidx
