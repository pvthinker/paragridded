from ctypes import cdll, c_double, byref
from carrays import CArray
import numpy as np
from ptr import ptr
from ctypes import POINTER, c_void_p, c_int, c_char, c_float, c_double, c_int8, c_int32, byref, cdll

libfortran = cdll.LoadLibrary("../diags/libcroco.so")

missing = np.asarray(9e99, dtype="f")
#missing_ = byref(c_double(missing))

ptrf = POINTER(c_float)


def vinterp1d(z, phi, zout, phiout):
    nz_, = z.shapeptr
    nout_, = zout.shapeptr

    z_ = z.ptr
    phi_ = phi.ptr
    zout_ = zout.ptr
    phiout_ = phiout.ptr

    libfortran.vinterp1d_(z_, phi_, zout_, phiout_, nz_, nout_, missing_)


def vinterp2d(z, phi, zout, phiout):
    nidx_, nz_ = z.shapeptr
    _, nout_ = zout.shapeptr

    z_ = z.ptr
    phi_ = phi.ptr
    zout_ = zout.ptr
    phiout_ = phiout.ptr

    libfortran.vinterp2d_basic_(
        z_, phi_, zout_, phiout_, nidx_, nz_, nout_, missing_)


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


def vinterp3d_at_z(eta, h, hc, sigma, cs, phi, zout, phiout, loc):
    nz, ny, nx = phi.shape
    nidx = ny*nx
    nout = zout.shape[0]

    # loc = 0 # rho-point
    # loc = 1 # u-point
    # loc = 2 # v-point
    # loc = 3 # f-point

    # 8% speed up if these two arrays are preallocated
    phioutT = np.zeros((ny, nx, nout), dtype=phi.dtype)
    phiT = np.zeros((ny, nx, nz), dtype=phi.dtype)

    phiT[:] = np.transpose(phi, [1, 2, 0])

    libfortran.zinterp3d_(ptr(eta), ptr(h),
                          ptr(hc), ptr(sigma), ptr(cs),
                          ptr(phiT), ptr(zout), ptr(phioutT),
                          ptr(nx), ptr(ny), ptr(nz), ptr(nout), ptr(missing), ptr(loc))

    phiout[:] = np.transpose(phioutT, [2, 0, 1])


def test_1():
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
    z[:, :] = z1d[np.newaxis, :]
    phi.flat = f(z)

    zout1d = np.asarray([0.2, 0.5, 2.8, 3.05])
    zout[:, :] = zout1d[np.newaxis, :]

    vinterp2d(z, phi, zout, phiout)

# using the Fortran compiled vinterp2d_basic function
# In [6]: %timeit vinterp2d(z, phi, zout, phiout)
# 2.89 ms ± 64.8 µs per loop (mean ± std. dev. of 7 runs, 100 loops each)


if __name__ == "__main__":
    import vert_coord as vc
    import matplotlib.pyplot as plt

    plt.ion()

    dtype = "f"

    nz, ny, nx = 100, 140, 105
    nout = 4
    zout = np.zeros((nout,), dtype=dtype)
    zout[:] = [-2000., -1000, -500, -200]
    #zout[:] = -1000.
    # zout=np.linspace(-220,-180,41)
    nout = len(zout)
    hc = np.asarray(300., dtype=dtype)

    zeta = np.zeros((ny, nx), dtype=dtype)
    h = np.zeros((ny, nx), dtype=dtype)

    sigma = -1+(np.arange(nz, dtype=dtype)+0.5)/nz
    N, hmin, Tcline, theta_s, theta_b = vc.gigatl()

    hc, Cs_w, Cs_r = vc.set_scoord(N, hmin, Tcline, theta_s, theta_b)

    hc = np.asarray(hc, dtype=dtype)
    cs = np.asarray(Cs_r, dtype=dtype)

    h[:] = 5000.
    zr = vc.sigma2z(sigma, cs, zeta[0, 0], h[0, 0], hc)

    phi = np.zeros((nz, ny, nx), dtype=dtype)
    for k in range(nz):
        phi[k] = zr[k]

    phioutT = np.zeros((ny, nx, nout), dtype=phi.dtype)
    phiT = np.zeros((ny, nx, nz), dtype=phi.dtype)
    phiout = np.zeros((nout, ny, nx), dtype=phi.dtype)
    vinterp3d_at_z(zeta, h, hc, sigma, cs, phi, zout, phiout)
