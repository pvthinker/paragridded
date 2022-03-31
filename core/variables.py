import gigatl
import halo
#from enum import Enum
import datetime
import numpy as np
from dataclasses import dataclass, field

# class Spacemode(Enum):
#     raw = 0
#     level = 1
#     depth = 2
#     profile = 3
#     point = 4

# class Space:
#     def __init__(self, mode=Spacemode.raw, values=[]):
#         self.mode = mode
#         self._infos = values

#     @property
#     def values(self):
#         """return infos on the space mode when mode is not 'all'"""
#         if isinstance(self._infos, float) or isinstance(self._infos, int):
#             return np.asarray([self._infos])
#         elif isinstance(self._infos, list):
#             return np.asarray(self._infos)
#         else:
#             return self._infos

# def __setitem__(self, key, value):
#     self.mode = key
#     self._infos = value

# def __repr__(self):
#     if self.mode == Spacemode.raw:
#         return self.mode.name
#     else:
#         return f"{self.mode.name}: {self._infos}"


class Space:
    RAW = 0
    LEVEL = 1
    DEPTH = 2
    PROFILE = 3
    POINT = 4
    SECTION = 5

    def __init__(self, mode=0, values=None):
        """ Setup the space mode for accessing within tiled arrays

        Parameters
        ----------
        mode: int, 0: raw,     1: level, 2: depth,
                   3: profile, 4: point, 5:section

        values: float, int, list, the values attached to the mode

        default values are mode=0, values=None
        """
        assert mode in range(6)

        self._mode = mode
        self._values = values

    def reset(self):
        """set mode to raw"""

        self._mode = self.RAW
        self._values = None

    # this function seems useless

    # @property
    # def raw(self):
    #     if self._mode == self.RAW:
    #         return True
    #     else:
    #         return None

    @property
    def depth(self):
        if self._mode == self.DEPTH:
            return self._values
        else:
            return None

    @depth.setter
    def depth(self, values):
        self._mode = self.DEPTH
        self._values = values

    @property
    def level(self):
        if self._mode == self.LEVEL:
            return self._values
        else:
            return None

    @level.setter
    def level(self, value):
        self._values = value
        self._mode = self.LEVEL

    @property
    def is_depth(self):
        return self._mode == self.DEPTH

    @property
    def is_level(self):
        return self._mode == self.LEVEL

    @property
    def is_raw(self):
        return self._mode == self.RAW

    def __str__(self):
        mode = {0: "raw", 1: "level", 2: "depth",
                3: "profile", 4: "point", 5: "section"}[self._mode]
        return f"{mode}: {self._values}"

    def __repr__(self):
        return str(self)


@dataclass
class Staggering:
    horiz: str = "r"
    vert: str = ""


class Domain:
    """ Domain provides the list of tiles

    it can be defined either as a list of tiles
    or as a bounding box in lat-lon"""

    def __init__(self, arg=[7788]):
        assert isinstance(arg, list)
        assert len(arg) > 0
        if isinstance(arg[0], int):
            tiles = arg
            self._tiles = tiles
            self._bbox = gigatl.get_bbox_from_tiles(tiles)
        else:
            bbox = arg
            self._tiles = gigatl.get_tiles_inside(bbox)
            self._bbox = bbox

    def copy(self):
        obj = Domain()
        obj._tiles = self._tiles
        obj._bbox = self.bbox
        return obj

    @property
    def tiles(self):
        return self._tiles

    @property
    def bbox(self):
        return self._bbox

    def __repr__(self):
        return f"{len(self._tiles)} tiles"

    def __eq__(self, other):
        return set(self.tiles) == set(other.tiles)


@dataclass
class Time:
    date: str = "2008-08-01"
    hour: int = 0

    def add(self, days, hours=0):
        t0 = datetime.datetime.fromisoformat(self.date)
        t0 += datetime.timedelta(hours=self.hour)

        t1 = t0+datetime.timedelta(days=days, hours=hours)
        self.date = t1.strftime("%Y-%m-%d")
        self.hour = t1.hour

    def copy(self):
        obj = Time()
        obj.date = self.date
        obj.hour = self.hour
        return obj


@dataclass
class Varinfos():
    varname: str = ""
    domain: Domain = Domain()
    time: Time = Time()
    space: Space = Space()
    staggering: Staggering = Staggering()

    def check(self):
        assert self.is_ok()

    def is_ok(self):
        return (isinstance(self.varname, str) and
                isinstance(self.domain, Domain) and
                isinstance(self.time, Time) and
                isinstance(self.space, Space))

    def __iter__(self):
        return iter(self.domain.tiles)

    def __contains__(self, tile):
        return tile in self.domain.tiles

    def __len__(self):
        return len(self.domain.tiles)


@dataclass
class Variable(Varinfos):
    has_halo = False
    halowidth = 3
    _arrays = {}
    # def __init__(self):
    # arrays is a *list* sorted by tile
    # self._copy(var)
    #self.halowidth = halowidth
    #self.has_halo = False
    #self._arrays = {}

    def update(self, arrays):
        self.has_halo = False
        self._arrays = {tile: array
                        for tile, array in zip(self, arrays)}

    @property
    def ndim(self):
        tile = self._getonetile()
        return self._arrays[tile].ndim

    def _getonetile(self):
        return next(iter(self))

    @property
    def shape(self):
        tile = self._getonetile()
        if len(self._arrays) > 0:
            return (len(self),)+self._arrays[tile].shape
        else:
            return (0,)

    def new(self, varname):
        return Variable(varname, self.domain, self.time, self.space)

    def _copy(self, var):
        self.varname = var.varname
        self.domain = var.domain
        self.time = var.time
        self.space = var.space

    def __getitem__(self, tile):
        return self._arrays[tile]

    def add_halo(self):
        """ add halos to arrays (deallocate previous arrays)"""
        if self.has_halo:
            print(f"variable is already haloed""")
            return

        self.has_halo = True
        # 1) allocate
        arrays = {tile: halo.reallocate(array, self.halowidth)
                  for tile, array in self._arrays.items()}
        # 2) overwrite (and free the unhaloed arrays)
        self._arrays = arrays
        # 3) exchange data across tiles
        halo.exchange(self._arrays, self.halowidth)

    def remove_halo(self):
        """ remove the halo"""
        pass


@dataclass
class Variable_old(Varinfos):

    def __init__(self, var, arrays, halowidth=0):
        # arrays is a *list* sorted by tile
        self._copy(var)
        self.halowidth = halowidth
        self.has_halo = False
        self._arrays = {tile: array
                        for tile, array in zip(var, arrays)}

    @property
    def shape(self):
        tile = next(iter(self))
        return (len(self),)+self._arrays[tile].shape

    def _copy(self, var):
        self.varname = var.varname
        self.domain = var.domain
        self.time = var.time
        self.space = var.space

    def __getitem__(self, tile):
        return self._arrays[tile]

    def add_halo(self):
        """ add halos to arrays (deallocate previous arrays)"""
        if self.has_halo:
            print(f"variable is already haloed""")
            return

        self.has_halo = True
        # 1) allocate
        arrays = {tile: halo.reallocate(array, self.halowidth)
                  for tile, array in self._arrays.items()}
        # 2) overwrite (and free the unhaloed arrays)
        self._arrays = arrays
        # 3) exchange data across tiles
        halo.exchange(self._arrays, self.halowidth)

    def remove_halo(self):
        """ remove the halo"""
        pass


if __name__ == "__main__":
    import numpy as np
    import matplotlib.pyplot as plt
    import halo

    plt.ion()

    christmas = Time("2008-12-25", 12)
    var = Varinfos("zeta", time=christmas)

    surface = Space(Space.LEVEL, -1)
    z1000 = Space(Space.DEPTH, -1000.)
    lucky = Space(Space.PROFILE, [45, 33])
    gridpoint = Space(Space.POINT, [12, 130, 95])

    brittany = Domain([(-12, 41), (4, 52)])

    block = halo.Block((45, 45), (10, 10))

    ssh = Varinfos("zeta", Domain(block.tiles), time=christmas)
    ssh = Varinfos("zeta", brittany, time=christmas)

    shape = (4, 3)
    arrays = [np.zeros(shape, dtype="f")+tile
              for tile in ssh.domain.tiles]
    #fssh = Variable(ssh, arrays, 1)
    # fssh.add_halo()
    #tiles = list(fssh)

    ssh = Variable("temp", brittany, christmas, z1000)
