"""
 Tools to manage the RGDF database
"""

from parameters import Param
import rgdf
import glob

param = Param()


def get_whatisdone(param, subd):
    """ return the list of dates that are completed in region subd
    """
    pattern = f"{param.dirgigabin}/{subd:02}/giga_*_{subd:02}.dat"
    files = glob.glob(pattern)
    dates = [f.split("/")[-1].split("_")[1] for f in files]
    return dates
    
def scan_all(param):
    dates = {}
    for subd in range(1, 14):
        dates[subd] = get_whatisdone(param, subd)
    return dates
