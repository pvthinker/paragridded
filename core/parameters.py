try:
    from pyaml import yaml
except:
    try:
        from ruamel import yaml
    except:
        raise ValueError("install Python module: pyaml or ruamel")

import os
import pickle
from pretty import BB, MA

configdir = os.path.expanduser("~/.paragridded")
paramfile = f"{configdir}/defaults.yaml"


def get_param():
    with open(paramfile, "r") as f:
        p = yaml.load(f, Loader=yaml.Loader)
    topics = p.keys()
    param = {}
    for topic in topics:
        elems = p[topic].keys()
        for e in elems:
            #print(e, p[topic][e])
            param[e] = p[topic][e]["default"]
    return param


class Param(object):
    def __init__(self):
        param = get_param()
        self.toc = list(param.keys())
        for key, val in param.items():
            setattr(self, key, val)
        # add subdmap
        self.subdmap = self.read_data_pkl("giga_subdmap.pkl")
        # add corners
        self.corners = self.read_data_pkl("giga_corners.pkl")
        # add missing
        alltiles = range(100*100)
        self.missing = [False if tile in self.subdmap else True for tile in alltiles]


    def get_subdomains(self):
        return self.read_data_pkl("giga_subdmap.pkl")

    def read_data_pkl(self, pklfile):
        with open(f"{self.dirmodule}/data/{pklfile}", "rb") as f:
            data = pickle.load(f)
        return data
        
    def __getitem__(self, key):
        """ allows to retrieve a value as if param was a dict """
        return getattr(self, key)

    def __setitem__(self, key, val):
        if key not in self.toc:
            self.toc += [key]
        setattr(self, key, val)

    def __repr__(self):
        string = ["<Param: paragridded parameters from "
                  +BB(f"{paramfile}")+">"]
        for key in self.toc:
            val = getattr(self, key)
            string += [BB(f"{key}: ")+f"{val}"]
        
        return "\n".join(string)
