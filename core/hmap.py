import gigatl
from variables import Variable, Domain
import halo

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt

videosize = {480: 640,
             720: 1080,
             1080: 1920}


class Pcolormesh:
    def __init__(self, giga, height=480):
        self.giga = giga

        assert height in [480, 720, 1080]

        width = videosize[height]
        figsize = (width, height)
        self.figsize = figsize
        self.dpi = 100

        if height == 1080:
            mpl.rcParams["font.size"] = 16
        elif height == 720:
            mpl.rcParams["font.size"] = 13

        figsize = (width/self.dpi, height/self.dpi)
        self.fig, self.ax = plt.subplots(figsize=figsize, dpi=self.dpi)

        self.colorbar = ()
        self.domain = Domain()
        self.im = {}

    def imshow(self, field, colorbar):
        tiles = list(field)
        ntiles = len(tiles)
        c = np.zeros((ntiles, 2), dtype="b")
        for k in range(ntiles):
            c[k] = halo.tilec(tiles[k])

            j0, j1 = c[:, 0].min(), c[:, 0].max()+1
            i0, i1 = c[:, 1].min(), c[:, 1].max()+1

        nt, nz, ny, nx = field.shape
        nh = field.halowidth
        nyglo = (ny-2*nh)*(j1-j0) + 2*nh
        nxglo = (nx-2*nh)*(i1-i0) + 2*nh
        gloshape = (nyglo, nxglo)
        print(gloshape)
        print(j0, j1, i0, i1)
        self.globarray = np.zeros(gloshape, dtype="f")

        for tile in field:
            jt, it = tile//100, tile % 100
            jj = (jt-j0)*(ny-2*nh)
            ii = (it-i0)*(nx-2*nh)
            jdx = slice(jj, jj+ny)
            idx = slice(ii, ii+nx)
            print(jdx, idx)
            print(field[tile].shape)
            self.globarray[jj:jj+ny, ii:ii+nx] = field[tile][-1]
        self.ax.imshow(self.globarray)

    def draw(self, field, colorbar, redraw=False):
        errmsg = f"pcolormesh requires {field.varname} to be a two-dimensional array"
        assert field.ndim == 2, errmsg

        domain = field.domain
        axis = gigatl.domaintoaxis(domain.bbox)

        ax = self.ax
        vmin, vmax, cmap = colorbar
        if (field.domain == self.domain) and (not redraw):
            for tile in field:
                # shading flat reduces the shape
                # cf https://github.com/matplotlib/matplotlib/issues/15388
                f = field[tile][1:, 1:].ravel()
                self.im[tile].set_array(f)

        else:
            lon = Variable("lon_psi", domain)
            self.giga.read(lon)
            lat = Variable("lat_psi", domain)
            self.giga.read(lat)

            ax.cla()
            self.im = {tile: ax.pcolormesh(lon[tile], lat[tile], field[tile],
                                           vmin=vmin, vmax=vmax, cmap=cmap,
                                           shading="flat")
                       for tile in field}

            ax.set_xlabel("Longitude")
            ax.set_ylabel("Latitude")
            ax.axis(axis)

            self.domain = field.domain

        date = field.time.date
        hour = field.time.hour
        title = f"{date}:{hour:02}"
        ax.set_title(title)

        if (self.colorbar != colorbar) or redraw:
            if hasattr(self, "cb"):
                self.cb.remove()
            tile = field._getonetile()
            self.cb = self.fig.colorbar(self.im[tile])
            self.colorbar = colorbar

        plt.tight_layout()


def get_vminmax(var):
    medians = [np.median(var[tile]) for tile in var]
    medians = [med for med in medians if med != np.inf]
    stds = [np.std(var[tile]) for tile in var]
    stds = [std for std in stds if not np.isnan(std)]
    median = np.median(medians)
    std = np.quantile(stds, 0.75)
    return (median-3*std, median+3*std)
