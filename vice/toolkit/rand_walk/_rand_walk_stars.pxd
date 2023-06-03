# cython: language_level = 3, boundscheck = False

from __future__ import absolute_import

cdef extern from "../../src/utils.h":
	void seed_random()
	double rand_range(double minimum, double maximum)
	double randn()


