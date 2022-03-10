!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!! Compute z_r and z_w for new or old S Coord
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!


# define NEW_S_COORD 


      subroutine zlevs_croco_new(Lm,Mm,N, h,zeta, hc, Cs_r, Cs_w,
     &                                      z_r,z_w)

      implicit none

      integer Lm,Mm,N, i,j,k

      real*8 Cs_w(0:N), Cs_r(N), cff_w, cff_r, cff1_w, cff1_r, sigma,
!     &       sc_w(0:N), sc_r(N),
     &       hc, ds, z_w0, z_r0,
     &       zeta(Lm, Mm),
     &       z_r(Lm, Mm,N),z_w(Lm, Mm,0:N),
     &       h(Lm, Mm), cff2(Lm, Mm)! ,hinv(Lm, Mm)   

      ds=1.D0/dble(N)

      do j=1,Mm
         do i=1,Lm

!     #  ifdef NEW_S_COORD 
            !hinv(i,j) = 1./(h(i,j)+hc)      
!     #  else
!     hinv(i,j)=1./h(i,j) 
!     #  endif
            cff2(i,j) = (zeta(i,j)+h(i,j))/(h(i,j)+hc)!*hinv(i,j)
            !z_w(i,j,0) = -h(i,j)

         enddo
      enddo
      do j=1,Mm
         do i=1,Lm

!     #  ifdef NEW_S_COORD 
            !hinv(i,j) = 1./(h(i,j)+hc)      
!     #  else
!     hinv(i,j)=1./h(i,j) 
!     #  endif
!            cff2(i,j) = (zeta(i,j)+h(i,j))/(h(i,j)+hc)!*hinv(i,j)
            z_w(i,j,0) = -h(i,j)

         enddo
      enddo
      do k=1,N
         sigma = -1.d0 +k/(1.d0*N)
         
!     #  ifdef NEW_S_COORD
         cff_w =hc*sigma
!         cff_r =hc*sc_r(k)
         cff1_w=Cs_w(k)
!         cff1_r=Cs_r(k)
!     #  else
!     cff_w =hc*(sc_w(k)-Cs_w(k))
!     cff_r =hc*(sc_r(k)-Cs_r(k))
!     cff1_w=Cs_w(k)
!     cff1_r=Cs_r(k)
!     #  endif           

         do j=1,Mm
            do i=1,Lm

               z_w0=cff_w+cff1_w*h(i,j) 
!               z_r0=cff_r+cff1_r*h(i,j) 

!     #  ifdef NEW_S_COORD
!               z_w(i,j,k)=z_w0*h(i,j)*hinv(i,j)+zeta(i,j)
!     &              *(1.+z_w0*hinv(i,j))
               z_w(i,j,k) = zeta(i,j) + z_w0*cff2(i,j)
!               z_r(i,j,k)=z_r0*h(i,j)*hinv(i,j)+zeta(i,j)
!     &              *(1.+z_r0*hinv(i,j))
!     #  else
!     z_w(i,j,k)=z_w0+zeta(i,j)*(1.+z_w0*hinv(i,j))      
!     z_r(i,j,k)=z_r0+zeta(i,j)*(1.+z_r0*hinv(i,j))
!     #  endif

            enddo
         enddo
      enddo
      do k=1,N
         sigma = -1. +(k-0.5d0)/(1.d0*N)
!     #  ifdef NEW_S_COORD
!         cff_w =hc*sc_w(k)
         cff_r =hc*sigma
!         cff1_w=Cs_w(k)
         cff1_r=Cs_r(k)
!     #  else
!     cff_w =hc*(sc_w(k)-Cs_w(k))
!     cff_r =hc*(sc_r(k)-Cs_r(k))
!     cff1_w=Cs_w(k)
!     cff1_r=Cs_r(k)
!     #  endif           

         do j=1,Mm
            do i=1,Lm

!               z_w0=cff_w+cff1_w*h(i,j) 
               z_r0=cff_r+cff1_r*h(i,j) 

!     #  ifdef NEW_S_COORD
!               z_w(i,j,k)=z_w0*h(i,j)*hinv(i,j)+zeta(i,j)
!     &              *(1.+z_w0*hinv(i,j)) 
!               z_r(i,j,k)=z_r0*h(i,j)*hinv(i,j)+zeta(i,j)
!     &              *(1.+z_r0*hinv(i,j))
               z_r(i,j,k) = zeta(i,j) + z_r0*cff2(i,j)
!     #  else
!     z_w(i,j,k)=z_w0+zeta(i,j)*(1.+z_w0*hinv(i,j))      
!     z_r(i,j,k)=z_r0+zeta(i,j)*(1.+z_r0*hinv(i,j))
!     #  endif

            enddo
         enddo
      enddo
      end


