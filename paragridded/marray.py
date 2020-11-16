"""Marray is a subclass of np.ndarray suited to handle gridded
variables on staggered grids

Marray provides

  - attrs: dict contains the metadata such as name, units etc
  - dims: tuple, the named dimensions, e.g. ("t", "y", "x")
  - stagg: dict, the staggering, e.g. {"t": False, "y": False, "x": True}

"""


import numpy as np
from pretty import BB, MA

debug = False


class Marray(np.ndarray):

    def __new__(cls, input_array, dims=None, attrs=None, stagg=None):
        """
        Parameters
        ----------
        
        - array: ndarray the data
        - attrs: dict contains the metadata such as name, units etc
        - dims: tuple, the named dimensions, e.g. ("t", "y", "x")
        - stagg: dict, the staggering, e.g. {"t": False, "y": False, "x": True}

        Returns
        -------
        - marray: same data with metainformations and named dimensions
        """
        # Input array is an already formed ndarray instance
        # We first cast to be our class type
        obj = np.asarray(input_array).view(cls)

        if attrs is None:
            if hasattr(input_array, "attrs"):
                attrs = getattr(input_array, "attrs")
            else:
                attrs = {}
        obj.attrs = attrs

        if dims is None:
            assert hasattr(input_array, "dims")
            dims = input_array.dims
        if isinstance(dims, str):
            dims = [dims]
        obj.dims = dims
        assert len(dims) == len(input_array.shape)

        staggering = {d: False for d in dims}
        if stagg is not None:
            for d in dims:
                if d in stagg:
                    staggering[d] = stagg[d]
        obj.stagg = staggering

        sizes = {}
        for k, d in enumerate(dims):
            sizes[d] = input_array.shape[k]
        obj.sizes = sizes

        # for xarray compatibility
        obj._data = obj.data
        # Finally, we must return the newly created object:
        return obj

    def slice(self, elem):
        """ Return a slice on axis == 0

        Put the slice index as a new attribute
        """
        assert isinstance(elem, int)
        data = np.asarray(self)
        data = data[elem]
        dims = self.dims[1:]
        attrs = self.attrs.copy()
        attrs[self.dims[0]] = elem
        return Marray(data, attrs=attrs, stagg=self.stagg.copy(), dims=dims)

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        string = []
        if hasattr(self, "dims"):
            # {d: self.shape[k] for k, d in enumerate(self.dims)}
            shape = [(d, self.sizes[d]) for d in self.dims]
            dims_str = [f"{dim}: {length}" for dim, length in shape]
            string += [MA("<M-array ("+", ".join(dims_str)+")>")]
        else:
            ndim = self.ndim
            string += [MA(f"<M-array ({ndim}-dimensional with unnamed dimensions)>")]

        string += [BB("* Data:")]
        #        string += [np.core.arrayprint.array2string(self)]
        string += [np.asarray(self).__repr__()]

        if hasattr(self, "attrs") and len(self.attrs.keys()) > 0:
            string += [BB("* Attributes:")]
            maxlen = max([len(k) for k in self.attrs.keys()])
            maxlen += 1
            for k, v in self.attrs.items():
                string += [f"  - {k:{maxlen}s}: {v}"]
        else:
            string += [BB("* Attributes:")+" None"]

        if hasattr(self, "stagg"):
            stagg_str = [f"{dim}: {val}" for dim, val in self.stagg.items()]
            stagg_str = "("+", ".join(stagg_str)+")"
        else:
            stagg_str = "None"
        string += [BB("* Staggering: ")+stagg_str]

        return "\n".join(string)

    def sumd(self, axis=None):
        if axis is None:
            return np.sum(self.data)
        else:
            assert all([a in self.dims if type(
                a) is str else False for a in axis])
            axis_int = []
            newdims = []
            for k, d in enumerate(self.dims):
                if d in axis:
                    axis_int += [k]
                else:
                    newdims += [d]
            attrs = self.attrs
            if "history" in attrs.keys():
                history = attrs["history"]
            else:
                history = attrs["name"]
            history += " -> sum over (" + ", ".join([a for a in axis])+")"
            attrs["history"] = history
            return Marray(np.sum(self.data, axis=tuple(axis_int)), dims=newdims, attrs=attrs)


def zeros(sizes, dims=None, attrs=None, stagg=None):
    """ Returns a zero m-array with prescribed sizes
    """
    dims = tuple([d for d in sizes.keys()])
    shape = tuple([sizes[d] for d in dims])
    return Marray(np.zeros(shape), dims=dims, attrs=attrs, stagg=stagg)


def copymeta(marray_in, marray_out):
    """ Copy metadata from input to output marray
    """
    for key in ["dims", "attrs", "stagg", "sizes"]:
        if not(hasattr(marray_out, key)):
            #print('copy', key, getattr(marray_in, key))
            setattr(marray_out, key, getattr(marray_in, key))


def flat2d(marray, dim):
    """ Flatten and squeeze marray into a two-axes array

    with dim on axis=0 and the others axes squeezed into a single axis

    if marray is one dimensional, do nothing

    Parameters
    ----------
    marray: m-array with ndim dimensions
    dim: name of the dimension to put on axis=0

    Returns
    -------
    permaxes: the permutation to get back marray shape from the unsqueezed tmp
    tmp_shape: shape of the transposed array, before squeezing
    tmp: marray[dim, otheraxes]

    """
    assert dim in marray.dims
    idx = marray.dims.index(dim)
    if marray.ndim == 1:
        return [0], marray.shape, marray
    else:
        shape = list(marray.shape)

        tmp_shape = rotatelist(shape, +idx)
        tmp = np.zeros(tmp_shape)

        n0 = shape[idx]
        n1 = np.prod(shape) // n0
        axes = list(range(marray.ndim))
        tmp[:] = np.transpose(marray, rotatelist(axes, +idx))
        if debug:
            print(marray.shape)
        tmp_shape = tmp.shape
        tmp.shape = (n0, n1)
        permaxes = rotatelist(axes, -idx)
        return permaxes, tmp_shape, tmp


def unflat2d(permaxes, tmp_shape, tmp):
    """ Reciprocal of flat2d

    Returns
    -------
    a view of the reorded array
    """
    tmp.shape = tmp_shape
    if len(tmp_shape) > 1:
        return np.transpose(tmp, permaxes).flat
    else:
        return tmp.flat


def rotatelist(mylist, n):
    """Rotate list elements """
    return mylist[n:]+mylist[:n]


if __name__ == "main__":

    #import xarray as xr

    nt = 2
    ny, nx = 4, 3

    N = nt*ny*nx

    phi = np.arange(N)
    phi.shape = (nt, ny, nx)
    print(phi)

    dims = ("t", "y", "x")
    attrs = {"name": "phi",
             "long_name": "temperature",
             "unit": "degree Celsius"}

    Phi = Marray(phi, dims=dims, attrs=attrs, stagg={"x": True})
    print(Phi)

    # # to convert a MyArray into an xarray
    # q = xr.DataArray(Phi)

    # # load an xarray dataset
    # ds = xr.load_dataset("/home/roullet/data/Nyles/TG_8/TG_8_00_hist.nc")
    # # grab a variable
    # b = ds["b"]
    # # convert it into a myarray
    # B = Marray(b)
