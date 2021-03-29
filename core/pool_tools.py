import schwimmbad

class Unpack():
    def __init__(self, func):
        self.func = func
    def __call__(self, args):
        if isinstance(args, tuple):
            return self.func(*args)
        else:
            return self.func(args)

def mypool(func, tasks, nworkers=0, maxworkers=31):
    if nworkers == 0:
        nworkers = min(len(tasks), maxworkers)

    # https://stackoverflow.com/questions/62186218/python-multiprocessing-attributeerror-cant-pickle-local-object
    # if isinstance(tasks[0], tuple):
    #     f = Unpack(func)
    # else:
    #     f = func

    pool = schwimmbad.MultiPool(processes=nworkers+1)
    data = pool.map(Unpack(func), tasks)
    pool.close()

    return data
