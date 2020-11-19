""" GIGATL experiment specifications

 dimpart contains

   - "netcdfdimnames": how to map netCDF to CROCO dimensions
   - "domainpartition": which CROCO dimensions are tiled

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

domain = os.popen("hostname -d").read()

if "tgcc" in domain:
    hostname = "irene"

elif "univ-brest" in domain:
    hostname = os.popen("hostname").read()[:-1]

else:
    raise ValueError("Could not find the Gigatl data")

print(f"hostname: {hostname}")

if hostname == "irene":
    dirgridtar = "/ccc/store/cont003/gch0401/gch0401/GIGATL1_1h_tides/GRD/{subd:02}"

    dirgiga = "/ccc/store/cont003/gch0401/gch0401/GIGATL1_1h_tides/HIS_1h/{subd:02}"

    # fix_filename_on_store
    # dirsurf = "/ccc/store/cont003/gch0401/gch0401/GIGATL1_1h_tides/SURF"

    dirmounted = "/ccc/work/cont003/gen7638/groullet/gigatl"

    dirgrid = dirmounted+"/GRD/{subd:02}"
    dirhis = dirmounted+"/HIS/{subd:02}"
    # or use directly
    # dirgrid = "/ccc/scratch/cont003/ra4735/gulaj/GIGATL1/INIT_N100_100_100/GRD3"

    # hisindex = [0, 6, 12, 18] | [24, 30, 36, 42] | [48, 54, 60, 66]
    # | [72, 78, 84, 90] | [96, 102, 108, 114]
    # e.g. "2008-09-19" contains [96, 102, 108, 114]
    hisindex = 36

    # hisdate = "2008-03-14" .. "2008-11-18" (included)
    # 250 days as of Nov 17th 2020
    hisdate = "2008-09-26"

    targridtemplate = "gigatl1_grd_masked.{subd:02}.tar"
    tarhistemplate = "gigatl1_his_1h.{hisdate}.{subd:02}.tar"


else:
    dirgrid = "/net/omega/local/tmp/1/gula/GIGATL1/GIGATL1_1h_tides/GRD"
    dirsurf = "/net/omega/local/tmp/1/gula/GIGATL1/GIGATL1_1h_tides/SURF/gigatl1_surf.2008-05-23"
    dirgiga = "/net/omega/local/tmp/1/gula/GIGATL1/GIGATL1_1h_tides/HIS_1h"
    dirmounted = "/net/omega/local/tmp/1/roullet/gigatl"

    dirhis = dirmounted+"/HIS/{subd:02}"
    hisindex = 72
    hisdate = "2008-09-23"
    tarhistemplate = "gigatl1_his_1h.{hisdate}.{subd:02}.tar"


hour = 14

sqlitesdir = f"{dirmounted}/sqlites"

if not os.path.exists(sqlitesdir):
    os.makedirs(sqlitesdir)


def grdfiles(tile):
    subd = subdmap[tile]
    directory = dirgrid.format(subd=subd)
    filename = f"{directory}/gigatl1_grd_masked.{tile:04}.nc"
    return filename


def surffiles(tile):
    return f"{dirsurf}/gigatl1_surf.{tile:04}.nc"


def hisfiles(tile):
    subd = subdmap[tile]
    directory = dirhis.format(subd=subd)
    files = sorted(glob.glob(f"{directory}/gigatl1_his.*.{tile:04}.nc"))
    _dateindex = [int(f.split(".")[-3]) for f in files]
    _hisindex = _dateindex[int(hour)//6]
    filename = f"{directory}/gigatl1_his.{_hisindex:06}.{tile:04}.nc"
    return filename


def get_subdmap(directory):
    """Reconstruct how netCDF files are stored in fused directory

    directory == dirgrid | dirhis """
    _subdmap = {}
    for subd in subdomains:
        fs = glob.glob(directory.format(subd=subd)+"/*.nc")
        tiles = [int(f.split(".")[2]) for f in fs]
        for t in tiles:
            _subdmap[t] = subd
    return _subdmap


def mount_tar(source, tarfile, destdir):
    """
    source: str, directory of the tar files
    template: str, template name for the tar file containing "{subd"
    subd: int, index of the subdomain (0<=subd<=13)
    destdir: str, directory where to archivemount

    """

    srcfile = f"{source}/{tarfile}"
    print(f"mount {srcfile} on {destdir}")
    assert os.path.isfile(srcfile), f"{srcfile} does not exsit"

    mount = "ratarmount"
    options = ""  # "-c -gs 160000"
    msg = "{mount} is not installed"
    whichmount = os.popen(f"which {mount}").read()
    assert len(whichmount) > 0, msg

    sqlitefile = get_sqlitefilename(srcfile)
    home = os.path.expanduser("~")
    ratardirsqlite = f"{home}/.ratarmount"

    if os.path.isfile(f"{ratardirsqlite}/{sqlitefile}"):
        # nothing to do
        pass
    else:
        if os.path.isfile(f"{sqlitesdir}/{sqlitefile}"):
            command = f"cp {sqlitesdir}/{sqlitefile} {ratardirsqlite}"
            os.system(command)

    command = f"{mount} {options} {srcfile} {destdir}"
    os.system(command)

    if os.path.isfile(f"{sqlitesdir}/{sqlitefile}"):
        # nothing to do
        pass
    else:
        command = f"cp {ratardirsqlite}/{sqlitefile} {sqlitesdir}"
        os.system(command)


def mount(subd, grid=False, overwrite=False):
    """Mount tar file `subd`"""
    if grid:
        destdir = dirgrid.format(subd=subd)
        srcdir = dirgridtar.format(subd=subd)
        tarfile = targridtemplate.format(subd=subd)

    else:
        destdir = dirhis.format(subd=subd)
        srcdir = dirgiga.format(subd=subd)
        tarfile = tarhistemplate.format(hisdate=hisdate, subd=subd)

    tomount = True
    if os.path.exists(destdir):
        print(f"{destdir} already exists")
        if len(os.listdir(destdir)) == 0:
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
        mount_tar(srcdir, tarfile, destdir)
        if not(grid):
            write_toc(destdir, subd, hisdate)


def write_toc(destdir, subd, _hisdate):
    with open(f"{destdir}/../hisdate_{subd:02}.txt", mode="w") as fid:
        fid.write(_hisdate)


def read_toc(destdir, subd):
    with open(f"{destdir}/../hisdate_{subd:02}.txt", mode="r") as fid:
        return fid.read()


def mount_all(grid=False):
    for subd in subdomains:
        mount(subd, grid=grid)


def mount_stats(grid=False):
    """ Print statistics on mounted tar files"""

    print("-"*40)
    print(BB("statistics on mounted tar files"))
    print(f"mounting point: {dirmounted}")

    for subd in subdomains:
        if grid:
            destdir = dirgrid.format(subd=subd)
        else:
            destdir = dirhis.format(subd=subd)
        if os.path.exists(destdir):
            filelist = os.listdir(f"{destdir}")
            nbfiles = len(filelist)
            if nbfiles > 0:
                tiles = set([int(f.split(".")[-2]) for f in filelist])
                nbtiles = len(tiles)
                tile = list(tiles)[0]
                fs = [f for f in filelist if f"{tile:04}.nc" in f]
                if grid:
                    msg = f"  - {subd:02} : {nbtiles:03} tiles"
                else:
                    _hisdate = read_toc(destdir, subd)
                    # dateindex = sorted([int(f.split(".")[-3]) for f in fs])
                    # msg = f"  - {subd:02} : {nbtiles:03} tiles x {dateindex} dateindex"
                    msg = f"  - {subd:02} : {_hisdate} with {nbtiles:03} tiles"
            else:
                msg = f"  - {subd:02} : empty"
        else:
            warning = BB("destroyed")
            msg = f"  - {subd:02} : {warning}"
        print(msg)


def umount_all(grid=False):
    for subd in subdomains:
        umount(subd, grid=grid)


def umount(subd, grid=False):
    """ Unmount `subd` tar archive folder

    The command to unmount a fuse folder is fusermount -u"""

    if grid:
        destdir = dirgrid.format(subd=subd)

    else:
        destdir = dirhis.format(subd=subd)

    if os.path.isdir(destdir) and len(os.listdir(f"{destdir}")) != 0:
        command = f"fusermount -u {destdir}"
        os.system(command)
        command = f"rmdir {destdir}"
        os.system(command)
    else:
        print(f"{destdir} is already umounted")


def get_sqlitefilename(tarfile):
    sqlitefile = "_".join(tarfile.split("/"))+".index.sqlite"
    return sqlitefile


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


def get_dates():
    """
    Scan dirgiga for *tar files
    """
    subd = 1
    pattern = f"{dirgiga}/*.{subd:02}.tar".format(subd=subd)
    files = glob.glob(pattern)
    _dates_tar = [f.split("/")[-1].split(".")[-3] for f in files]
    return sorted(_dates_tar)


def get_hisindexes_in_histar(hisdate):
    # select one subd
    subd = 1
    # select one tile in this subd
    tile = [t for t, s in subdmap.items() if s == subd][0]

    tarfile = "/".join([dirgiga, tarhistemplate])
    tarfile = tarfile.format(hisdate=hisdate, subd=subd)

    files = os.popen(f"tar tvf {tarfile} *{tile:04}.nc").readlines()
    hisindexes = [int(f.split(".")[-3]) for f in files]
    return hisindexes


hisdates = get_dates()
