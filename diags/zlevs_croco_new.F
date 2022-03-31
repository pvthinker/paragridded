!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!! Compute z_r and z_w for new or old S Coord
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!


# define NEW_S_COORD 


      subroutine zlevs_croco_new(Lm,Mm,N, h,zeta, hc, Cs_r, Cs_w,
     &                                      z_r,z_w)
! compute z_r AND z_w

      implicit none

      integer Lm,Mm,N, i,j,k

      real*8 Cs_w(0:N), Cs_r(N), cff_w, cff_r, cff1_w, cff1_r, sigma,
     &       hc, ds, z_w0, z_r0,
     &       zeta(Lm, Mm),
     &       z_r(Lm, Mm,N),z_w(Lm, Mm,0:N),
     &       h(Lm, Mm), cff2(Lm, Mm)

      ds=1.D0/dble(N)

      do j=1,Mm
         do i=1,Lm

            cff2(i,j) = (zeta(i,j)+h(i,j))/(h(i,j)+hc)

         enddo
      enddo
      do j=1,Mm
         do i=1,Lm

            z_w(i,j,0) = -h(i,j)

         enddo
      enddo
      do k=1,N
         sigma = -1.d0 +k/(1.d0*N)
         
         cff_w =hc*sigma
         cff1_w=Cs_w(k)

         do j=1,Mm
            do i=1,Lm

               z_w0=cff_w+cff1_w*h(i,j) 
               z_w(i,j,k) = zeta(i,j) + z_w0*cff2(i,j)

            enddo
         enddo
      enddo
      do k=1,N
         sigma = -1. +(k-0.5d0)/(1.d0*N)
         cff_r =hc*sigma
         cff1_r=Cs_r(k)

         do j=1,Mm
            do i=1,Lm

               z_r0=cff_r+cff1_r*h(i,j) 

               z_r(i,j,k) = zeta(i,j) + z_r0*cff2(i,j)

            enddo
         enddo
      enddo
      end


      subroutine zrs_croco_new(Lm,Mm,N, h,zeta, hc, Cs_r, z_r)
! compute only z_r

      implicit none

      integer Lm,Mm,N, i,j,k

      real Cs_r(N), cff_w, cff_r,  cff1_r, sigma,
     &       hc, ds, z_r0,
     &       zeta(Lm, Mm),
     &       z_r(Lm, Mm,N),
     &       h(Lm, Mm), cff2(Lm, Mm)

      ds=1.0/N!1.D0/dble(N)

      do j=1,Mm
         do i=1,Lm

            cff2(i,j) = (zeta(i,j)+h(i,j))/(h(i,j)+hc)

         enddo
      enddo
      do k=1,N
         sigma = -1. +(k-0.5)*ds!/(1.d0*N)
         cff_r =hc*sigma
         cff1_r=Cs_r(k)

         do j=1,Mm
            do i=1,Lm

               z_r0=cff_r+cff1_r*h(i,j) 

               z_r(i,j,k) = zeta(i,j) + z_r0*cff2(i,j)

            enddo
         enddo
      enddo
      end


