""" GIGATL experiment specifications
"""
import os
import glob
from shapely.geometry.polygon import Polygon
import pickle

subdomains = range(1, 14)

partition = (100, 100)

dimpart = {0: ("eta_rho", "eta_v"),
           1: ("xi_rho", "xi_u")}

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
        return f"{dirmounted}/{subd:02}bis/gigatl1_his.000072.{tile:04}.nc"
    else:
        return ""


def get_subdmap():
    """Reconstruct how netCDF files are stored in *.tar files"""
    subdmap = {}
    for subd in subdomains:
        fs = glob.glob(f"{dirmounted}/{subd:02}bis/*nc")
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

    destdir = f"{dest}/{subd:02}bis"
    if os.path.exists(destdir):
        print(f"{destdir} already exists")
        if overwrite:
            print("remove its content")
            os.removedirs(destdir)
        else:
            return
    os.makedirs(destdir)

    command = f"{mount} {srcfile} {destdir}"
    os.system(command)


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
