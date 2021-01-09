import math
import subprocess
import os

PIPE = subprocess.PIPE


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
