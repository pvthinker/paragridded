FC = ifort
FFLAGS = -O3

C = gfortran
FFLAGS = -O4 -march=native


SRC = zlevs.F zlevs_croco_new.F rho_eos.F vinterp.f90
PYTHON = carrays.py croco_functions.py vert_coord.py vinterp.py

all: $(SRC)
	$(FC) -fPIC  -shared $(FFLAGS) $(SRC) -o libcroco.so

tar: $(SRC) $(PYTHON)
	tar cvf diags.tar Makefile $(SRC) $(PYTHON)
