# cython: language_level = 3, boundscheck = False

from __future__ import absolute_import
from cmath import atanh, NAN, sqrt

cdef extern from "../../src/utils.h":
	void seed_random()
	double rand_range(double minimum, double maximum)
	double randn()


print("loaded migration header")

""""
A struct to hold the migration parameters of a star in 2D.

Attributes:
	R_birth: The birth radius of the star.
	R_final: The final radius of the star.
	z_birth: The birth z coordinate of the star.
	z_final: The final z coordinate of the star.
	t_birth: The birth time of the star.
	t_end: The end time of the star (simulation).
"""
cdef struct migration_star_2d:
	double R_birth
	double R_final
	double z_birth
	double z_final
	double t_birth
	double t_end



cdef (double*, int) to_double_ptr(arr, bint sort=*)
cpdef double rand_sech2() 
cdef inline (double, double) sqrt_migration_2d(migration_star_2d*, double) 
cdef inline (double, double) linear_migration_2d(migration_star_2d* star, double time)
cdef inline int bin_of(double * bins, size_t n_bins, double R)
cdef inline double reflect_boundary(double R, double R_min, double R_max) 
cdef inline double absorb_boundary(double R, double R_min, double R_max)
cdef inline double no_boundary(double R, double R_min, double R_max)


cdef class array_3d:
	cdef double* array
	cdef int dim1, dim2, dim3
	cdef int length

	cdef double get(self, int i, int j, int k) except *

	cdef void set_value(self, int i, int j, int k, double value) except *

	cpdef (int, int, int) shape(self) except *
	cpdef int get_idx(self, int i, int j, int k) except *

	cpdef void free(self)
