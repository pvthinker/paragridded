import numpy as np

class color:
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    DARKCYAN = '\033[36m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLACK = "\033[0;30m"
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

def set_char(value, col):
    if value < chunk:
        c = str(value)
    else:
        c = "\u2588"
    return col+c+color.END

def print_summary(status, chunk, nchunks):
    line = " "*4+"".join([f"{k:<5}" for k in range(0, nchunks, chunk)])
    print(line)
    for k in range(13):
        line = f"{k+1:2}: "
        for l in range(nchunks):
            if status[k, 0, l] > 0:
                c = set_char(status[k, 0, l], color.BLACK)
            elif status[k, 1, l] > 0:
                c = set_char(status[k, 1, l], color.RED)
            else:
                c = set_char(status[k, 2, l], color.BLUE+color.BOLD)
            line += c
        print(line)

def analyze_filestatus(ds, dates):
    ndates = len(dates)
    chunk = 5
    nchunks = int(np.ceil(ndates/chunk))
    #dates = list(range(ndates))
    status = np.zeros((13, 3, chunk*nchunks), dtype="b")

    for s in range(13): 
        r = ds.readers[s+1] 
        for k,d in enumerate(dates): 
            if d not in r.dates: 
                status[s,0,k] = 1 
            elif r.filestatus[d] == "lost": 
                status[s,1,k] = 1 
            elif r.filestatus[d] == "online": 
                status[s,2,k] = 1 


    status.shape = (13, 3, nchunks, chunk)
    status = status.sum(axis=-1)

    return (status, chunk, nchunks)

if __name__ == "__main__":
    import bindatasets as bd

    ds = bd.Dataset()

    dates = ds.readers[13].dates
    status, chunk, nchunks = analyze_filestatus(ds, dates)
    print_summary(status, chunk, nchunks)
    
