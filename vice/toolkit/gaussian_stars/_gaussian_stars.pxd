# cython: language_level = 3, boundscheck = False

from __future__ import absolute_import

cdef extern from "./gauss_obj.h":
	GAUSSIANSTARS * gaussian_stars_initialize()
	void gaussian_stars_free(GAUSSIANSTARS *gns)


cdef extern from "../../src/utils.h":
	void seed_random()
	double rand_range(double minimum, double maximum)
	double randn()


cdef class c_gaussian_stars:
	cdef GAUSSIANSTARS *_gns
	cdef long _analog_idx
	cdef double _migration_time
	cdef object _analog_data
