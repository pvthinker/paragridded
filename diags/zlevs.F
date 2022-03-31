!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!! Compute z_r and z_w for NEW_S_COORD
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!



      subroutine zlevs(Lm,Mm,N, h, zeta, hc, Cs_r, Cs_w,z_r,z_w)
! compute z_r AND z_w

      implicit none

      integer Lm,Mm,N, i,j,k

      real*8 Cs_w(0:N), Cs_r(N), cff_w, cff_r, cff1_w, cff1_r,
     &     hc, ds,
     &     zeta(Lm,Mm),
     &     z_r(Lm,Mm,N),z_w(Lm,Mm,0:N),
     &     h(Lm,Mm), cff2(Lm, Mm)


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
!
      do k=1,N,+1
         cff_r=hc*ds*(dble(k-N)-0.5)
         cff1_r=Cs_r(k)
         do j=1,Mm
            do i=1,Lm
               z_r(i,j,k)=zeta(i,j) + cff2(i,j)*(cff_r+cff1_r*h(i,j))
            enddo
         enddo
      enddo
!
      do k=1,N,+1
         cff_w=hc*ds* dble(k-N)
         cff1_w=Cs_w(k)
         do j=1,Mm
            do i=1,Lm
               z_w(i,j,k)=zeta(i,j) + cff2(i,j)*(cff_w+cff1_w*h(i,j))
            enddo
         enddo
      enddo
      end


      subroutine zrs(Lm,Mm,N, h, zeta, hc, Cs_r, z_r)
! compute only z_r

      implicit none

      integer Lm,Mm,N, i,j,k

      real*8  Cs_r(N), cff_w, cff_r, cff1_w, cff1_r,
     &     hc, ds,
     &     zeta(Lm,Mm),
     &     z_r(Lm,Mm,N),
     &     h(Lm,Mm), cff2(Lm, Mm)


      ds=1.D0/dble(N)

      do j=1,Mm
         do i=1,Lm
            cff2(i,j) = (zeta(i,j)+h(i,j))/(h(i,j)+hc)
         enddo
      enddo
!
      do k=1,N,+1
         cff_r=hc*ds*(dble(k-N)-0.5)
         cff1_r=Cs_r(k)
         do j=1,Mm
            do i=1,Lm
               z_r(i,j,k)=zeta(i,j) + cff2(i,j)*(cff_r+cff1_r*h(i,j))
            enddo
         enddo
      enddo

      end


