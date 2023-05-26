# cython: language_level = 3, boundscheck = False

from __future__ import absolute_import

cdef extern from "../../src/utils.h":
	void seed_random()
	double rand_range(double minimum, double maximum)
	double randn()



cdef class c_gaussian_stars:
	cdef double[:] _radial_bins
	cdef int n_bins
	cdef int n_t
	cdef int n_stars
	cdef Py_ssize_t N_idx
	cdef double dt
	cdef double[:] radii
	cdef double sigma_R
	cdef double tau_R
	cdef bint _write
	cdef char * filename
