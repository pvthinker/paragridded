import math
import subprocess
import os
import pool_tools as pt
import pickle
import glob

PIPE = subprocess.PIPE

class TarGiga():
    def __init__(self, param):
        self.param = param
        self.tarpklfile = f"{param.dirmodule}/data/tar_struct.pkl"
        self.tar_struct = self.load_tar_struct()
        self.subdmap = param.read_data_pkl("giga_subdmap.pkl")
        assert len(self.subdmap) == 6582, "something is wrong with data/giga_subdmap.pkl"


    def load_tar_struct(self):
        if os.path.isfile(self.tarpklfile):
            with open(self.tarpklfile, "rb") as f:
                tar_struct = pickle.load(f)
        else:
            # no choice, we need to scan the database to figure out
            # how tarfiles are organized
            # to speed up, we can do that in parallel
            # one thread per subd
            res = pt.mypool(self.get_tar_struct, range(1, 14))
            # make it a neat dict with subd as key
            tar_struct = {k+1: r for k, r in enumerate(res)}
            with open(self.tarpklfile, "wb") as f:
                pickle.dump(tar_struct, f)
        return tar_struct

    def get_tar_struct(self, subd):
        tardir = f"{self.param.gigaref}/{subd:02}"
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
            toc = get_toc(tarfile)
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

    def extract_from_tar(self, date, subd, tile, quarter, verbose=True):
        tiles = [t for t, s in self.subdmap.items() if s == subd]
        assert tile in tiles
        itile = tiles.index(tile)

        tarfile = f"{self.param.dirgigaref}/{subd:02}/gigatl1_his_1h.{date}.{subd:02}.tar"
        destdir = f"{self.param.dirscratch}/{date}/{subd:02}"
        destfile = f"gigatl1_his.{quarter*6:02}.{tile:04}.nc"

        print(f"extract {destfile} from {tarfile} and store it in {destdir}")
        if not os.path.isdir(destdir):
            os.makedirs(destdir)

        filesize = os.path.getsize(tarfile)
        block, fsize = self.tar_struct[subd][filesize][(tile, quarter)]
        skip = block+1
        count = fsize//512+1

        command = f"dd if={tarfile} of={destdir}/{destfile} skip={skip} count={count}"
        if verbose:
            print(command, flush=True)
        result = subprocess.run(command.split(), stdout=PIPE, stderr=PIPE,
                                universal_newlines=True, check=True)
        if verbose:
            print(result.stderr.split("\n")[-2])

        # first three bytes must be the "CDF" string
        with open(f"{destdir}/{destfile}", "rb") as fid:
            cdf = fid.read(3)
        msg = f"pb with {destfile}"
        assert cdf.decode() == "CDF", msg


    

def get_toc(tarfile):
    """Return the table of content of a tar file
    """
    assert os.path.isfile(tarfile)
    command = f"tar tvfR {tarfile}"
    result = subprocess.run(command.split(), stdout=PIPE, stderr=PIPE,
                            universal_newlines=True, check=True)
    out = result.stdout.split("\n")
    toc = []
    for line in out[:-2]:
        words = line.split()
        if words[1].endswith(":"): words[1] = words[1][:-1]
        bloc_start, filesize, filename = int(words[1]), int(words[-4]), words[-1]
        toc += [(bloc_start, filesize, filename)]
    return toc


def extract(tarfile, filename, destdir=".", toc=None, exact=False, verbose=True):
    """Extract filename from tarfile in destdir using toc

    extraction is done in direct access mode with dd

    Warning: the resulting file is slightly larger than in the archive,
    because dd extracts 512 bytes blocks

    the resulting file has at most 511 more bytes than the original

    to force exact same size, use exact=True
    Be aware, this makes the extraction much slower!
    """
    if toc is None:
        toc = get_toc(tarfile)
    # transform toc into dict
    content = {name: (bloc, size) for bloc, size, name in toc}
    if filename not in content:
        print(f"{filename} not found in {tarfile}")
        return

    destfile = f"{destdir}/{filename}"
    if os.path.isfile(destfile):
        print(f"{destfile} already exists, no extraction done")
        return

    bstart, size = content[filename]
    if exact:
        block_size = 1
        skip = (bstart+1)*512
        count = size
    else:
        block_size = 512
        skip = (bstart+1)
        count = size//block_size+1

    command = f"dd if={tarfile} of={destfile} bs={block_size} skip={skip} count={count}"
    result = subprocess.run(command.split(), stdout=PIPE, stderr=PIPE,
                            universal_newlines=True, check=True)
    if verbose:
        print(command)
        print(result.stderr.split("\n")[-2])


if __name__ == "__main__":
    tarfile = "scripts.tar"
    toc = get_toc(tarfile)
