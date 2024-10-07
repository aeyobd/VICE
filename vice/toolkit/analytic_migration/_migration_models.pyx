# cython: language_level = 3, boundscheck = False, wraparound = False, cdivision = True

from __future__ import absolute_import

from . cimport _migration_utils
from ...core cimport _cutils
from ...core import _pyutils
from ._migration_utils cimport rand_range, randn, rand_sech2, to_double_ptr
from libc.math cimport exp, atanh

from libc.stdlib cimport free



cdef class c_initial_positions:
	pass

cdef class c_final_positions:
	pass

cdef class c_initial_positions_uniform(c_initial_positions):
	# Static class attributes
	cdef double zone_width
	cdef double R_min
	cdef double R_max
	
	def __cinit__(self, *, double zone_width, double R_min, double R_max):
		# Initialize to static defaults
		self.zone_width = zone_width
		self.R_min = R_min
		self.R_max = R_max

	cpdef (double, double) call(self, double R_i, double t, int n):

		cdef double R_low = max(self.R_min, R_i - self.zone_width/2)
		cdef double R_high = min(self.R_max, R_i + self.zone_width/2)
		cdef double R = rand_range(R_low, R_high)
		cdef double z = 0.

		return R, z
	

cdef class c_final_positions_gaussian(c_final_positions):
	cdef double sigma_r8, tau_power, R_power, hz_s, tau_s_z, R_s

	def __cinit__(self,
			double sigma_r8,
			double tau_power,
			double R_power,
			double hz_s,
			double tau_s_z,
			double R_s,
		):
		self.sigma_r8 = sigma_r8
		self.tau_power = tau_power
		self.R_power = R_power
		self.hz_s = hz_s
		self.tau_s_z = tau_s_z
		self.R_s = R_s


	cpdef (double, double) call(self, double R, double time_birth, int n, double time):
		cdef double R_f, z_f, sigma, hz
		if time < time_birth:
			return -1, -1

		cdef double delta_t = time - time_birth

		sigma = self.sigma_r8 * (R / 8.)**self.R_power * (delta_t / 8.)**self.tau_power
		R_f = R + sigma * randn()

		hz = (self.hz_s / exp(2.0)) * exp(delta_t / self.tau_s_z + R_f / self.R_s)
		z_f = hz * 2 * rand_sech2()

		return R_f, z_f



