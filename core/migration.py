"""
Tools to handle the migration from tapes to disk at TGCC
"""
import os
import subprocess

PIPE = subprocess.PIPE

def get_status(param, subd, date, filetype):
    assert filetype in ["tar", "bin"]
    
    if filetype == "tar":
        filename = f"{param.dirgigaref}/{subd:02}/gigatl1_his_1h.{date}.{subd:02}.tar"
    elif filetype == "bin":
        filename = f"{param.dirgigabin}/{subd:02}/giga_{date}_{subd:02}.dat"

    command = ["ccc_hsm", "status", filename]
    
    result = subprocess.run(command, stdout=PIPE, stderr=PIPE)
    print(result.stdout)
    if len(result.stdout) == 0:
        status = "missing"
    else:
        status = result.stdout.split()[-1].decode("utf8")

    # status : "released", "online"
    return status
