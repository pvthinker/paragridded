import numpy as np


def exchange(arrays, nh):
    tiles = list(arrays)
    ntiles = len(tiles)
    c = np.zeros((ntiles, 2), dtype="b")
    for k in range(ntiles):
        c[k] = tilec(tiles[k])

    j0, j1 = c[:, 0].min(), c[:, 0].max()
    i0, i1 = c[:, 1].min(), c[:, 1].max()

    data = arrays

    for j in range(j0+1, j1+1):
        for i in range(i0+1, i1+1):
            tile0 = ctile(j-1, i)
            tile1 = ctile(j, i-1)
            if (tile0 in tiles) and (tile1 in tiles):
                exchange_halo(data[tile0],
                              data[tile1],
                              nh, "rightbottom")

            tile0 = ctile(j-1, i-1)
            tile1 = ctile(j, i)
            if (tile0 in tiles) and (tile1 in tiles):
                exchange_halo(data[tile0],
                              data[tile1],
                              nh, "leftbottom")

    for j in range(j0+1, j1+1):
        for i in range(i0, i1+1):

            tile0 = ctile(j-1, i)
            tile1 = ctile(j, i)
            if (tile0 in tiles) and (tile1 in tiles):
                exchange_halo(data[tile0],
                              data[tile1],
                              nh, "bottom")

    for j in range(j0, j1+1):
        for i in range(i0+1, i1+1):

            tile0 = ctile(j, i-1)
            tile1 = ctile(j, i)
            if (tile0 in tiles) and (tile1 in tiles):
                exchange_halo(data[tile0],
                              data[tile1],
                              nh, "left")


def exchange_halo(B, A, nh, what):
    Aouter = slice(-nh, None)
    Ainner = slice(-nh-nh, -nh)
    Bouter = slice(nh)
    Binner = slice(nh, nh+nh)
    inner = slice(nh, -nh)

    if what == "left":
        A[inner, Aouter] = B[inner, Binner]
        B[inner, Bouter] = A[inner, Ainner]

    elif what == "bottom":
        A[Aouter, inner] = B[Binner, inner]
        B[Bouter, inner] = A[Ainner, inner]

    elif what == "leftbottom":
        A[Aouter, Aouter] = B[Binner, Binner]
        B[Bouter, Bouter] = A[Ainner, Ainner]

    elif what == "rightbottom":
        A[Aouter, Bouter] = B[Binner, Ainner]
        B[Bouter, Aouter] = A[Ainner, Binner]

    else:
        raise ValueError


def reallocate(Ashort, nh):
    if Ashort.ndim == 2:
        ny, nx = Ashort.shape
        shape = (ny+2*nh, nx+2*nh)
    elif Ashort.ndim == 3:
        nz, ny, nx = Ashort.shape
        shape = (nz, ny+2*nh, nx+2*nh)

    A = np.zeros(shape, dtype=Ashort.dtype)+np.nan
    inner = slice(nh, -nh)
    A[..., inner, inner] = Ashort
    return A


def ctile(j, i):
    return j*100+i


def tilec(tile):
    return (tile//100, tile % 100)


class Block:
    def __init__(self, corner, shape):
        self.corner = corner
        self.shape = shape
        self._set_tiles()

    def _set_tiles(self):
        j0, i0 = self.corner
        npy, npx = self.shape
        self.tiles = [ctile(j, i)
                      for j in range(j0, j0+npy)
                      for i in range(i0, i0+npx)]

    def add_halo(self, fields, nh):
        j0, i0 = self.corner
        npy, npx = self.shape
        data = {tile: reallocate(field, nh)
                for tile, field in fields.items()}

        for j in range(j0+1, j0+npy):
            for i in range(i0+1, i0+npx):

                exchange_halo(data[ctile(j-1, i)],
                              data[ctile(j, i-1)],
                              nh, "rightbottom")

                exchange_halo(data[ctile(j-1, i-1)],
                              data[ctile(j, i)],
                              nh, "leftbottom")

        for j in range(j0+1, j0+npy):
            for i in range(i0, i0+npx):

                exchange_halo(data[ctile(j-1, i)],
                              data[ctile(j, i)],
                              nh, "bottom")

        for j in range(j0, j0+npy):
            for i in range(i0+1, i0+npx):

                exchange_halo(data[ctile(j, i-1)],
                              data[ctile(j, i)],
                              nh, "left")

        return data

    def aggregate(self, fields):
        j0, i0 = self.corner
        npy, npx = self.shape
        A = fields[self.tiles[0]]
        if A.ndim == 2:
            ny, nx = A.shape
            shape = (npy*ny, npx*nx)
        elif A.ndim == 3:
            nz, ny, nx = A.shape
            shape = (nz, npy*ny, npx*nx)
        Aglobal = np.zeros(shape, dtype=A.dtype)
        for j in range(npy):
            for i in range(npx):
                jdx = slice(j*ny, j*ny+ny)
                idx = slice(i*nx, i*nx+nx)
                A = fields[ctile(j+j0, i+i0)]
                Aglobal[..., jdx, idx] = A
        return Aglobal


def test():
    nh = 2
    ny, nx = (5, 3)
    dtype = "f"
    shape = (ny+2*nh, nx+2*nh)
    A = np.ones(shape, dtype=dtype)
    B = np.ones(shape, dtype=dtype)*2
    C = np.ones(shape, dtype=dtype)*3
    exchange_halo(A, B, nh, "left")
    #exchange_halo(A, B, "bottom")
    exchange_halo(A, C, nh, "leftbottom")

    print(f"A=\n{A}")
    print(f"B=\n{B}")
    print(f"C=\n{C}")

    block = Block((45, 45), (10, 10))

    ny, nx = 145, 105
    rawdata = {tile: np.zeros((ny, nx), dtype=dtype)+k
               for k, tile in enumerate(block.tiles)}

    halodata = block.add_halo(rawdata, 5)
    globaldata = block.aggregate(rawdata)
    gdata = block.aggregate(halodata)

    plt.clf()
    #plt.imshow(halodata[ctile(47, 47)], origin="lower")
    plt.imshow(gdata, origin="lower")


if __name__ == "__main__":
    import matplotlib.pyplot as plt
    plt.ion()
