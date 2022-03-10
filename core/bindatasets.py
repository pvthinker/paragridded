"""
Various dataset classes to handle the binary *.dat files
"""
import bBDF
import gigatl
import parameters
#import glob
import schwimmbad
import subprocess
from functools import lru_cache

PIPE = subprocess.PIPE

param = parameters.Param()

def is_fileonline(filename):
    command = f"ccc_hsm status {filename}"
    result = subprocess.run(command.split(), stdout=PIPE, stderr=PIPE,
                            universal_newlines=True, check=True)
    status = result.stdout.split()[-1]
    return status == "online"

@lru_cache(maxsize=None)
def get_dirstatus(dirname):
    command = f"ccc_hsm ls {dirname}"
    result = subprocess.run(command,
                            stdout=PIPE,
                            stderr=PIPE,
                            universal_newlines=True,
                            check=True,
                            shell=True)
    lines = result.stdout.split("\n")[:-1]
    if len(lines)>0:
        namestatus = [line.split() for line in lines]
        dirstatus = {arg[1]: arg[0]
                     for arg in namestatus}
    else:
        dirstatus = {}
    
    # namestatus is a nested list [ [filename, status] ]
    # filename contains the full path
    # status is either " released " or " online " (with whitespaces)
    
    # dirstatus = {arg[0]: arg[1].strip() == "online"
    #              for arg in namestatus}
    return dirstatus

class Dataset():
    """
    Class to read history files in bBDF format for any tile

    the main function provided is read()

    """
    def __init__(self, bypass_check=False):
        self.subds = list(range(1, 14))
        self.readers = {subd:RegDataset(subd, bypass_check=bypass_check)
                        for subd in self.subds}
        self.subdmap = gigatl.subdmap
        self.has_threads = False
        self.nthreads = 16
        self._setdates()

    def _setdates(self):
        dates = set()
        for reader in self.readers.values():
            dates = dates.union(set(reader.dates))
        self.dates = sorted(list(dates))

    def read(self, args):
        varname, tile, hour, date = args
        subd = self.subdmap[tile]
        return self.readers[subd].read(args)

    def pread(self, args):
        varname, tiles, hour, date = args
        # if not self.has_threads:
        #     self.pool = schwimmbad.MultiPool(processes=self.nthreads+1)
        #     self.has_treads = True
        tasks = iter(
            [(self.readers[self.subdmap[tile]], varname, tile, hour, date)
             for tile in tiles])
        pool = schwimmbad.MultiPool(processes=self.nthreads)
        data = pool.map(read_his, tasks)
        pool.close()
        return data

    def close(self):
        if self.has_threads:
            self.pool.close()
            self.has_threads = False

    def readsurf(self, args):
        varname, tile, hour, date = args
        subd = self.subdmap[tile]
        data = self.readers[subd].read(args)
        if varname in ["u", "v", "temp", "salt", "AKv"]:
            return data[-1]
        else:
            return data

    def is_datetiles_online(self, tiles, date):
        subds = set([self.subdmap[t]
                     for t in tiles])

        status = [self.readers[subd].filestatus[date]
                  for subd in subds]

        return all([s == "online"
                    for s in status])
        
class GDataset():
    """
    Class to read grid files in bBDF format for any tile

    the main function provided is read()

    """
    def __init__(self):
        self.subds = list(range(1, 14))
        self.readers = {subd:GridRegDataset(subd)
                        for subd in self.subds}
        self.subdmap = gigatl.subdmap
        self.has_threads = False
        self.nthreads = 16
        #self.pool = schwimmbad.MultiPool(processes=self.nthreads+1)
        #self.has_treads = True


    def read(self, args):
        varname, tile = args
        subd = self.subdmap[tile]
        return self.readers[subd].read(varname, tile)

    def pread(self, args):
        varname, tiles = args
        # if not self.has_threads:
        #     self.pool = schwimmbad.MultiPool(processes=self.nthreads+1)
        #     self.has_treads = True
        tasks = [(self.readers[self.subdmap[tile]], varname, tile)
                 for tile in tiles]
        pool = schwimmbad.MultiPool(processes=self.nthreads)
        data = pool.map(read_grid, tasks)
        pool.close()
        return data

def read_grid(args):
    reader, varname, tile = args
    return reader.read(varname, tile)

def read_his(args):
    reader, varname, tile, hour, date = args
    return reader.read((varname, tile, hour, date))

class RegDataset():
    """
    Class to read bBDF data for a given region (0 < region < 14)

    the main function provided is read()

    the tiles handled by this object are stored in the .tiles attribute
    the dates handled by this object are stored in the .dates attribute

    """

    def __init__(self, subd, bypass_check=False):
        assert 0 < subd < 14
        self.dirbin = param.dirgigaref
        self.subd = subd
        self.bypass_check = bypass_check
        #self.dates = self._getdates()
        self.infos = self._get_infos()
        #self.filestatus = self._get_filestatus()
        self.set_dates_status()
        self.dataset = bBDF.Dataset("")
        self.dataset.set_structure(self.infos)
        self.tiles = self.infos["tile"]
        self.fastread = {}

    def set_dates_status(self):
        dirname = f"{self.dirbin}/{self.subd:02}"
        dirstatus = get_dirstatus(dirname)
        files = dirstatus.keys()
        self.dates = [file.split("_")[-2] for file in files]
        self.filestatus = {date: status
                           for date, status in zip(self.dates, dirstatus.values())}

    def _get_infos(self):
        header = self._readheaderfile()
        return bBDF.retrieve_infos(header)

    def _readheaderfile(self):
        """
        Read the header bBDF file from the local yaml file

        (instead of reading it from the bBDF file directly)

        """
        headerfile = f"{param.dirmodule}/data/header_his_{self.subd:02}.yaml"
        with open(headerfile, "r") as fid:
            header = "".join(fid.readlines())
        return header

    def filename(self, date):
        assert date in self.dates
        return f"{self.dirbin}/{self.subd:02}/giga_{date}_{self.subd:02}.dat"

    def _getdates(self):
        files = sorted(glob.glob(f"{self.dirbin}/{self.subd:02}/*.dat"))
        return [file.split("_")[-2] for file in files]

    def _get_filestatus(self):
        if self.bypass_check:
            return {date: True for date in self.dates}
        else:
            return {date: is_fileonline(self.filename(date))
                    for date in self.dates}

    def read(self, args):
        """read a variable from a (tile, hour, date)

        Parameters
        ----------        

       args: tuple (varname, tile, hour, date). The tile must belong
       to the region. 

        Returns
        -------

        variable: nd.array, a 3D or 2D array

        """
        varname, tile, hour, date = args
        datfile = self.filename(date)
        assert self.filestatus[date] == "online"
        self.dataset.filename = datfile
        loc = (self.tiles.index(tile), hour)
        return self.dataset.read_variable(varname, loc)

    def open_date(self, date):
        self.dataset.filename = self.filename(date)
        self.fastread[date] = bBDF.FastRead(self.dataset)

    def prefetch(self, args):
        varname, tile, hour, date = args
        loc = (self.tiles.index(tile), hour)
        if date not in self.fastread:
            self.open_date(date)
        self.fastread[date].prefetch(varname, loc)

    def fread(self, args):
        varname, tile, hour, date = args
        loc = (self.tiles.index(tile), hour)
        if date not in self.fastread:
            self.open_date(date)
        return self.fastread[date].read(varname, loc)

    def close_date(self, date):
        if date in self.fastread:
            self.fastread[date].close()
            self.fastread.pop(date)

    def close_all(self):
        dates = list(self.fastread.keys())
        for date in dates:
            self.close_date(date)

class GridRegDataset():
    """Class to read grid bBDF data from a given region

    the main function provided is read()

    """

    def __init__(self, subd):
        self.dirgrid = param.dirgrid
        self.subd = subd
        self.filename = f"{self.dirgrid}/{subd:02}/grd_gigatl1_{subd:02}.dat"
        self.infos = bBDF.read_infos(self.filename)
        self.dataset = bBDF.Dataset(self.filename)
        self.dataset.set_structure(self.infos)
        self.tiles = self.infos["tiles"]

    def read(self, varname, tile):
        """
        Read a variable from the grid

        Parameters
        ----------

        varname: str the name of the variable
        tile: int the tile

        Returns
        -------
        variable: nd.array, the data
        """
        assert tile in self.tiles
        index = self.tiles.index(tile)
        loc = (index // 100, index % 100)
        return self.dataset.read_variable(varname, loc)
