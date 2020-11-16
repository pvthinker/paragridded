"""
module to vertically interpolate
"""

import numpy as np
from numba import jit
from scipy.interpolate import interp1d
import sys


def lagrange_poly_raw(z, k0, k1, ztarget, coef):
    i = 0
    coef[:] = 1.
    for k in range(k0, k1):
        for l in range(k0, k1):
            if l != k:
                coef[i] *= (ztarget-z[l])/(z[k]-z[l])
        i += 1


def lag_poly_raw(z, k0, k1, ztarget, phi_in):
    res = 0.
    for k in range(k0, k1):
        coef = 1.
        for l in range(k0, k1):
            if l != k:
                coef *= (ztarget-z[l])/(z[k]-z[l])

        res += coef*phi_in[k]
    return res


def lag_poly_raw_trial(z, k0, k1, ztarget, phi_in):
    res = 0.
    for k in range(k0, k1):
        p = np.poly1d([1])
        for l in range(k0, k1):
            if l != k:
                d = np.poly1d([1, -z[l]])
                p *= d/(z[k]-z[l])

        res += np.polyval(p, ztarget)*phi_in[k]
    return res


def vinterp1d(phi_in, phi_out, z_in, z_out, order, scipy=False, missing=np.nan, new=False):

    if scipy:
        f = interp1d(z_in, phi_in, kind="cubic", bounds_error=False)
        phi_out = f(z_out)
    else:
        nin = len(phi_in)
        nout = len(phi_out)

        # k0s = [0]*nout
        # kout = 0
        # k0 = -1
        # if (z_out[kout]<z_in[0]):
        #     k0s[0] = None
        #     kout += 1

        # for kin in range(nin-1):
        #     if (z_out[kout]>=z_in[kin]) and (z_out[kout]<z_in[kin+1]):
        #         k0s[kout] = kin
        #         kout += 1
        #     if kout == nout:
        #         break

        # if (kout<nout) and (z_out[kout]>z_in[-1]):
        #     k0s[-1] = None

        if not(new):
            coef = np.zeros((order,))
        kref = 0
        for kout in range(nout):
            cont = True
            kr = kref
            while cont:
                if (z_out[kout] < z_in[kr]):
                    k0 = None
                    cont = False
#                elif (z_out[kout]>=z_in[kr]) and (z_out[kout]<z_in[kr+1]):
                elif (z_out[kout] < z_in[kr+1]):
                    k0 = kref = kr
                    cont = False
                elif kr == nin-1:
                    k0 = None
                    cont = False
                else:
                    kr += 1

            # k0=k0s[kout]
            if k0 is None:  # (z_out[kout]<z_in[0]) or (z_out[kout]>z_in[-1]):
                phi_out[kout] = missing
            else:
                #            k0 = np.argmin(z_in<z_out[kout])
                #            print(k0)
                if (k0 == 0) or (k0 == nin-2):
                    o = 2  # force linear interpolation
                else:
                    o = order
                dk = (o//2)
                #ks = np.arange(k0-dk,k0+dk)
                #print(k0, dk, o, ks)
                k1, k2 = k0-dk, k0+dk
                if new:
                    phi_out[kout] = lag_poly(z_in, k1, k2, z_out[kout], phi_in)
                else:
                    lagrange_poly(z_in, k1, k2, z_out[kout], coef)
                    #            phi_out[kout] = np.sum(coef*phi_in[ks])
                    res = 0.
                    for i, k in enumerate(range(k1, k2)):
                        res += coef[i]*phi_in[k]
                    phi_out[kout] = res


def vinterp2d_raw(phi_in, phi_out, z_in, z_out, zmin, zmax, order, missing):

    nin = phi_in.shape[1]
    nout = phi_out.shape[1]
    nx = phi_in.shape[0]

    kref = np.zeros((nx,), dtype=int)

    for kout in range(nout):
        for i in range(nx):
            cont = True
            kr = kref[i]
            while cont:
                cont = False
                if (z_out[kout] < zmin[i]):
                    # outside
                    phi_out[i, kout] = missing

                elif (z_out[kout] < z_in[i, kr]):
                    # linear extrapolation
                    alpha = (zmin[i]-z_in[i, kr])/(z_in[i, kr]-z_in[i, kr+1])
                    phi_out[i, kout] = phi_in[i, 0]+alpha * \
                        (phi_in[i, kr]-phi_in[i, kr+1])

                elif (z_out[kout] < z_in[i, kr+1]):
                    # the linear interpolation could be replaced
                    # with a parabolic interpolation with
                    #
                    # lag_poly(z_in[i], max(kr-1, 0), min(kr+1, nin-1), z_out[kout], phi_in[i])
                    #
                    if (kr == 0) or (kr == nin-2):
                        # linear interpolation
                        phi_out[i, kout] = lag_poly(
                            z_in[i], kr, kr, z_out[kout], phi_in[i])
                    else:
                        # cubic interpolation
                        phi_out[i, kout] = lag_poly(
                            z_in[i], kr-1, kr+1, z_out[kout], phi_in[i])

                    kref[i] = kr

                elif kr == nin-1:
                    if (z_out[kout] <= zmax[i]):
                        # linear extrapolation
                        alpha = (zmax[i]-z_in[i, -1])/(z_in[i, -1]-z_in[i, -2])
                        phi_out[i, kout] = phi_in[i, -1] + \
                            alpha*(phi_in[i, -1]-phi_in[i, -2])
                    else:
                        # outside
                        phi_out[i, kout] = missing

                else:
                    kr += 1
                    cont = True


def vinterp3d(phi_in, phi_out, z_in, z_out, order,
              method=0, zmin=0, zmax=0, **kwargs):

    assert phi_in.ndim == 3
    assert phi_out.ndim == 3
    nz, ny, nx = phi_in.shape
    shape_out = phi_out.shape
    assert (shape_out[1] == ny) and (shape_out[2] == nx)

    p_in = np.transpose(phi_in, [1, 2, 0])
    z_i = np.transpose(z_in, [1, 2, 0])
    p_out = np.zeros((ny, nx, shape_out[0]))

    missing = 999.
    if "missing" in kwargs.keys():
        missing = kwargs.pop("missing")
    if method == 0:
        for idx in np.ndindex(ny, nx):
            vinterp1d(p_in[idx], p_out[idx], z_i[idx],
                      z_out, order, kwargs, missing=missing)

    elif method == 1:
        #kref = np.zeros((nx,), dtype=int)
        for idx in range(ny):
            vinterp2d(p_in[idx], p_out[idx], z_i[idx],
                      z_out, zmin, zmax, order, missing)

    elif method == 2:
        nout = len(z_out)
        p_in.shape = (nx*ny, nz)
        p_out.shape = (nx*ny, nout)
        z_i.shape = (nx*ny, nz)
        kref = np.zeros((nx*ny,), dtype=int)
        if isinstance(zmin, float):
            zmin = np.zeros((nx*ny,))+zmin
        else:
            zmin.shape = (nx*ny,)
        if isinstance(zmax, float):
            zmax = np.zeros((nx*ny,))+zmax
        else:
            zmax.shape = (nx*ny,)
        vinterp2d(p_in, p_out, z_i, z_out, zmin, zmax, order, missing)
        p_out.shape = (ny, nx, nout)

    phi_out.flat = np.transpose(p_out, [2, 0, 1])


lagrange_poly = jit(lagrange_poly_raw)
lag_poly = jit(lag_poly_raw)
vinterp2d = jit(vinterp2d_raw)


def Vinterp3d(grid, phi_in, z_in, z_out):
    # TODO: get the staggering of phi_in

    zmin = -grid.depth
    zmax = 0.
    shape = (z_out.shape[0],) + phi_in.shape[-2:]
    phi_out = np.zeros(shape)
    vinterp3d(phi_in, phi_out, z_in, z_out, 4,
              zmin=zmin, zmax=zmax, method=2)
    return phi_out


# if __name__ == "__main__":
#     from R_tools_fort import sigma_to_z_intr_sfc

#     nz = 100
#     dz = 10./nz
#     z_in = (np.arange(nz)+0.5)*dz
#     z_out = np.asarray([-2.23, 3.25, 4.75, 6.78])

#     def f(x):
#         return x**3

#     phi_in = f(z_in)
#     phi_out = np.zeros_like(z_out)
#     vinterp1d(phi_in, phi_out, z_in, z_out, 4)
#     print("theorique:")
#     print(f(z_out))
#     print("numerique:")
#     print(phi_out)
#     print("error:")
#     print(phi_out-f(z_out))

#     ny, nx = 140, 105
#     #ny, nx = 5, 5
#     nz = len(z_in)
#     zi = z_in[:, np.newaxis, np.newaxis]*np.ones((nz, ny, nx))
#     pi = f(zi)
#     po = np.zeros((len(z_out), ny, nx))

#     vinterp3d(pi, po, zi, z_out, 4, method=0)

#     nbope = nx*ny*nz*len(z_out)*100

#     # sys.exit()
#     lm = nx
#     mm = ny
#     n = len(z_in)
#     nz = len(z_out)
#     z_r = np.zeros((lm + 2, mm + 2, n))
#     z_w = np.zeros((lm + 2, mm + 2, n+1))
#     z_lev = np.zeros((lm + 2, mm + 2, nz))
#     rmask = np.ones((lm + 2, mm + 2))
#     imin = 0
#     jmin = 0
#     kmin = 1
#     for k in range(n):
#         z_r[:, :, k] = (k+0.5)*dz
#     for k in range(n+1):
#         z_w[:, :, k] = k*dz

#     var = f(z_r)
#     for k in range(nz):
#         z_lev[:, :, k] = z_out[k]

#     fillvalue = 999.

#     var_zlv = sigma_to_z_intr_sfc(
#         z_r, z_w, rmask, var, z_lev, imin, jmin, kmin, fillvalue)

#     # perfs

#     # >>> %timeit vinterp3d(pi, po, zi, z_out, 4)
#     # 1.03 s ± 46.5 ms per loop (mean ± std. dev. of 7 runs, 1 loop each)

#     # >>> %timeit var_zlv = sigma_to_z_intr_sfc(z_r,z_w,rmask,var,z_lev,imin,jmin,kmin, fillvalue)
#     # 29.6 ms ± 313 µs per loop (mean ± std. dev. of 7 runs, 10 loops each)

#     # >>> %timeit vinterp3d(pi, po, zi, z_out, 4, method=2)
#     # 4.99 ms ± 90.8 µs per loop (mean ± std. dev. of 7 runs, 100 loops each)
