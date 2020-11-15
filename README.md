# Paragridded

`Paragridded` is a python module to perform offline diagnostics on
large volumes of high-resolution fluid simulations data. The data
should be discretized on logically rectangular grids, potentially
staggered (C-grid). The data are stored in NetCDF files. The module is
designed to be fast and scalable on HPC centers. The tools can be used
either in batch mode (MPI) or in interactive mode (multithreading).

The module provides

* sub-class of ndarray with
   - metadata
   - grid staggering
   - named dimensions

* functions to perform fast finite differences operations
   - gradient, divergence, curl
   - two-points averaging
   - lambda_2
   - computation of potential vorticity
   - vertical interpolation
   
  functions are
   - staggering aware
   - handle metadata
   - compiled with numba, achieving cpu peak performance

* NetCDF reading tools to handle parallel files
  - the API follows the one-file standard netCDF4.py API as much as
    possible
  - can read one subdomain or several subdomains arranged in an array
  - return variables with their halo (of any width) by reading neighbouring files
  - can read NetCDF stored in *.tar without untaring them (via the fuse library)

* parallel tools
  - to harness MPI or multithreads
  - perform reads and computations in parallel

* plotting functions
  - to produce maps from list of arrays

* customizations for a few models
  - croco, a regional circulation ocean model
  - nyles, an implicit LES model

The module competes with the xarray+dask+zarr+xgcm suite and offers a
completely different approach. Here are the differences

 pangeo     | this module
 ---------  | --------------- 
 xarray     | ndarray subclass 
 dask       | schwimmbad 
 zarr       | tar + fuse 
 xgcm       | grid operations with numba 


* keywords

parallel files, parallel computation, speed, high-resolution
simulations, staggered grid, netCDF files

![Demo](/figures/demo_1.png)
