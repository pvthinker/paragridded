from netCDF4 import Dataset
from dataclasses import dataclass, field
# import os
# import pickle
# import sys
# import shutil
import numpy as np


@dataclass
class VariableInfo():
    nickname: str = ""
    dimensions: tuple = field(default_factory=lambda: ())
    name: str = ""
    units: str = ""
    dtype: str = "f"


class NetCDF_tools():
    """
    Basic class to create and write NetCDF files

    Parameters
    ----------
    filename : str
        The file name to be created.
    attrs : dict
        The global attributes.
    dimensions : list[(name, size), ...]
       The list of dimensions.
       size==None -> unlimited
    variables : list[VariableInfo, ...]
        The name of variable.dimensions should match one of dimensions.

    """

    def __init__(self, filename, attrs, dimensions, variables):
        self.filename = filename
        self.attrs = attrs
        self.dimensions = {dim[0]: dim[1] for dim in dimensions}
        self.variables = {var.nickname: var for var in variables}
        self.iscreated = False

    def create(self):
        """
        Create the empty NetCDF file with

        - attributes
        - dimensions
        - variables
        """
        with Dataset(self.filename, "w", format='NETCDF4') as nc:
            nc.setncatts(self.attrs)

            for dim, size in self.dimensions.items():
                nc.createDimension(dim, size)

            for infos in self.variables.values():
                assert isinstance(infos.dimensions, tuple)
                v = nc.createVariable(infos.nickname,
                                      infos.dtype,
                                      infos.dimensions)
                v.standard_name = infos.name
                v.units = infos.units

        self.iscreated = True

    def write(self, variables, nc_start={}, data_start={}):
        """
        Write variables

        Parameters
        ----------
        variables : list[(nickname, data), ...]
             where data is an ndarray
        nc_start : dict{name: (offset, size)}
             name : the dimension name
             offset : the offset of that dimension in the NetCDF file
             size : the size of data in that dimension

             If a dimension is not in nc_start it is assumed that
             the data has a size that matches the size defined in
             the NetCDF.
        data_start : dict{name: (offset, size)}
             same that nc_start but for the data in variables
        """

        errormsg = f"The NetCDF file needs to be created before writing"
        assert self.iscreated, errormsg

        with Dataset(self.filename, "r+") as nc:
            errormsg = "Problem of dimensions between the data array and what is declared in the NetCDF file"
            for nickname, data in variables.items():

                ncidx = self._get_idx(nickname, nc_start)

                if isinstance(data, np.ndarray):
                    dataidx = self._get_idx(nickname, data_start)
                    assert self._count_elements(
                        ncidx) == self._count_elements(dataidx), errormsg
                    nc.variables[nickname][ncidx] = data[dataidx]

                else:
                    assert self._count_elements(ncidx) == 1, errormsg
                    nc.variables[nickname][ncidx] = data

    def _count_elements(self, slicers):
        """
        Return the number of elements indexed by a list of slices

        """
        count = 1
        for idx in slicers:
            count *= (idx.stop-idx.start)
        return count

    def _get_idx(self, nickname, nc_start):
        """
        Return the tuple of slices

        to either slice through nc.variables or through data
        """
        infos = self.variables[nickname]
        ncidx = []
        for dim in infos.dimensions:
            if dim in nc_start:
                istart, size = nc_start[dim]
            else:
                istart, size = 0, self.dimensions[dim]
            if size is not None:
                ncidx += [slice(istart, istart+size)]
        return tuple(ncidx)

