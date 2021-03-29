"""
 Demo on howto convert netCDF files to RGDF files
"""

from parameters import Param
import ncconvert

# load the paragridded parameters
param = Param()

# create the convert device
conv = ncconvert.Convert(param)

# regions and dates to proceed
regions = [2]
dates = ["2009-06-02"]

conv.proceed(regions, dates, nworkers=8)

