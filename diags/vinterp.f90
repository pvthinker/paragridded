! gfortran -fPIC -shared -O4 -march=native vinterp.f90 -olibvinterp.so
function linear_onepoint(z, phi, zout, k0, n)
  implicit none

  real:: linear_onepoint, zout
  real, dimension(n):: z, phi
  integer:: n, k0

  integer:: k1
  real:: z01
  real:: dz0, dz1

  k1 = k0+1

  z01 = z(k1)-z(k0)

  dz0 = zout-z(k0)
  dz1 = zout-z(k1)
  
  linear_onepoint = (-phi(k0)*dz1+phi(k1)*dz0)/z01  
  
end function linear_onepoint

function cubic_onepoint(z, phi, zout, k0, n)
  implicit none

  real:: cubic_onepoint, zout
  real, dimension(n):: z, phi
  integer:: n, k0

  integer:: k1, k2, k3
  real:: z01, z02, z03, z12, z13, z23  
  real:: dz0, dz1, dz2, dz3
  real:: den
  real:: cff0, cff1, cff2, cff3  

  k1 = k0+1
  k2 = k0+2
  k3 = k0+3
  
  z01 = z(k1)-z(k0)
  z02 = z(k2)-z(k0)
  z03 = z(k3)-z(k0)
  z12 = z(k2)-z(k1)
  z13 = z(k3)-z(k1)
  z23 = z(k3)-z(k2)

  dz0 = zout-z(k0)
  dz1 = zout-z(k1)
  dz2 = zout-z(k2)
  dz3 = zout-z(k3)
  
  den = -z01*z02*z03
  cff0 = dz1*dz2*dz3/den

  den = z01*z12*z13
  cff1 = dz0*dz2*dz3/den
  
  den = -z02*z12*z23
  cff2 = dz0*dz1*dz3/den
  
  den = z03*z13*z23
  cff3 = dz0*dz1*dz2/den
  
  cubic_onepoint = phi(k0)*cff0+phi(k1)*cff1+phi(k2)*cff2+phi(k3)*cff3
  
end function cubic_onepoint


subroutine vinterp1d(z, phi, zout, phiout, n, nout, missing)
  ! assume z is in INCREASING with its index
  implicit none

  integer:: n, nout
  real, dimension(n):: z, phi
  real, dimension(nout):: zout, phiout
  real:: missing

  integer:: kout, kr, k0, k1
  real:: ztarget, zbottom, ztop, linear_onepoint, cubic_onepoint
  logical:: cont

  kr = 1
  kout = 1
  zbottom = z(kr)
  do while ((zout(kout).lt.zbottom).and.(kout.le.nout))
     phiout(kout) = missing
     kout = kout+1
  end do

  if (kout.gt.nout) return
    
  do while ((kr.lt.n).and.(kout.le.nout))
     ztarget = zout(kout)
     if (ztarget.lt.z(kr+1)) then
        if ((kr.eq.1).or.(kr.eq.(n-1))) then
           phiout(kout) = linear_onepoint(z, phi, ztarget, kr, n)        
        else
           phiout(kout) = cubic_onepoint(z, phi, ztarget, kr-1, n)        
        endif
        kout = kout+1
     else
        kr = kr+1
     endif
  end do

  if (kout.gt.nout) return
  
  do while (kout.le.nout)
     phiout(kout) = missing
     kout = kout + 1
  end do

end subroutine vinterp1d

subroutine vinterp1d_new(z, phi, zout, phiout, n, nout, missing)
  implicit none

  integer:: n, nout
  real, dimension(n):: z, phi
  real, dimension(nout):: zout, phiout
  real:: missing

  integer:: kout, k0
  integer,dimension(1):: kr
  real:: ztarget, ztop, zbottom

  integer:: k1, k2, k3
  real:: z01, z02, z03, z12, z13, z23  
  real:: dz0, dz1, dz2, dz3
  real:: den
  real:: cff0, cff1, cff2, cff3  

  do kout = 1, nout
     ztarget = zout(kout)
     kr = maxloc(z, mask=(z<ztarget),dim=1)
     k0 = kr(1)
     if ((k0.eq.1).or.(k0.eq.(n-1))) then

        ! linear interpolation

        ! a) call a function prevents vectorization
        ! phiout(kout) = linear_onepoint(z, phi, ztarget, k0, n)

        ! b) do the interpolation directly
        k1 = k0+1
        z01 = z(k1)-z(k0)
        dz0 = ztarget-z(k0)
        dz1 = ztarget-z(k1)  
        phiout(kout) = (-phi(k0)*dz1+phi(k1)*dz0)/z01  

     else
        ! cubic interpolation

        ! phiout(kout) = cubic_onepoint(z, phi, ztarget, k0-1, n)        

        k1 = k0+1
        k2 = k0+2
        k3 = k0+3

        z01 = z(k1)-z(k0)
        z02 = z(k2)-z(k0)
        z03 = z(k3)-z(k0)
        z12 = z(k2)-z(k1)
        z13 = z(k3)-z(k1)
        z23 = z(k3)-z(k2)

        dz0 = ztarget-z(k0)
        dz1 = ztarget-z(k1)
        dz2 = ztarget-z(k2)
        dz3 = ztarget-z(k3)

        den = z01*z02*z03
        cff0 = dz1*dz2*dz3/den

        den = z01*z12*z13
        cff1 = dz0*dz2*dz3/den

        den = z02*z12*z23
        cff2 = dz0*dz1*dz3/den

        den = z03*z13*z23
        cff3 = dz0*dz1*dz2/den

        phiout(kout) = -phi(k0)*cff0+phi(k1)*cff1-phi(k2)*cff2+phi(k2)*cff3

     endif
  end do
!  do while (kout.le.nout)
!     phiout(kout) = missing
!     kout = kout + 1
!  end do

  
end subroutine vinterp1d_new


subroutine vinterp2d(z, phi, zout, phiout, nidx, n, nout, missing)
  implicit none

  integer:: nidx, n, nout
  real, dimension(n, nidx):: z, phi
  real, dimension(nout, nidx):: zout, phiout
  real:: missing

  integer:: k

  do k = 1, nidx
     call vinterp1d(z(1,k), phi(1,k), zout(1,k), phiout(1,k), n, nout, missing)
  enddo

end subroutine vinterp2d

subroutine zinterp2d(eta, h, hc, sigma, cs, phi, zout, phiout, nidx, nz, nout, missing)
  ! same as vinterp2d but replace first argument
  !
  !          (z, ...) -> (eta, h, hc, sigma, cs, ...)
  !
  ! so that z in computed on the fly, during the interpolation

  implicit none

  integer:: nidx, nz, nout
  real, dimension(nz, nidx):: phi
  real, dimension(nout):: zout
  real, dimension(nout, nidx):: phiout
  real, dimension(nidx):: eta, h
  real, dimension(nz):: sigma, cs, z
  real, dimension(nz):: p
  real, dimension(nout):: po
  real:: hc, missing
  real:: ztop, depth, cff2

  integer:: i, k

  do i = 1, nidx
     ztop = eta(i)
     depth = h(i)
     cff2 = (ztop+depth)/(depth+hc)
     do k = 1, nz
        z(k) = ztop  + (hc*sigma(k)+cs(k)*depth)*cff2
     enddo
    
     call vinterp1d(z, phi(1,i), zout, phiout(1,i), nz, nout, missing)

  enddo

end subroutine zinterp2d

subroutine zinterp3d(eta, h, hc, sigma, cs, phi, zout, phiout, nx, ny, nz, nout, missing, loc)

  implicit none

  integer:: nx, ny, nz, nout, loc
  real, dimension(nz, nx, ny):: phi
  real, dimension(nout):: zout
  real, dimension(nout, nx, ny):: phiout
  real, dimension(nx, ny):: eta, h
  real, dimension(nz):: sigma, cs, z
  real, dimension(nz):: p
  real, dimension(nout):: po
  real:: hc, missing
  real:: ztop, depth, cff2

  integer:: i, j, k
  integer:: i1, j1

  
  do j = 1, ny
     j1 = min(j+1, nx)
     
     do i = 1, nx
        
        if (loc.eq.0) then ! rho point
           ztop = eta(i,j)
           depth = h(i,j)
           
        elseif (loc.eq.1) then ! u-point
           i1 = min(i+1, nx)
           ztop = (eta(i,j)+eta(i1,j))/2
           depth = (h(i,j)+h(i1,j))/2
           
        elseif (loc.eq.2) then ! v-point
           ztop = (eta(i,j)+eta(i,j1))/2
           depth = (h(i,j)+h(i,j1))/2
           
        elseif (loc.eq.3) then ! f-point
           i1 = min(i+1, nx)
           ztop = (eta(i,j)+eta(i,j1)+eta(i1,j)+eta(i1,j1))/4
           depth = (h(i,j)+h(i,j1)+h(i1,j)+h(i1,j1))/4
           
        endif
           
        cff2 = (ztop+depth)/(depth+hc)
        do k = 1, nz
           z(k) = ztop  + (hc*sigma(k)+cs(k)*depth)*cff2
        enddo

        call vinterp1d(z, phi(1,i,j), zout, phiout(1,i,j), nz, nout, missing)

     enddo
  enddo

     
end subroutine zinterp3d
