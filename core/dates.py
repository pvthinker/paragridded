import numpy as np
import datetime as dt

day = dt.timedelta(days=1)
hour = dt.timedelta(hours=1)

d0 = dt.datetime(2008, 9, 26, 3)
d1 = d0 + 2*day-5*hour

    

def daterange(d0, d1, delta):
    """ Datetime list from `d0` to `d1` with increment `delta`    

    Parameters
    ----------
    d0, d1 : datetime
    delta : timedelta

    Returns
    -------
    a list of datetime
    """
    if not isinstance(d0, dt.datetime):
        try:
            t0 = dt.datetime.fromisoformat(d0)
        except:
            raise ValueError
    else:
        t0 = d0
    if not isinstance(d1, dt.datetime):
        try:
            t1 = dt.datetime.fromisoformat(d1)
        except:
            raise ValueError
    else:
        t1 = d1
        
    n = int((t1-t0).total_seconds() / delta.total_seconds())
    return [t0+delta*k for k in range(n)]

if __name__ == "__main__":
    t = list(daterange(d0, d0+20*day, day))
    x = np.asarray(range(len(t)))*5
    plt.clf()
    plt.plot(t, x)
    plt.gcf().autofmt_xdate()

