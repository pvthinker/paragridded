"""
 Demo on how to untar a netCDF from a tar
"""

from parameters import Param
import tar_tools as tt

# load the paragridded parameters
param = Param()

# create the untar device
tg = tt.TarGiga(param)

# select the file
date = "2009-06-02"
tile = 745
subd = tg.subdmap[tile] # region
quarter = 0 # 0, 6, 12, 18 / quarter of the day

tg.extract_from_tar(date, subd, tile, quarter)
