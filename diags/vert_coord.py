import numpy as np


NEW_S_COORD = True


def set_scoord(N, hmin, Tcline, theta_s, theta_b):
    if NEW_S_COORD:

        def sigma_to_cs(sigma):
            if(theta_s > 0.):
                csrf = (1.-np.cosh(theta_s*sigma))/(np.cosh(theta_s)-1.)
            else:
                csrf = -sigma**2
            if (theta_b > 0.):
                cs = (np.exp(theta_b*csrf)-1.)/(1.-np.exp(-theta_b))
            else:
                cs = csrf
            return cs

        s2cs = np.vectorize(sigma_to_cs)

        hc = min(hmin, Tcline)
        cff1 = 1./np.sinh(theta_s)
        cff2 = 0.5/np.tanh(0.5*theta_s)

        sc_w = -1. + np.arange(N+1)/N
        sc_r = -1. + (np.arange(N)+0.5)/N
        Cs_w = s2cs(sc_w)
        Cs_r = s2cs(sc_r)

    else:
        raise ValueError("scoord implemented only for NEW_S_COORD")

    return (hc, Cs_w, Cs_r)


def gigatl():
    # GIGATL
    N = 100
    hmin = 1000
    Tcline = 300.
    theta_s = 5.
    theta_b = 2.
    return (N, hmin, Tcline, theta_s, theta_b)


def sigma2z(sigma, Cs, zeta, h, hc):
    cff2 = (zeta+h)/(h+hc)
    z = zeta + (hc*sigma+Cs*h)*cff2
    return z


if __name__ == "__main__":
    N, hmin, Tcline, theta_s, theta_b = gigatl()

    hc, Cs_w, Cs_r = set_scoord(N, hmin, Tcline, theta_s, theta_b)
