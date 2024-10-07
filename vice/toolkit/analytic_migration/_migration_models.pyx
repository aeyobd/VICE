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
	cdef double r_low, r_high
	cdef double * _radial_bins
	cdef int n_zones
	
	def __cinit__(self, radial_bins, int n_zones):
		# Initialize to static defaults
		self.r_low = radial_bins[0]
		self.r_high = radial_bins[n_zones]
		self.n_zones = n_zones
		self.radial_bins = radial_bins

	cpdef (double, double) call(self, int zone, double t, int n):
		if zone < 0 or zone >= self.n_zones:
			raise ValueError("Zone index out of bounds.")

		cdef double R = rand_range(self._radial_bins[zone], self._radial_bins[zone + 1])
		cdef double z = 0.

		return R, z
	
	cpdef free(self):
		free(self._radial_bins)


	@property
	def radial_bins(self):
		return [self._radial_bins[i] for i in range(self.n_zones + 1)]

	@radial_bins.setter
	def radial_bins(self, value):
		cdef double* value_c
		value_c, length = to_double_ptr(value, sort=True)
		self._radial_bins = value_c
		self.n_zones = length - 1


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


	cpdef (double, double) call(self, double R, double delta_t, int n):
		cdef double R_f, z_f, sigma, hz

		sigma = self.sigma_r8 * (R / 8.)**self.R_power * (delta_t / 8.)**self.tau_power
		R_f = R + sigma * randn()

		hz = (self.hz_s / exp(2.0)) * exp(delta_t / self.tau_s_z + R_f / self.R_s)
		z_f = hz * 2 * rand_sech2()

		return R_f, z_f



cpdef (double, double) f_initial_default(r_bins, int zone, double t, int n):
	"""
	The default initial radius function. Returns the radius of the star at time t.
	"""
	cdef double r_low = r_bins[zone]
	cdef double r_high = r_bins[zone + 1]

	cdef double R = rand_range(r_low, r_high)
	cdef double z = 0.

	return R, z




cpdef (double, double) f_final_liam(double R, double delta_t, int n,
		double sigma_r8=2.68, double tau_power=0.33, double R_power=0.61,
		double hz_s=0.24, double tau_s_z=7, double R_s=6
	):
	"""
	The final radius function for Liam's model as a function of initial radius, 
	stellar age (at the end of the simulation) and the particle number (ignored).

	The migration is described by a normal distribution centred on the particle's
	initial radius with a standard deviation given by
	``
		sigma = sigma_r8 * (R / 8.)**R_power * (delta_t / 8.)**tau_power
	``
	The z position is given by the distribution 
	``
		hz = (hz_s / exp(2) ) * exp(delta_t / tau_s_z + R_f / R_s)
		z_f = hz*2 * rand_sech2()
	``

	Parameters
	----------
	R : double
		The initial radius of the star.
	delta_t : double
		The time step of the simulation.
	n : int
		The particle number (ignored).
	sigma_r8 : double
		The standard deviation of the migration scaling
	

	"""

	cdef double R_f, z_f
	cdef double sigma, hz

	sigma = sigma_r8 * (R / 8.)**R_power * (delta_t / 8.)**tau_power
	R_f = R + sigma * randn()

	hz = (hz_s / exp(2) ) * exp(delta_t / tau_s_z + R_f / R_s)
	z_f = hz*2 * rand_sech2()
	return R_f, z_f

