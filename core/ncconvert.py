"""
 Convert netCDF files to RGDF files

 if properly parallelized the typical performance is 25 s/GB of data converted
 per thread

 properly means one or two threads at maximum per tar file

 if more threads per tar file the conversion slows down. This is likely because tar files are stored on only 2 OSTs.

"""

import numpy as np
import glob
import os
import time
import schwimmbad
import tar_tools as tt
import rgdf


class Convert():
    def __init__(self, param):
        self.param = param

        # create the untar device
        self.tg = tt.TarGiga(param)

        # setup readers
        rgdf.setup_predefine_readers(param)

        tilesperregion = [643, 525, 416, 475, 568,
                          653, 364, 285, 549, 549, 454, 450, 651]

        self.stripesize = 711393280  # one tile, 24hours, all variables
        # self.ntiles is used to define the size of the empty RGDF file
        self.ntiles = {subd: tilesperregion[subd-1] for subd in range(1, 14)}

    def partial(self, subd, tiles, dates, nworkers=31):
        assert isinstance(dates, list)
        assert isinstance(tiles, list)
        for date in dates:
            self.create_destdir(date, subd)
            self.allocate_empty_binfile(date, subd)

        tasks = [(date, subd, t) for t in tiles for date in dates]

        pool = schwimmbad.MultiPool(processes=nworkers+1)
        tic = time.time()
        pool.map(self.task_extract_convert, tasks)
        toc = time.time()
        elapsed = toc-tic
        print(
            f"time to convert {len(tasks)} tiles with {nworkers} workers: {elapsed:.4} s")
        pool.close()

        for date in dates:
            self.cleantar(date, subd)
        
    def proceed2(self, subd, dates):
        assert isinstance(dates, list)
        nworkers = len(dates)
        assert nworkers < 127

        tiles = [t for t, s in self.tg.subdmap.items() if s == subd]
        
        for date in dates:
            self.create_destdir(date, subd)
            self.allocate_empty_binfile(date, subd)

        tasks = [(date, subd, t) for t in tiles for date in dates]

        pool = schwimmbad.MultiPool(processes=nworkers+1)
        tic = time.time()
        pool.map(self.task_extract_convert, tasks)
        toc = time.time()
        elapsed = toc-tic
        print(
            f"time to convert {len(tasks)} tiles with {nworkers} workers: {elapsed:.4} s")
        pool.close()

        for date in dates:
            self.cleantar(date, subd)
        
    def proceed(self, subds, dates, nworkers=31):
        assert isinstance(dates, list)
        assert isinstance(subds, list)
        for date in dates:
            tasks = []
            for subd in subds:
                tasks += [(date, subd, t)
                          for t, s in self.tg.subdmap.items() if s == subd]
                self.create_destdir(date, subd)
                self.allocate_empty_binfile(date, subd)

                pool = schwimmbad.MultiPool(processes=nworkers+1)
                tic = time.time()
                pool.map(self.task_extract_convert, tasks)
                toc = time.time()
                elapsed = toc-tic
                print(
                    f"time to convert {len(tasks)} tiles with {nworkers} workers: {elapsed:.4} s")
                pool.close()

                self.cleantar(date, subd)
        
    def task_extract_convert(self, args):
        date, subd, tile = args
        if self.need_conversion(date, subd, tile):
            for quarter in range(4):
                self.tg.extract_from_tar(date, subd, tile, quarter)
            hisfiles = [self.get_hisname(date, subd, tile, quarter) for quarter in range(4)]
            rgdf.writesubd(date, tile, hisfiles)


    def create_destdir(self, date, subd):
        destdir = f"{self.param.dirscratch}/{date}/{subd:02}"
        if os.path.isdir(destdir):
            print(f"{destdir} already exists -> do nothing")
        else:
            os.makedirs(destdir)

    def cleantar(self, date, subd):
        destdir = f"{self.param.dirscratch}/{date}/{subd:02}"
        if os.path.isdir(destdir):
            files = glob.glob(f"{destdir}/*.nc")
            if len(files) > 0:
                print(
                    f"found {len(files)} netcdf files in {destdir} -> cleaning")
                for f in files:
                    os.remove(f)
            else:
                print(f"{destdir} is already converted")
        else:
            print(f"{destdir} not yet converted")

    def allocate_empty_binfile(self, date, subd):
        binfile = f"{self.param.dirgigabin}/{subd:02}/giga_{date}_{subd:02}.dat"
        filesize = self.stripesize * self.ntiles[subd]
        if os.path.isfile(binfile):
            print(f"Warning {binfile} already exist")
        else:
            command = f"dd if=/dev/zero of={binfile} bs=1 count=0 seek={filesize}"
            print(command)
            os.system(command)

    def need_conversion(self, date, subd, tile):
        """Determine if this tile at this date needs to be converted

        Method: read zeta @ hour=23 and check whether it's all 0"""
        reader = rgdf.predefined_readers[subd]
        data = reader.read(tile, date, 23, "zeta")
        return np.allclose(data, 0)


    def get_hisname(self, date, subd, tile, quarter):
        directory = f"{self.param.dirscratch}/{date}/{subd:02}"
        hisname = f"{directory}/gigatl1_his.{quarter*6:02}.{tile:04}.nc"
        return hisname

