import numpy as np
from ctypes import cdll, c_double, c_float, c_int, byref
from carrays import CArray

libfortran = cdll.LoadLibrary("../diags/libcroco.so")


def zlevs_old(h, zeta, hc, Cs_r, Cs_w, z_r, z_w):
    Mm_, Lm_ = zeta.shapeptr
    N_, = Cs_r.shapeptr

    h_ = h.ptr
    zeta_ = zeta.ptr
    hc_ = byref(c_double(hc))
    Cs_r_ = Cs_r.ptr
    Cs_w_ = Cs_w.ptr
    z_r_ = z_r.ptr
    z_w_ = z_w.ptr

    libfortran.zlevs_(Lm_, Mm_, N_,
                      h_, zeta_,
                      hc_, Cs_r_, Cs_w_, z_r_, z_w_)


def zlevs(h, zeta, hc, Cs_r, Cs_w, z_r, z_w):
    N_, Mm_, Lm_ = z_r.shapeptr

    h_ = h.ptr
    zeta_ = zeta.ptr
    hc_ = byref(c_double(hc))
    Cs_r_ = Cs_r.ptr
    Cs_w_ = Cs_w.ptr
    z_r_ = z_r.ptr
    z_w_ = z_w.ptr

    libfortran.zlevs_croco_new_(Lm_, Mm_, N_,
                                h_, zeta_,
                                hc_, Cs_r_, Cs_w_,
                                z_r_, z_w_)


def rho_eos(T, S, z_r, z_w, rho0, rho):
    N_, Mm_, Lm_ = T.shapeptr
    T_ = T.ptr
    S_ = S.ptr
    z_r_ = z_r.ptr
    z_w_ = z_w.ptr
    rho0_ = byref(c_double(rho0))
    rho_ = rho.ptr

    libfortran.rho_eos_(Lm_, Mm_, N_,
                        T_, S_, z_r_, z_w_,
                        rho0_, rho_)


if __name__ == "__main__":
    import sys
    import vert_coord

    N, M, L = 100, 140, 105

    h = CArray((M, L))
    hinv = CArray((M, L))
    zeta = CArray((M, L))
    Cs_w = CArray((N+1,))
    Cs_r = CArray((N,))

    # sc_w = CArray((N+1,))
    # sc_r = CArray((N,))

    Cs_w[:] = np.arange(N+1) / N
    Cs_r[:] = (np.arange(N)+0.5)/N

    # sc_w[:] = np.arange(N+1) / N
    # sc_r[:] = (np.arange(N)+0.5)/N

    z_r = CArray((N, M, L))
    z_w = CArray((N+1, M, L))

    h[:] = 2000.

    N, hmin, Tcline, theta_s, theta_b = vert_coord.gigatl()

    hc, cs_w, cs_r = vert_coord.set_scoord(N, hmin, Tcline, theta_s, theta_b)
    Cs_w[:] = cs_w
    Cs_r[:] = cs_r

    #zlevs_old(h, zeta, hc, Cs_r, Cs_w, z_r, z_w)
    zlevs(h, zeta, hc, Cs_r, Cs_w, z_r, z_w)

    T = CArray((N, M, L))
    S = CArray((N, M, L))
    T[:] = 20.
    S[:] = 35.5
    rho = CArray((N, M, L))
    rho0 = 1000.

    rho_eos(T, S, z_r, z_w, rho0, rho)

    if False:
        dir_R_tools = "/home/roullet/dev/python/R_tools"
        sys.path.append(dir_R_tools)
        import R_tools_fort

        T = np.zeros((L, M, N))
        S = np.zeros((L, M, N))
        z_r = np.zeros((L, M, N))
        z_w = np.zeros((L, M, N+1))
        h = np.zeros((L, M))
        zeta = np.zeros((L, M))

        z_r, z_w = R_tools_fort.zlevs(h, zeta, hc, Cs_r, Cs_w)
        rho = R_tools_fort.rho_eos(T, S, z_r, z_w, rho0)
