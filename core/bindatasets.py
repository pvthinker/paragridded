"""
Various dataset classes to handle the binary *.dat files
"""
import bBDF
import glob
import subprocess

PIPE = subprocess.PIPE


def is_fileonline(filename):
    command = f"ccc_hsm status {filename}"
    result = subprocess.run(command.split(), stdout=PIPE, stderr=PIPE,
                            universal_newlines=True, check=True)
    status = result.stdout.split()[-1]
    return status == "online"


class RegDataset():
    """
    Class to read bBDF data for a given region (0 < region < 14)

    the main function provided is read()

    the tiles handled by this object are stored in the .tiles attribute
    the dates handled by this object are stored in the .dates attribute

    """

    def __init__(self, dirbin, subd):
        assert 0 < subd < 14
        self.dirbin = dirbin
        self.subd = subd
        self.dates = self._getdates()
        self.infos = self._get_infos()
        self.dataset = bBDF.Dataset("")
        self.dataset.set_structure(self.infos)
        self.tiles = self.infos["tile"]

    def _get_infos(self):
        header = self._readheaderfile()
        return bBDF.retrieve_infos(header)

    def _readheaderfile(self):
        """
        Read the header bBDF file from the local yaml file

        (instead of reading it from the bBDF file directly)

        """
        headerfile = f"header_his_{self.subd:02}.yaml"
        with open(headerfile, "r") as fid:
            header = "".join(fid.readlines())
        return header

    def filename(self, date):
        assert date in self.dates
        return f"{self.dirbin}/{self.subd:02}/giga_{date}_{self.subd:02}.dat"

    def _getdates(self):
        files = sorted(glob.glob(f"{self.dirbin}/{self.subd:02}/*.dat"))
        return [file.split("_")[-2] for file in files]

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
        assert is_fileonline(datfile)
        self.dataset.filename = datfile
        loc = (self.tiles.index(tile), hour)
        return self.dataset.read_variable(varname, loc)


class GridRegDataset():
    """Class to read grid bBDF data from a given region

    the main function provided is read()

    """

    def __init__(self, dirgrid, subd):
        self.dirgrid = dirgrid
        self.subd = subd
        self.filename = f"{dirgrid}/{subd:02}/grd_gigatl1_{subd:02}.dat"
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
