import os

script = "demo_convert"

def prepare_submission_script(param, script, nworkers=20, time=6000):
    dirjob = f"{param.dirmodule}/pbs"
    template = f"{param.dirmodule}/pbs/template_threads.sh"
    pyscript = f"{script}.py"
    shscript = f"{script}.sh"

    keywords = {
        "JOBNAME": script,
        "NTHREADS": nworkers+1,
        "TIME": time,
        "SCRIPT": f"{pyscript}",
        "DIRJOB": dirjob}

    replace = [f"s|#{key}#|{val}|;" for key, val in keywords.items()]
    replace = " ".join(replace)
    command = f"sed '{replace}' {template} > {dirjob}/{shscript}"
    print(command)
    os.system(command)

    with open(f"{dirjob}/{shscript}", "r+") as fid:
        fid.seek(0, 2)
        fid.write(f"cat > {pyscript} << EOF\n")
        with open(f"{pyscript}", "r") as fin:
            lines = fin.readlines()
        fid.writelines(lines)
        fid.write(f"EOF\n")
        fid.write("\n")
        fid.write(f"ccc_mprun python3 {pyscript} > output_{script}.txt \n")
