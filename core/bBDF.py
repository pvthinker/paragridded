"""
Basic Binary Data Format

"""
import numpy as np
import os
import yaml
import io

ENCODING = "utf-8"
FIRST_LINE = "#BBDF 1.0 Basic Binary Data Format"
LAST_LINE = "# >>> data start below >>>"
DEFAULT_DTYPE = "f"

header_sample = """\
#BBDF 1.0 Basic Binary Data Format
headersize: 1000
stripes:
  size: 7168
  roundingsize: 1024
dimensions:
  tile: 4
  time: 10
variables:
  temp:
    shape: [10, 5]
    dtype: f
    longname: temperature
    units: degree C
  u:
    shape: [10, 6]
    dtype: f
    longname: along-i velocity
    units: m s^-1
  v:
    shape: [11, 5]
    dtype: f
    longname: along-j velocity
    units: m s^-1
  time:
    shape: 1
    longname: time
    units: days since 2000-01-01
attrs:
  author: G. Roullet
  source: Euler2d code
tiles: [0, 1, 2, 3]
# >>> data start below >>>
"""


def roundup(x, y):
    return int(y*np.ceil(x/y))


class Dataset():
    def __init__(self, filename):
        self.filename = filename
        self.has_stripes = False
        self.ndims = 0

    def set_structure(self, userinfos):
        self.infos = userinfos
        self.header = generate_header(userinfos)
        self.has_stripes = "stripes" in userinfos
        self.ndims = len(userinfos["dimensions"])
        self.dims = tuple(userinfos["dimensions"].keys())
        self.set_dimcount(userinfos)
        self.set_offsets(userinfos)
        self.update_infos()
        #self.header = generate_header(self.infos)
        # self.write_header()

    def get_structure(self):
        hs = retrieve_headersize(self.filename)
        header = read_header(self.filename, hs)
        userinfos = retrieve_infos(header)
        self.infos = userinfos
        self.header = header
        self.has_stripes = "stripes" in userinfos
        self.ndims = len(userinfos["dimensions"])
        self.dims = tuple(userinfos["dimensions"].keys())
        self.set_dimcount(userinfos)
        self.set_offsets(userinfos)
        self.update_infos()

        return userinfos

    @property
    def filesize(self):
        dim0 = self.dims[0]
        datasize = self.dimcount[dim0]*self.dimsize[dim0]
        if self.has_stripes:
            return datasize
        else:
            headersize = len(self.header)
            return headersize+datasize

    def update_infos(self):
        realheadersize = len(self.header)
        if self.infos["headersize"] == 0:
            self.infos["headersize"] = realheadersize
        assert self.infos["headersize"] >= realheadersize
        self.headersize = self.infos["headersize"]

        # STRIPESIZE NEEDS MORE CLEANUP/DEBUG -> still fragile
        if self.has_stripes:
            if self.infos["stripes"]["size"] == 0:
                self.infos["stripes"]["size"] = self.stripesize
            else:
                self.stripesize = self.infos["stripes"]["size"]

            if self.infos["stripes"]["size"] != self.stripesize:
                userstripesize = self.infos["stripes"]["size"]
                print(
                    f"[WARNING] user stripesize {userstripesize} differs from computed one {self.stripesize}")

    def set_dimcount(self, infos):
        self.dimcount = {}
        for name, size in infos["dimensions"].items():
            if isinstance(size, list):
                count = len(size)
            else:
                count = size
            self.dimcount[name] = count

    def set_offsets(self, infos):
        self.toc = {}
        offset = 0
        for name, varinfos in infos["variables"].items():
            shape = varinfos["shape"]
            if "dtype" in varinfos:
                dtype = varinfos["dtype"]
            else:
                dtype = DEFAULT_DTYPE

            if isinstance(shape, int):
                shape = [shape]
            self.toc[name] = {"shape": tuple(shape),
                              "offset": offset,
                              "dtype": dtype}
            offset += np.nbytes[dtype]*np.prod(shape)

        self.dimsize = {}
        for k in range(self.ndims-1, -1, -1):
            name = self.dims[k]
            if (k == 0) and self.has_stripes:
                roundingsize = infos["stripes"]["roundingsize"]
                stripesize = infos["stripes"]["size"]
                offset = stripesize  # roundup(offset, roundingsize)
                #self.stripesize = offset
            self.dimsize[name] = offset
            offset = self.dimsize[name]*self.dimcount[name]

    def read_variable(self, name, idx):
        offset = self.get_offset(name, idx)
        shape = self.toc[name]["shape"]
        dtype = self.toc[name]["dtype"]
        count = np.prod(shape)
        data = np.fromfile(self.filename,
                           count=count,
                           offset=offset,
                           dtype=dtype)
        if shape is 1:
            data = data[0]
        else:
            data.shape = shape
        return data

    def get_offset(self, name, idx):
        if self.ndims > 1:
            assert len(idx) == self.ndims
            baseoffset = self.headersize
            for k in range(self.ndims):
                dname = self.dims[k]
                assert idx[k] < self.dimcount[dname]
                baseoffset += +self.dimsize[dname]*idx[k]
        else:
            dname = self.dims[0]
            assert idx < self.dimcount[dname]
            baseoffset = self.headersize+self.dimsize[dname]*idx

        offset = baseoffset + self.toc[name]["offset"]
        return offset

    def write_variable(self, name, data, idx):
        offset = self.get_offset(name, idx)
        shape = self.toc[name]["shape"]
        dtype = self.toc[name]["dtype"]
        with open(self.filename, "rb+") as fid:
            fid.seek(offset)
            if shape == (1,):
                data = np.asarray(data)
            fid.write(data.astype(dtype).tobytes())

    def write_header(self):
        flag = "br+" if os.path.isfile(self.filename) else "bw"
        with open(self.filename, flag) as fid:
            data = np.asarray(self.header, dtype="c")
            fid.write(data.tobytes())

    def allocate_empty_file(self, force=False):
        binfile = self.filename
        filesize = self.filesize
        if os.path.isfile(binfile):
            print(f"[WARNING] {binfile} already exists -> do nothing")
        elif (filesize <= 1024**2) or force:
            command = f"dd if=/dev/zero of={binfile} bs=1 count=0 seek={filesize}"
            os.system(command)
        else:
            print(f"[WARNING] {binfile} is too large (use force=True)")


def retrieve_headersize(filename):
    headersize = -1
    with open(filename, "br") as fid:
        while True:
            line = fid.readline()
            if len(line) > 0:
                words = line.split()
                word = words[0].decode(ENCODING)
                if word == "headersize:":
                    headersize = int(words[1])
                    break
    return headersize


def check_header(filename, headersize, header):
    #header = read_header(filename, headersize)
    lines = header.split("\n")
    size = 0
    for line in lines:
        size += len(line)+1
        if line == LAST_LINE:
            break
    assert size <= headersize, f"headersize is {headersize} but it should be at least {size}"
    return size


def read_header(filename, headersize):
    header = np.fromfile(filename, count=headersize, dtype="i1")
    header = "".join([chr(asciicode) for asciicode in header])
    return header


def retrieve_infos(header):
    end = header.find(LAST_LINE)
    with io.StringIO(header[:end]) as stream:
        infos = yaml.load(stream,  Loader=yaml.FullLoader)
    return infos


def read_infos(filename):
    headersize = retrieve_headersize(filename)
    header = read_header(filename, headersize)
    return retrieve_infos(header)


def convert_list_to_str(infos: dict) -> dict:
    """replace all lists and tuples in a (nested) dictionary
    with strings.

    example:

    [0, 1, 2] -> "list([0, 1, 2])"

    this is to force lists and tuples to appear as a single line in
    a yaml file rather being written over as many lines as the
    number of elements
    """
    newinfos = {}
    for key, val in infos.items():
        if isinstance(val, dict):
            newinfos[key] = convert_list_to_str(val)
        elif isinstance(val, list):
            newinfos[key] = f"{val}"
        elif isinstance(val, tuple):
            newinfos[key] = f"{list(val)}"
        else:
            newinfos[key] = val
    return newinfos


def generate_header(infos):
    content = ""
    with io.StringIO() as stream:
        myinfos = convert_list_to_str(infos)
        yaml.safe_dump(myinfos, stream, indent=2,
                       sort_keys=False, width=120)
        stream.seek(0)
        content = stream.readlines()

    content.insert(0, FIRST_LINE+"\n")
    content += [LAST_LINE+"\n"]

    header = fix_lists("".join(content))
    # fill with white spaces
    headersize = infos["headersize"]
    header += "."*(headersize-len(header))
    return header


def fix_lists(yaml_str):
    fixed_str = yaml_str.replace("'[", "[").replace("]'", "]")
    return fixed_str


def generate_sample(samplefile):

    infos = retrieve_infos(header_sample)

    ds = Dataset(samplefile)
    ds.set_structure(infos)
    print(ds.header)
    print(f"filesize: {ds.filesize} B")
    ds.allocate_empty_file()
    ds.write_header()


def write_sample(samplefile):

    ds = Dataset(samplefile)
    infos = ds.get_structure()

    k = 0
    for name, props in infos["variables"].items():
        shape = props["shape"]
        dtype = "f"
        if "dtype" in props:
            dtype = props["dtype"]
        data = np.zeros(shape, dtype=dtype)
        for idx in np.ndindex(tuple(infos["dimensions"].values())):
            data.flat = k
            # print(name, shape, idx, k)
            ds.write_variable(name, data, idx)
            k += 1


def read_sample(samplefile):
    ds = Dataset(samplefile)
    infos = ds.get_structure()

    data = ds.read_variable("temp", (1, 0))
    assert np.allclose(data, 10.)

    data = ds.read_variable("time", (3, 9))
    assert np.allclose(np.asarray(data), 159.)


class FastRead():
    def __init__(self, dataset):
        self.dataset = dataset
        self.fid = open(dataset.filename, "br")
        self.is_open = True

    def close(self):
        self.fid.close()
        self.is_open = False

    def prefetch0(self, ncount=24):
        assert self.is_open, f"file is closed"
        filesize = self.dataset.filesize
        data = np.zeros((1,), dtype="i")
        for k in range(ncount):
            offset = k*filesize//ncount
            self.fid.seek(offset)
            self.fid.readinto(data)

    def prefetch(self, name, idx):
        assert self.is_open, f"file is closed"
        offset = self.dataset.get_offset(name, idx)
        data = np.zeros((1,), dtype="b")
        self.fid.seek(offset)
        self.fid.readinto(data)

    def read(self, name, idx):
        assert self.is_open, f"file is closed"
        offset = self.dataset.get_offset(name, idx)
        toc = self.dataset.toc
        shape = toc[name]["shape"]
        dtype = toc[name]["dtype"]
        data = np.zeros(shape, dtype=dtype)
        self.fid.seek(offset)
        self.fid.readinto(data)
        return data


class FastRead2():
    def __init__(self, dataset):
        self.dataset = dataset
        self.fid = open(dataset.filename, "br")
        self.is_open = True

    def close(self):
        self.fid.close()
        self.is_open = False

    def prefetch0(self, ncount=24):
        assert self.is_open, f"file is closed"
        filesize = self.dataset.filesize
        data = np.zeros((1,), dtype="i")
        for k in range(ncount):
            offset = k*filesize//ncount
            self.fid.seek(offset)
            self.fid.readinto(data)

    def prefetch(self, name, idx):
        assert self.is_open, f"file is closed"
        offset = self.dataset.get_offset(name, idx)
        data = np.zeros((1,), dtype="b")
        self.fid.seek(offset)
        self.fid.readinto(data)

    def read(self, name, idx):
        assert self.is_open, f"file is closed"
        offset = self.dataset.get_offset(name, idx)
        toc = self.dataset.toc
        shape = toc[name]["shape"]
        dtype = toc[name]["dtype"]
        data = np.zeros(shape, dtype=dtype)
        self.fid.seek(offset)
        self.fid.readinto(data)
        return data


if __name__ == "__main__":

    samplefile = "samplefile.dat"

    generate_sample(samplefile)

    write_sample(samplefile)

    read_sample(samplefile)
