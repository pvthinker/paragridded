from ctypes import cdll, c_double, byref
from carrays import CArray
import numpy as np

libfortran = cdll.LoadLibrary("../diags/libcroco.so")

missing = 9e99
missing_ = byref(c_double(missing))


def vinterp1d(z, phi, zout, phiout):
    nz_, = z.shapeptr
    nout_, = zout.shapeptr

    z_ = z.ptr
    phi_ = phi.ptr
    zout_ = zout.ptr
    phiout_ = phiout.ptr

    libfortran.vinterp1d_(z_, phi_, zout_, phiout_, nz_, nout_, missing_)

def vinterp2d(z, phi, zout, phiout):
    nidx_, nz_  = z.shapeptr
    _, nout_ = zout.shapeptr

    z_ = z.ptr
    phi_ = phi.ptr
    zout_ = zout.ptr
    phiout_ = phiout.ptr

    libfortran.vinterp2d_basic_(z_, phi_, zout_, phiout_, nidx_, nz_, nout_, missing_)

def vinterp3d(z, phi, zout):
    nz, ny, nx = phi.shape
    nout = zout.shape[0]

    nidx = nx*ny

    z2 = CArray((nidx, nz))
    p2 = CArray((nidx, nz))
    zout2 = CArray((nidx, nout))
    pout2 = CArray((nidx, nout))

    z2.shape = (ny, nx, nz)
    p2.shape = (ny, nx, nz)
    zout2.shape = (ny, nx, nout)
    z2[:] = np.transpose(z, [1, 2, 0])
    p2[:] = np.transpose(phi, [1, 2, 0])
    zout2[:] = np.transpose(zout, [1, 2, 0])

    vinterp2d(z2, p2, zout2, pout2)

    pout2.shape = (ny, nx, nout)
    phiout = CArray((nout, ny, nx))
    phiout[:] = np.transpose(pout2, [2, 0, 1])
    return phiout
    
def test1d():
    nz = 100
    nout = 3
    z = CArray((nz,))
    phi = CArray((nz,))
    zout = CArray((nout,))
    phiout = CArray((nout,))
    
    def f(x):
        return np.sin(x)
    
    z.flat = np.arange(nz)*2*np.pi/nz
    phi.flat = f(z)

    zout.flat = [0.2, 0.5, 1., 2.]

    vinterp1d(z, phi, zout, phiout)
    for k in range(nout):
        zo = zout[k]
        po = phiout[k]
        ze = f(zo)
        print(f"zout={zo:.3} po={po:.3} exact={ze:.3}")

    plt.clf()
    plt.plot(z, phi, "+-")
    plt.plot(zout, phiout, "o")
    
if __name__ == "__main__":
    import matplotlib.pyplot as plt

    plt.ion()

    N = 140*105
    nz = 100
    nout = 4
    z = CArray((N, nz))
    phi = CArray((N, nz))
    zout = CArray((N, nout))
    phiout = CArray((N, nout))
    
    def f(x):
        return np.sin(x)

    z1d = np.arange(nz)*2*np.pi/nz
    z[:,:] =  z1d[np.newaxis, :]
    phi.flat = f(z)

    zout1d = np.asarray([0.2, 0.5, 2.8, 3.05])
    zout[:,:] =  zout1d[np.newaxis, :]

    vinterp2d(z, phi, zout, phiout)

# using the Fortran compiled vinterp2d_basic function
# In [6]: %timeit vinterp2d(z, phi, zout, phiout)                                 
# 2.89 ms ± 64.8 µs per loop (mean ± std. dev. of 7 runs, 100 loops each)
