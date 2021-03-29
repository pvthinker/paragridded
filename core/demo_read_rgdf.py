"""
 Demo on howto read a variable in the rgdf format
"""

from parameters import Param
import rgdf
import matplotlib.pyplot as plt
import time

plt.ion()

# load the paragridded parameters
param = Param()

# setup readers
rgdf.setup_predefine_readers(param)

# what we want to read
# a snapshot
date = "2009-06-02"
hour = 14
tile = 745
varname = "zeta"

tic = time.time()
data = rgdf.read(tile, date, hour, varname)
toc = time.time()
elapsed = toc-tic
print(f"time to read: {elapsed:.3g} s")

plt.figure()
plt.imshow(data)
