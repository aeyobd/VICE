# cython: language_level = 3, boundscheck = False, wraparound = False, cdivision = True

from __future__ import absolute_import
from ..._globals import _DIRECTORY_
from ...core import _pyutils
from ...core cimport _cutils

from libc.math cimport NAN, sqrt, atanh, log, exp
cimport cython

from libc.stdlib cimport malloc, free

from . cimport _analytic_migration_2d
import numpy as np


""""
A struct to hold the migration parameters of a star in 2D.
"""
cdef struct migration_star_2d:
	double R_birth
	double R_final
	double z_birth
	double z_final
	double t_birth
	double t_end


cdef (double, double) sqrt_migration_2d(migration_star_2d* star, double time):
	"""
	A migration function that linearly interpolates the radius and height of a star
	"""
	cdef double x = (time - star.t_birth) / (star.t_end - star.t_birth)
	cdef double R = star.R_birth + (star.R_final - star.R_birth) * sqrt(x)
	cdef double z = star.z_birth + (star.z_final - star.z_birth) * sqrt(x)
	return R, z


cdef (double, double) linear_migration_2d(migration_star_2d* star, double time):
	"""
	"""
	cdef double x = (time - star.t_birth) / (star.t_end - star.t_birth)
	cdef double R = star.R_birth + (star.R_final - star.R_birth) * x
	cdef double z = star.z_birth + (star.z_final - star.z_birth) * x
	return R, z


@staticmethod
cdef int bin_of(double[::1] bins, size_t n_bins, double R) nogil:
	"""
	Efficient binary search for the bin index of a given radius R. 

	The array `bins` must be sorted and of length `n_bins`. Returns the
	index of the bin that contains the radius R (left-closed, right-open).

	If R is outside the range of the bins, returns -1.
	"""
	cdef int left = 0
	cdef int right = n_bins - 1
	cdef int mid

	while left <= right:
		mid = (left + right) // 2
		if bins[mid] <= R < bins[mid+1]:
			return mid
		elif R < bins[mid]:
			right = mid - 1
		else:
			left = mid + 1

	return -1

cdef double reflect_boundary(double R, double R_min, double R_max):
	"""
	Reflects the radius R off of the boundaries R_min and R_max.
	"""
	while (R < R_min):
		dR = R_min - R
		R = R_min + dR

	while (R > R_max):
		dR = R - R_max
		R = R_max - dR

	return R


cdef double absorb_boundary(double R, double R_min, double R_max):
	"""
	Absorbs the radius R into the boundaries R_min and R_max.
	"""
	if R < R_min:
		R = R_min
	elif R > R_max:
		R = R_max
	return R


cdef double no_boundary(double R, double R_min, double R_max):
	"""
	Does nothing to the radius R.
	"""
	if (R < R_min) or (R > R_max):
		return NAN
	return R


cpdef (double, double) f_initial_default(double[::1] r_bins, int zone, double t, int n):
	"""
	The default initial radius function. Returns the radius of the star at time t.
	"""
	cdef double r_low = r_bins[zone]
	cdef double r_high = r_bins[zone + 1]

	cdef double R = rand_range(r_low, r_high)
	cdef double z = 0.

	return R, z


cdef double rand_sec2():
	"""
	Returns a random number drawn from a sech2 distribution.
	"""
	cdef double u = rand_range(-1, 1)
	return atanh(u)


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
		z_f = hz*2 * rand_sec2()
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
	z_f = hz*2 * rand_sec2()
	return R_f, z_f


cdef class c_analytic_migration_2d:
	"""
	The C-implementation of a generalized functional migration model.

	The initial and final radii are determined from the functions f_initial
	and f_final which are called with the signature f(r_bins, zone, t, n) and 
	f_(r_bins, R_birth, tform, n). 
	The functional form will be called with
	f(migration_star_2d, time) and should return the new radius of the star.
	"""

	cdef public int n_zones
	cdef int n_t
	cdef int n_stars

	cdef double dt
	cdef double t_end

	cdef double[:, :, :] _R_birth
	cdef double[:, :, :] _R_final
	cdef double[:, :, :] _z_birth
	cdef double[:, :, :] _z_final

	cdef double R_min
	cdef double R_max

	cdef double[::1] _radial_bins

	cdef bint _write
	cdef char* _filename

	cdef (double, double) (*migration_func)(migration_star_2d*, double )
	cdef double (*boundary_func)(double, double, double )

	def __cinit__(self, radbins, 
			migration_mode="sqrt",
			int n_stars=2, double dt=0.01, double t_end=13.5, filename=None,
			boundary_conditions="reflect",
			f_final_kwargs={},
		):
		"""
		See python documentation for analytic migration 2D
		"""
		self.dt = dt
		self.t_end = t_end
		self.n_stars = n_stars
		self.radial_bins = radbins
		self.filename = filename

		self._write = False
		self.n_t = round(t_end / dt)
		self.n_zones = len(radbins) - 1

		self.alloc_arrays()
		self.init_radii(f_initial_default, f_final_liam, f_final_kwargs)
		
		self.R_min = self._radial_bins[0]
		self.R_max = self._radial_bins[self.n_zones]

		if migration_mode == "sqrt":
			self.migration_func = sqrt_migration_2d
		elif migration_mode == "linear":
			self.migration_func = linear_migration_2d
		else:
			raise ValueError("migration mode not know")

		if boundary_conditions == "reflect_final":
			self.apply_final_boundary(reflect_boundary)
			self.boundary_func = no_boundary
		elif boundary_conditions == "absorb_final":
			self.apply_final_boundary(absorb_boundary)
			self.boundary_func = no_boundary
		elif boundary_conditions == "reflect":
			self.boundary_func = reflect_boundary
		elif boundary_conditions == "absorb":
			self.boundary_func = absorb_boundary
		else:
			raise ValueError("Invalid boundary condition.")


	def alloc_arrays(self):
		"""Allowocates the arrays for the particle positions."""
		arr_shape = (self.n_zones, self.n_t, self.n_stars)
		dtype = np.float64
		self._R_birth = np.empty(arr_shape, dtype=dtype)
		self._R_final = np.empty(arr_shape, dtype=dtype)
		self._z_birth = np.empty(arr_shape, dtype=dtype)
		self._z_final = np.empty(arr_shape, dtype=dtype)


	cpdef call(self, int zone, double tform, double time, int n=0):
		cdef int bin_id
		cdef double R_new
		cdef double z_new

		cdef int time_int = round(tform / self.dt)
		cdef migration_star_2d star = self.get_star(zone, time_int, n)

		R_new, z_new = self.migration_func(&star, time)
		R_new = self.boundary_func(R_new, self.R_min, self.R_max)

		bin_id = bin_of(self._radial_bins, self.n_zones + 1, R_new)
		
		if R_new < self.R_min or R_new > self.R_max:
			raise ValueError("Radius out of bounds %f" % R_new)

		if self.write:
			self.write_migration(f"{zone},{time_int},{n},{time},{R_new},{z_new},{bin_id}\n")
			
		return bin_id


	cpdef migration_star_2d get_star(self, int zone, int t_idx, int n):
		if t_idx >= self.n_t or t_idx < 0:
			raise ValueError("Time index %d out of bounds." % t_idx)
		if zone >= self.n_zones or zone < 0:
			raise ValueError("Zone index %d out of bounds." % zone)
		if n >= self.n_stars or n < 0:
			raise ValueError("Star index %d out of bounds." % n)

		cdef migration_star_2d star
		star.R_birth = self._R_birth[zone, t_idx, n]
		star.R_final = self._R_final[zone, t_idx, n]
		star.z_birth = self._z_birth[zone, t_idx, n]
		star.z_final = self._z_final[zone, t_idx, n]
		star.t_birth = self.dt * t_idx
		star.t_end = self.t_end
		return star


	cpdef void init_radii(self, f_ini, f_fin, f_final_kwargs={}):
		cdef double r_i, r_f, z_i, z_f

		for n in range(self.n_stars):
			for zone in range(self.n_zones):
				for i in range(self.n_t):
					r_i, z_i = f_ini(self._radial_bins, zone, self.dt * i, n)
					r_f, z_f = f_fin(r_i, self.dt * i, n, **f_final_kwargs)
					self._R_birth[zone, i, n] = r_i
					self._R_final[zone, i, n] = r_f
					self._z_birth[zone, i, n] = z_i
					self._z_final[zone, i, n] = z_f


	cpdef void apply_final_boundary(self, boundary_func):
		cdef int i, j, k
		for i in range(self.n_zones):
			for j in range(self.n_t):
				for k in range(self.n_stars):
					self._R_final[i, j, k] = boundary_func(self._R_final[i, j, k], self.R_min, self.R_max)


	def write_initial_final(self, filename):
		cdef int i, j, k
		with open(filename, "w") as f:
			f.write("zone,i,n,t,R_birth,R_final,z_birth,z_final\n")
			for i in range(self.n_zones):
				for j in range(self.n_t):
					for k in range(self.n_stars):
						f.write(f"{i},{j},{k},{self.dt * j},"
								f"{self._R_birth[i, j, k]},{self._R_final[i, j, k]},"
								f"{self._z_birth[i, j, k]},{self._z_final[i, j, k]}\n")


	@property 
	def filename(self):
		return self._filename

	@filename.setter
	def filename(self, value):
		cdef size_t f_len
		if value is not None:
			f_len = <size_t>(2 * len(value))
			self._filename = <char *>malloc(f_len * sizeof(char))
			_cutils.set_string(self.filename, value)
			self.write = True
		else:
			self._filename = ''

	@property
	def radial_bins(self):
		return [self._radial_bins[i] for i in range(self.n_zones + 1)]

	@radial_bins.setter
	def radial_bins(self, value):
		value = _pyutils.copy_array_like_object(value)
		_pyutils.numeric_check(value, TypeError, "Non-numerical value detected.")
		value = sorted(value)
		self.n_zones = len(value) - 1
		self._radial_bins = np.array(value, dtype=np.float64)

	def get_n_zones(self):
		return self.n_zones

	@property
	def write(self):
		return self._write

	@write.setter
	def write(self, a):
		if self.filename.decode() == '':
			print("warning, filename not set, so will not write")
			self._write = False
		else:
			self._write = a

		if a and self.filename.decode() != '':
			self.write_header()
