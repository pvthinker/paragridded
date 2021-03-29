from parameters import Param
import giga_subdomains as gs
import datetime as dt
import dates
import ncconvert
import migration

param = Param()

# Region 1 (Gulf Stream separation): 78W-68W, 30N-40N;
dom = ((-78, 30), (-68, 40))

# Region 2 (Gulf Stream extension): 54W-44W, 30N-40N
dom = ((-54, 30), (-44, 40))

domain = gs.LLTR2domain(*dom)
tiles = gs.find_tiles_inside(param, domain)
subds = [param.subdmap[t] for t in tiles]
print(set(subds))

# Pour les périodes:
#
# Aug., Sep. and Oct. 2008
# Feb., Mar. and Apr. 2009

d0 = dt.datetime(2008, 8, 1, 0)
d1 = dt.datetime(2008, 11, 1, 0)

d0 = dt.datetime(2009, 2, 1, 0)
d1 = dt.datetime(2009, 5, 1, 0)
hisdates = dates.daterange(d0, d1, dates.day)

subd = 10
for date in hisdates:
    datestr = date.isoformat()[:10]
    migration.get_status(param, subd, datestr, "tar")


# create the convert device
param2 = Param()
param2.dirgigabin = "/ccc/store/cont003/gch0401/gch0401/GIGATL1_1h_tides/BIN_1h"
conv = ncconvert.Convert(param2)

# regions and dates to proceed
regions = [10]
dates = [d.isoformat()[:10] for d in hisdates]

#conv.proceed(regions, [dates[0]], nworkers=20)

subd = 11
subtiles = [t for t in tiles if param.subdmap[t] == subd]
conv.partial(subd, subtiles, dates, nworkers=20)
