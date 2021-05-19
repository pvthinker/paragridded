import numpy as np
import giga_tools as giga
import rgdf
import os
import glob
import schwimmbad
import time
import subprocess
import tar_tools as tt
import pool_tools as pt
import pickle

PIPE = subprocess.PIPE

stripesize = 711393280  # one tile, 24hours, all variables

# regions to proceed

regions = [10]

tilesperregion = [643, 525, 416, 475, 568,
                  653, 364, 285, 549, 549, 454, 450, 651]

ntiles = {subd: tilesperregion[subd-1] for subd in range(1, 14)}

date = "2008-09-26"

dirgigaref = "/ccc/store/cont003/gch0401/gch0401/GIGATL1_1h_tides/HIS_1h"
databin = "/ccc/store/cont003/gch0401/groullet/dat"

# lfs setstripe -c -1 -S 177864704 giga
dirscratch = "/ccc/scratch/cont003/gen7638/groullet/giga"

rgdf.setup_predefine_readers(databin)


def get_tar_struct(subd):
    tardir = f"{dirgigaref}/{subd:02}"
    tarfiles = sorted(glob.glob(f"{tardir}/*.tar"))
    sizes = {f: os.path.getsize(f) for f in tarfiles}
    size_set = set(sizes.values())

    struct = {}
    for tarsize in size_set:
        # pick the first fname whose size is tarsize
        tarfile = next((fname for fname, fsize in sizes.items()
                        if fsize == tarsize), None)
        # reverse the name list to pick the last one
        names = reversed(list(sizes.keys()))
        tarfile = next(
            (fname for fname in names if sizes[fname] == tarsize), None)
        print(tarfile)
        toc = tt.get_toc(tarfile)
        # transform toc into a dict with (tile, quarter) as key
        # and where (tile, quarter) is deduced from filename
        assert len(toc) % 4 == 0
        ntiles = len(toc) // 4
        s = {}
        for k, t in enumerate(toc):
            block, size, fname = t
            tile = int(fname.split(".")[-2])
            quarter = k // ntiles
            s[(tile, quarter)] = (block, size)
        struct[tarsize] = s
    return struct


def load_tar_struct(tarpklfile):
    if os.path.isfile(tarpklfile):
        with open(tarpklfile, "rb") as f:
            tar_struct = pickle.load(f)
    else:
        # no choice, we need to scan the database to figure out
        # how tarfiles are organized
        # to speed up, we can do that in parallel
        # one thread per subd
        res = mypool(get_tar_struct, range(1, 14))
        # make it a neat dict with subd as key
        tar_struct = {k+1: r for k, r in enumerate(res)}
        with open(tarpklfile, "wb") as f:
            pickle.dump(tar_struct, f)
    return tar_struct

# [groullet@irene194 10]$ ccc_mprun -A gen12051 -p rome -n 16 -T 1500 dcp /ccc/store/cont003/gch0401/gch0401/GIGATL1_1h_tides/HIS_1h/10/gigatl1_his_1h.2008-10-06.10.tar .
# [2021-01-05T16:07:55] Data: 363.683 GB (390501376000 bytes)
# [2021-01-05T16:07:55] Rate: 801.267 MB/s (390501376000 bytes in 464.778 seconds)


tarpklfile = f"{param.dirmodule}/data/tar_struct.pkl"
tar_struct = load_tar_struct(tarpklfile)


def extract_from_tar(date, subd, tile, quarter, verbose=True):
    tiles = [t for t, s in giga.subdmap.items() if s == subd]
    assert tile in tiles
    itile = tiles.index(tile)

    tarfile = f"{dirgigaref}/{subd:02}/gigatl1_his_1h.{date}.{subd:02}.tar"
    destdir = f"{dirscratch}/{date}/{subd:02}"
    destfile = f"gigatl1_his.{quarter*6:02}.{tile}.nc"

    print(f"extract {destfile} from {tarfile}")
    if not os.path.isdir(destdir):
        os.makedirs(destdir)

    filesize = os.path.getsize(tarfile)
    block, fsize = tar_struct[subd][filesize][(tile, quarter)]
    skip = block+1
    count = fsize//512+1

    command = f"dd if={tarfile} of={destdir}/{destfile} skip={skip} count={count}"
    result = subprocess.run(command.split(), stdout=PIPE, stderr=PIPE,
                            universal_newlines=True, check=True)
    if verbose:
        print(command)
        print(result.stderr.split("\n")[-2])

    # first three bytes must be the "CDF" string
    with open(f"{destdir}/{destfile}", "rb") as fid:
        cdf = fid.read(3)
    msg = f"pb with {destfile}"
    assert cdf.decode() == "CDF", msg


def extract_from_tar_v0(date, subd, tile, quarter):

    tiles = [t for t, s in giga.subdmap.items() if s == subd]
    itile = tiles.index(tile)

    grid_present = (giga.hisdates.index(date) % 5) == 0
    blocks_per_tile = 347312
    blocks_firsttile = 348709
    if grid_present:
        if quarter == 0:
            skip = itile*blocks_firsttile + 1
            count = blocks_per_tile
        else:
            skip = len(tiles)*blocks_firsttile + (len(tiles) *
                                                  (quarter-1) + itile)*blocks_per_tile + 1
            count = blocks_firsttile
    else:
        skip = (len(tiles)*quarter + itile)*blocks_per_tile + 1
        count = blocks_per_tile

    hisindex = gethisindex(date)[quarter]
    tarfile = f"{dirgigaref}/{subd:02}/gigatl1_his_1h.{date}.{subd:02}.tar"
    destdir = f"{dirscratch}/{date}/{subd:02}"
    destfile = f"gigatl1_his.{hisindex}.{tile}.nc"
    command = f"dd if={tarfile} of={destdir}/{destfile} skip={skip} count={count}"
    print(f"extract {destfile} from {tarfile}")
    if not os.path.isdir(destdir):
        os.makedirs(destdir)
    os.system(command)

    # first three bytes must be the "CDF" string
    with open(f"{destdir}/{destfile}", "rb") as fid:
        cdf = fid.read(3)
    msg = f"pb with {destfile}"
    assert cdf.decode() == "CDF", msg


def untar(date, subd):
    tarfile = f"{dirgigaref}/{subd:02}/gigatl1_his_1h.{date}.{subd:02}.tar"
    destdir = f"{dirscratch}/{date}/{subd:02}"
    if os.path.isdir(destdir):
        print(f"{destdir} already exists -> do nothing")
    else:
        os.makedirs(destdir)
        command = f"tar xvf {tarfile} -C {destdir}"
        print(command)
        tic = time.time()
        os.system(command)
        toc = time.time()
        elapsed = toc-tic
        print(f"time to untar {tarfile}: {elapsed:.2} s")


def gethisindex(date, subd):
    tarfile = f"{dirgigaref}/{subd:02}/gigatl1_his_1h.{date}.{subd:02}.tar"
    firsttile = [t for t, s in giga.subdmap.items() if s == subd][0]

    command = ["tar", "tvf", tarfile, f"*{firsttile}.nc"]
    PIPE = subprocess.PIPE
    result = subprocess.run(command, stdout=PIPE,
                            stderr=PIPE, universal_newlines=True)
    hisindex = [result.stdout.split("\n")[quarter].split(
        ".")[-3] for quarter in range(4)]
    return hisindex


def gethisindex(date):
    idx = giga.hisdates.index(date) % 5
    hisindex = [f"{i*6+24*idx:06}" for i in range(4)]
    return hisindex


def create_destdir(date, subd):
    destdir = f"{dirscratch}/{date}/{subd:02}"
    if os.path.isdir(destdir):
        print(f"{destdir} already exists -> do nothing")
    else:
        os.makedirs(destdir)


def untarquarter(date, subd, quarter):
    tarfile = f"{dirgigaref}/{subd:02}/gigatl1_his_1h.{date}.{subd:02}.tar"
    destdir = f"{dirscratch}/{date}/{subd:02}"
    assert os.path.isdir(destdir)

    hisindex = gethisindex(date)[quarter]
    command = ["tar", "xvf", tarfile, f"*.{hisindex}.*.nc"]

    command = f"tar xvf {tarfile} -C {destdir} --wildcards '*.{hisindex}.*.nc'"
    print(command)
    tic = time.time()
    os.system(command)
    toc = time.time()
    elapsed = toc-tic
    print(f"time to untar {tarfile}-{hisindex}: {elapsed:.2} s")


def cleantar(date, subd):
    destdir = f"{dirscratch}/{date}/{subd:02}"
    if os.path.isdir(destdir):
        files = glob.glob(f"{destdir}/*.nc")
        if len(files) > 0:
            print(f"found {len(files)} netcdf files in {destdir} -> cleaning")
            for f in files:
                os.remove(f)
        else:
            print(f"{destdir} is already converted")
    else:
        print(f"{destdir} not yet converted")


def allocate_empty_binfile(date, subd):
    binfile = f"{databin}/{subd:02}/giga_{date}_{subd:02}.dat"
    filesize = stripesize * ntiles[subd]
    if os.path.isfile(binfile):
        print(f"Warning {binfile} already exist")
    else:
        command = f"dd if=/dev/zero of={binfile} bs=1 count=0 seek={filesize}"
        print(command)
        os.system(command)

# giga.hisdate = date
# for subd in regions:
#     giga.mount(subd)


def get_hisname(date, subd, tile, quarter):
    directory = f"{dirscratch}/{date}/{subd:02}"
    hisname = f"{directory}/gigatl1_his.{quarter*6:02}.{tile:04}.nc"
    return hisname


def get_hisname_v0(date, subd, tile, quarter):
    directory = f"{dirscratch}/{date}/{subd:02}"
    files = sorted(glob.glob(f"{directory}/gigatl1_his.*.{tile:04}.nc"))
    _dateindex = [int(f.split(".")[-3]) for f in files]
    _hisindex = _dateindex[quarter]
    hisname = f"{directory}/gigatl1_his.{_hisindex:06}.{tile:04}.nc"
    return hisname


def task(args):
    date, subd, tile = args
    hisfiles = [get_hisname(date, subd, tile, quarter) for quarter in range(4)]
    rgdf.writesubd(date, tile, hisfiles)


def task_untar(args):
    date, subd = args
    untar(date, subd)


def task_untarquarter(args):
    date, subd, quarter = args
    untarquarter(date, subd, quarter)


def task_extract(args):
    date, subd, tile, quarter = args
    extract_from_tar(date, subd, tile, quarter)


def need_conversion(date, subd, tile):
    """Determine if this tile at this date needs to be converted

    Method: read zeta @ hour=23 and check whether it's all 0"""
    reader = rgdf.predefined_readers[subd]
    data = reader.read(tile, date, 23, "zeta")
    return np.allclose(data, 0)


def task_extract_convert(date, subd, tile):
    if need_conversion(date, subd, tile):
        for quarter in range(4):
            extract_from_tar(date, subd, tile, quarter)
        hisfiles = [get_hisname(date, subd, tile, quarter)
                    for quarter in range(4)]
        rgdf.writesubd(date, tile, hisfiles)

 # time to convert 549 tiles with 40 workers: 4.4e+02 s
# time to convert 549 tiles with 80 workers: 471.5 s
# time to convert 549 tiles with 20 workers: 407.3 s
# time to convert 549 tiles with 10 workers: 509.8 s
# time to convert 2745 tiles with 20 workers: 1.482e+03 s (5 dates, region 10)
# time to convert 549 tiles with 40 workers: 740.8 s including untar (task_extract)
# time to convert 549 tiles with 31 workers: 664.0 s including untar (task_extract)
# time to convert 549 tiles with 31 workers: 626.5 s including untar (task_extract)

# pb with /ccc/store/cont003/gch0401/gch0401/GIGATL1_1h_tides/HIS_1h/10/gigatl1_his_1h.2008-10-10.09.tar
# tar tvfR  returns bad blocks
# [groullet@irene194 10]$ tar tvfR /ccc/store/cont003/gch0401/gch0401/GIGATL1_1h_tides/HIS_1h/10/gigatl1_his_1h.2008-10-10.10.tar *.6444.nc
# block 348709: -rw-r----- gulaj/gch0401 178538268 2020-07-18 21:04 gigatl1_his.000000.6444.nc
# block 191788553: -rw-r----- gulaj/gch0401 177822960 2020-07-18 22:02 gigatl1_his.000006.6444.nc
# block 382462841: -rw-r----- gulaj/gch0401 177822960 2020-07-18 23:00 gigatl1_his.000012.6444.nc
# block 573137129: -rw-r----- gulaj/gch0401 177822960 2020-07-18 23:58 gigatl1_his.000018.6444.nc
# block 763464105: ** Block of NULs **
# en fait c'est parce que le tar a embarqué la grille


def convert_fulltar(date, subd):
    tasks = [(date, subd, t)
             for t, s in giga.subdmap.items() if s == subd]
    create_destdir(date, subd)
    allocate_empty_binfile(date, subd)

    pool = schwimmbad.MultiPool(processes=nworkers+1)
    tic = time.time()
    pool.map(task_extract_convert, tasks)
    toc = time.time()
    elapsed = toc-tic
    print(
        f"time to convert {len(tasks)} tiles with {nworkers} workers: {elapsed:.4} s")
    pool.close()

    cleantar(date, subd)


def convert_fulltimeseries(tile):
    """ tile = 6443
    tile,subd=gs.find_tile_at_point(-32.28,37.39) -> 7063
    """
    subd = giga.subdmap[tile]
    lastindex = giga.hisdates.index("2008-09-26")
    dates = giga.hisdates  # [:lastindex]
    tasks = [(date, subd) for date in dates]
    pt.mypool(create_destdir, tasks)
    pt.mypool(allocate_empty_binfile, tasks)

    tasks = [(date, subd, tile) for date in dates]
    tic = time.time()
    pt.mypool(task_extract_convert, tasks)
    toc = time.time()
    elapsed = toc-tic
    print(
        f"time to convert fulltimeseries of tile {tile} with {nworkers} workers: {elapsed:.4} s")


nworkers = 31

idate = giga.hisdates.index("2008-12-19")
ndates = 20
#hisdates = [giga.hisdates[i+1+idate] for i in range(ndates)]
hisdates = giga.hisdates[idate:]

hisdates = ["2008-09-26"]
regions = list(range(11, 14))
for date in hisdates:

    nworkers = 31
    tasks = []
    for subd in regions:
        tasks += [(date, subd, t)
                  for t, s in giga.subdmap.items() if s == subd]
        create_destdir(date, subd)
        allocate_empty_binfile(date, subd)

        pool = schwimmbad.MultiPool(processes=nworkers+1)
        tic = time.time()
        pool.map(task_extract_convert, tasks)
        toc = time.time()
        elapsed = toc-tic
        print(
            f"time to convert {len(tasks)} tiles with {nworkers} workers: {elapsed:.4} s")
        pool.close()

        cleantar(date, subd)

exit()
# time to extract all tiles from region 10 with 20 workers: 500.4 s (task_extract)
nworkers = 20
tasks = []
date = "2008-10-07"
for subd in regions:
    tasks += [(date, subd, t, quarter) for quarter in range(4)
              for t, s in giga.subdmap.items() if s == subd]

create_destdir(date, subd)
pool = schwimmbad.MultiPool(processes=nworkers+1)
tic = time.time()
pool.map(task_extract, tasks)
toc = time.time()
elapsed = toc-tic
print(
    f"time to extract all tiles from region {subd:02} with {nworkers} workers: {elapsed:.4} s")
pool.close()


# ttiles = []
# for i in range(nworkers):
#     ttiles += tiles[i::nworkers]


# roughly 1300s to untar four (subd=10) region
# roughly 1400s to untar five (subd=10) region with 1 proc per quarter -> 20 procs
idate = giga.hisdates.index("2008-09-30")
ndates = 5
hisdates = [giga.hisdates[i+1+idate] for i in range(ndates)]
for date in hisdates:
    create_destdir(date, subd)

nworkers = ndates*4
tasks = [(hisdates[i], subd, quarter)
         for i in range(ndates) for quarter in range(4)]

pool = schwimmbad.MultiPool(processes=nworkers+1)
pool.map(task_untarquarter, tasks)
pool.close()
