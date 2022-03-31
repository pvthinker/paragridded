import gigatl
import bindatasets as bd
import reading
import vinterp
import curl
#import heatflux


class Giga:
    def __init__(self):
        self.reader = reading.Gigatl()
        self.vinterp = vinterp.Vinterp(self.reader)
        self.curl = curl.Curl(self.reader, self.vinterp)
        #self.heatflux = HeatFlux(self.reader, self.vinterp)

    def update(self, var):
        if var.varname == "vorticity":
            self.curl.compute(var)
        # elif var.varname == "heatflux":
        #     self.heatflux.compute(temp, 98)
        else:
            self.reader.read(var)
            if var.space.is_depth:
                self.vinterp.compute(var)
            elif var.space.is_level:
                level = var.space.level
                assert isinstance(level, int)
                var._arrays = {tile: array[level].copy()
                               for tile, array in var._arrays.items()}

    def print_status(self):
        self.reader.hist.print_status()

    def is_online(self, var, tile=None):
        if tile is None:
            tiles = var.domain.tiles
            date = var.time.date
            return self.reader.hist.is_datetiles_online(tiles, date)
        else:
            assert isinstance(tile, int)
            date = var.time.date
            subd = gigatl.subdmap[tile]
            r = self.reader.hist.readers[subd]
            filename = r.filename(date)
            return bd.is_fileonline(filename)

    def restart_pool(self):
        self.reader.restart_pool()
