""" GIGATL experiment specifications
"""
import os
import glob
from shapely.geometry.polygon import Polygon
import pickle
from pretty import BB

subdomains = range(1, 14)

partition = (100, 100)

dimpart = {"netcdfdimnames":
           {"sigma": ("sigma_rho", "sigma_w"),
            "eta": ("eta_rho", "eta_v"),
            "xi": ("xi_rho", "xi_u")},
           "domainpartition": ("eta", "xi")}

dirgrid = "/net/omega/local/tmp/1/gula/GIGATL1/GIGATL1_1h_tides/GRD"
dirsurf = "/net/omega/local/tmp/1/gula/GIGATL1/GIGATL1_1h_tides/SURF/gigatl1_surf.2008-05-23"
dirgiga = "/net/omega/local/tmp/1/gula/GIGATL1/GIGATL1_1h_tides/HIS_1h"
dirmounted = "/net/omega/local/tmp/1/roullet/gigatl"
tartemplate = "gigatl1_his_1h.2008-09-23.{subd:02}.tar"


def grdfiles(tile):
    return f"{dirgrid}/gigatl1_grd_masked.{tile:04}.nc"


def surffiles(tile):
    return f"{dirsurf}/gigatl1_surf.{tile:04}.nc"


def hisfiles(tile):
    # add time in the arguments => 000072
    if tile in subdmap.keys():
        subd = subdmap[tile]
        filename = f"{dirmounted}/{subd:02}/gigatl1_his.000072.{tile:04}.nc"
    else:
        filename = ""
    return filename


def get_subdmap():
    """Reconstruct how netCDF files are stored in *.tar files"""
    subdmap = {}
    for subd in subdomains:
        fs = glob.glob(f"{dirmounted}/{subd:02}/*nc")
        tiles = [int(f.split(".")[2]) for f in fs]
        for t in tiles:
            subdmap[t] = subd
    return subdmap


def mount_tar(source, template, subd, dest, overwrite=False):
    """
    source: str, directory of the tar files
    template: str, template name for the tar file containing "{subd"
    subd: int, index of the subdomain (0<=subd<=13)
    dest: str, directory where to archivemount

    """
    assert template.find("{subd") > -1
    tarfile = template.format(subd=subd)
    srcfile = f"{source}/{tarfile}"
    print(srcfile)
    assert os.path.isfile(srcfile), f"{srcfile} does not exsit"

    mount = "ratarmount"
    msg = "{mount} is not installed"
    whichmount = os.popen(f"which {mount}").read()
    assert len(whichmount) > 0, msg

    tomount = True
    destdir = f"{dest}/{subd:02}"
    if os.path.exists(destdir):
        print(f"{destdir} already exists")
        if len(os.listdir(f"{destdir}")) == 0:
            # folder is empty
            pass
        elif overwrite:
            # folder is not empty but we want to overwrite it
            # first let's unmount it
            command = f"fusermount -u {destdir}"
            os.system(command)
            #
            assert len(os.listdir(f"{destdir}")) == 0
        else:
            tomount = False
    else:
        os.makedirs(destdir)

    if tomount:
        command = f"{mount} {srcfile} {destdir}"
        os.system(command)


def mount(subd):
    """Mount tar file `subd`"""
    destdir = f"{dirmounted}"
    mount_tar(dirgiga, tartemplate, subd, destdir)


def mount_all():
    for subd in subdomains:
        mount(subd)


def mount_stats():
    """ Print statistics on mounted tar files"""

    print("-"*40)
    print(BB("statistics on mounted tar files"))
    print(f"mounting point: {dirmounted}")
    for subd in subdomains:
        destdir = f"{dirmounted}/{subd:02}"
        if os.path.exists(destdir):
            filelist = os.listdir(f"{destdir}")
            nbfiles = len(filelist)
            if nbfiles > 0:
                tiles = set([int(f.split(".")[-2]) for f in filelist])
                nbtiles = len(tiles)
                tile = list(tiles)[0]
                fs = [f for f in filelist if f"{tile:04}.nc" in f]
                dateindex = sorted([int(f.split(".")[-3]) for f in fs])
                nbdates = len(dateindex)
                print(
                    f"  - {subd:02} : {nbtiles:03} tiles x {dateindex} dateindex")
        else:
            warning = BB("destroyed")
            print(f"  - {subd:02} : {warning}")


def umount_all():
    for subd in subdomains:
        umount(subd)


def umount(subd):
    """ Unmount `subd` tar archive folder

    The command to unmount a fuse folder is fusermount -u"""

    destdir = f"{dirmounted}/{subd:02}"
    if len(os.listdir(f"{destdir}")) != 0:
        command = f"fusermount -u {destdir}"
        os.system(command)
        command = f"rmdir {destdir}"
        os.system(command)
    else:
        print(f"{destdir} is already umounted")


def LLTP2domain(lowerleft, topright):
    """Convert the two pairs of (lower, left), (top, right) in (lat, lon)
    into the four pairs of (lat, lon) of the corners """
    xa, ya = lowerleft
    xb, yb = topright
    domain = [(xa, ya), (xa, yb), (xb, yb), (xb, ya)]
    return domain


def find_tiles_inside(domain, corners):
    """Determine which tiles are inside `domain`

    The function uses `corners` the list of corners for each tile
    """
    p = Polygon(domain)
    tileslist = []
    for tile, c in corners.items():
        q = Polygon(c)
        if p.overlaps(q) or p.contains(q):
            tileslist += [tile]
    return tileslist


# corners and submap are stored in pickle files
with open('../data/giga_corners.pkl', 'rb') as f:
    corners = pickle.load(f)
with open('../data/giga_subdmap.pkl', 'rb') as f:
    subdmap = pickle.load(f)

nsigma = 100
