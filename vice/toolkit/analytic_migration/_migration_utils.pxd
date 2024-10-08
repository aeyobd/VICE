# cython: language_level = 3, boundscheck = False

from __future__ import absolute_import
from cmath import atanh, NAN, sqrt

cdef extern from "../../src/utils.h":
	void seed_random()
	double rand_range(double minimum, double maximum)
	double randn()


""""
A struct to hold the migration parameters of a star in 2D.

Attributes:
	R_birth: The birth radius of the star.
	R_final: The final radius of the star.
	z_birth: The birth z coordinate of the star.
	z_final: The final z coordinate of the star.
	t_birth: The birth time of the star.
	t_final: The end time of the star (simulation).
"""
cdef struct migration_star_2d:
	double R_birth
	double R_final
	double z_birth
	double z_final
	double t_birth
	double t_final



cdef (double*, int) to_double_ptr(arr, bint sort=*)
cpdef double rand_sech2() 
cdef double  c_migration_sqrt(migration_star_2d, double) except -1
cdef double  c_migration_sqrt_z(migration_star_2d, double) except -1

cdef double c_migration_linear(migration_star_2d, double) except -1
cdef double c_migration_linear_z(migration_star_2d, double) except -1

cdef int c_bin_of(double * bins, size_t n_bins, double R) except -2
cdef double c_reflect_boundary(double R, double R_min, double R_max)  except -1
cdef double c_absorb_boundary(double R, double R_min, double R_max) except -1
cdef double c_no_boundary(double R, double R_min, double R_max) except -1


cdef class array_3d:
	cdef double* array
	cdef int dim1, dim2, dim3
	cdef int length

	cpdef double get(self, int i, int j, int k) except *

	cpdef void set_value(self, int i, int j, int k, double value) except *

	cpdef (int, int, int) shape(self) except *
	cpdef int get_idx(self, int i, int j, int k) except *

	cpdef void free(self)
