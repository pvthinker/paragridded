! gfortran -fPIC -shared -O4 -march=native vinterp.f90 -olibvinterp.so
function linear_onepoint(z, phi, zout, k0, n)
  implicit none

  real*8:: linear_onepoint, zout
  real*8, dimension(n):: z, phi
  integer:: n, k0

  integer:: k1
  real*8:: z01
  real*8:: dz0, dz1

  k1 = k0+1

  z01 = z(k1)-z(k0)

  dz0 = zout-z(k0)
  dz1 = zout-z(k1)
  
  linear_onepoint = (-phi(k0)*dz1+phi(k1)*dz0)/z01  
  
end function linear_onepoint

function cubic_onepoint(z, phi, zout, k0, n)
  implicit none

  real*8:: cubic_onepoint, zout
  real*8, dimension(n):: z, phi
  integer:: n, k0

  integer:: k1, k2, k3
  real*8:: z01, z02, z03, z12, z13, z23  
  real*8:: dz0, dz1, dz2, dz3
  real*8:: den
  real*8:: cff0, cff1, cff2, cff3  

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
  
  den = z01*z02*z03
  cff0 = dz1*dz2*dz3/den

  den = z01*z12*z13
  cff1 = dz0*dz2*dz3/den
  
  den = z02*z12*z23
  cff2 = dz0*dz1*dz3/den
  
  den = z03*z13*z23
  cff3 = dz0*dz1*dz2/den
  
  cubic_onepoint = -phi(k0)*cff0+phi(k1)*cff1-phi(k2)*cff2+phi(k2)*cff3
  
end function cubic_onepoint

subroutine vinterp1d_slower(z, phi, zout, phiout, n, nout, missing)
  implicit none

  integer:: n, nout
  real*8, dimension(n):: z, phi
  real*8, dimension(nout):: zout, phiout
  real*8:: missing

  integer:: kref, kout, kr, k0
  integer, dimension(nout) :: k0all
  real*8:: ztarget, linear_onepoint, cubic_onepoint
  logical:: cont

  kref = 1  
  do kout = 1, nout
     cont = .true.
     kr = kref
     ztarget = zout(kout)
     
     ! determine k0
     do while (cont)
        if (ztarget.lt.z(kr)) then
           k0all(kout) = -1
           cont = .false.
!!$           phiout(kout) = missing
        elseif (ztarget.lt.z(kr+1)) then
           k0all(kout) = kr
           kref = kr
           cont = .false.
!!$           if ((kr.eq.1).or.(kr.eq.(n-2))) then
!!$              phiout(kout) = linear_onepoint(z, phi, ztarget, kr, n)
!!$           else
!!$              phiout(kout) = cubic_onepoint(z, phi, ztarget, kr-1, n)
!!$           endif
        elseif (kr.eq.n) then
           k0all(kout) = -1
           cont = .false.
!           phiout(kout) = missing
        else
           kr = kr + 1
!           cont = .true.
        endif        
     enddo
  enddo
  do kout = 1, nout
     k0 = k0all(kout)
     ! compute the interpolated value using k0
     if (k0.eq.-1) then
        ! extrapolation
        phiout(kout) = missing
        
     elseif ((k0.eq.1).or.(k0.eq.(n-2))) then
        ! linear interpolation
        phiout(kout) = linear_onepoint(z, phi, ztarget, k0, n)
        
     else
        ! cubic interpolation
        phiout(kout) = cubic_onepoint(z, phi, ztarget, k0-1, n)
        
     endif
  enddo 
  
end subroutine vinterp1d_slower

subroutine vinterp1d(z, phi, zout, phiout, n, nout, missing)
  implicit none

  integer:: n, nout
  real*8, dimension(n):: z, phi
  real*8, dimension(nout):: zout, phiout
  real*8:: missing

  integer:: kout, kr, k0
  real*8:: ztarget, linear_onepoint, cubic_onepoint
  logical:: cont

  kr = 1  
  do kout = 1, nout
     cont = .true.
     ztarget = zout(kout)
     
     ! determine k0
     do while (cont)
        cont = .false.
        if (ztarget.lt.z(kr)) then
           k0 = -1
        elseif (ztarget.lt.z(kr+1)) then
           k0 = kr
        elseif (kr.eq.n) then
           k0 = -1
        else
           kr = kr + 1
           cont = .true.
        endif        
     enddo
     
     ! compute the interpolated value using k0
     if (k0.eq.-1) then
        phiout(kout) = missing      
     elseif ((k0.eq.1).or.(k0.eq.(n-2))) then
        phiout(kout) = linear_onepoint(z, phi, ztarget, k0, n)        
     else
        phiout(kout) = cubic_onepoint(z, phi, ztarget, k0-1, n)        
     endif
  enddo 
  
end subroutine vinterp1d

subroutine vinterp2d(z, phi, zout, phiout, nidx, n, nout, missing)
  implicit none

  integer:: nidx, n, nout
  real*8, dimension(n, nidx):: z, phi
  real*8, dimension(nout, nidx):: zout, phiout
  real*8:: missing

  integer,dimension(nidx):: kref
  integer:: kr, i, kout
  real*8:: ztarget, linear_onepoint, cubic_onepoint
  logical:: cont

  kref(:) = 1  
  do kout = 1, nout
     do i = 1, nidx
        kr = kref(i)
        ztarget = zout(kout, i)
        !write(*,*) kout, i, kr
        cont = .true.
        do while (cont)
           cont = .false.
           if (ztarget.lt.z(kr, i)) then
              phiout(kout, i) = missing
           elseif (ztarget.lt.z(kr+1, i)) then
              if ((kr.eq.1).or.(kr.eq.n-1)) then
                 phiout(kout, i) = linear_onepoint(z(1, i), phi(1, i), ztarget, kr, n)
              else
                 phiout(kout, i) = cubic_onepoint(z(1, i), phi(1, i), ztarget, kr-1, n)
              endif
           elseif (kr.eq.n) then
              phiout(kout, i) = missing
           else
              kr = kr + 1
              cont = .true.
           endif
        enddo
        kref(i) = kr
     enddo
  enddo
  
end subroutine vinterp2d

subroutine vinterp2d_basic(z, phi, zout, phiout, nidx, n, nout, missing)
  implicit none

  integer:: nidx, n, nout
  real*8, dimension(n, nidx):: z, phi
  real*8, dimension(nout, nidx):: zout, phiout
  real*8:: missing

  integer:: k

  do k = 1, nidx
     call vinterp1d(z(1,k), phi(1,k), zout(1,k), phiout(1,k), n, nout, missing)
  enddo

end subroutine vinterp2d_basic
