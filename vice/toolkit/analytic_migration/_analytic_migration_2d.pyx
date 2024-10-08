# cython: language_level = 3, boundscheck = False, wraparound = False, cdivision = True

from __future__ import absolute_import
from ..._globals import _DIRECTORY_
from ...core import _pyutils
from ...core cimport _cutils

from libc.math cimport NAN, sqrt, atanh, log, exp
cimport cython

from libc.stdlib cimport malloc, free

from . cimport _migration_utils  as mu

from ._migration_utils import migration_sqrt, migration_sqrt_z, migration_linear, migration_linear_z, reflect_boundary, absorb_boundary, no_boundary


ctypedef double (*MigrationFunc)(mu.migration_star_2d, double ) except -1
ctypedef double (*MigrationFunc_Z)(mu.migration_star_2d, double ) except -1

ctypedef double (*BoundaryFunc)(double, double, double ) except -1


cdef class c_analytic_migration_2d:
	"""
	The C-implementation of a generalized functional migration model.
	See the python version for documentation.
	"""
	cdef public int n_zones
	cdef public int n_t
	cdef public int n_stars

	cdef public double dt
	cdef public double t_end

	cdef mu.array_3d _R_birth
	cdef mu.array_3d _R_final
	cdef mu.array_3d _z_birth
	cdef mu.array_3d _z_final

	cdef public double R_min
	cdef public double R_max

	cdef double* _radial_bins

	cdef bint _write
	cdef MigrationFunc migration_func
	cdef MigrationFunc migration_func_z
	cdef object boundary_func

	cdef public str filename
	cdef public bint verbose


	def __cinit__(self, radbins,*,
			str migration_mode,
			object initial_positions,
			object final_positions,
			int n_stars,
			double dt,
			double t_end, 
			str filename=None,
			str boundary_conditions="reflect",
	       		bint verbose=False,
	       		str initial_final_filename=None,
		):
		"""See python initialization documentation"""

		self.migration_func = NULL
		self._radial_bins = NULL

		# scalar properties
		self.dt = dt
		self.t_end = t_end
		self.n_stars = n_stars
		self.n_t = round(t_end / dt)
		self.n_zones = len(radbins) - 1
		self.verbose = verbose
		self.filename = filename
		self._write = False

		self.info("allocating memory")
		self.alloc_arrays()

		self.info("setting radial bins & mode")
		self.radial_bins = radbins
		self.R_min = self._radial_bins[0]
		self.R_max = self._radial_bins[self.n_zones]

		self.set_migration_mode(migration_mode)

		self.info("initializing radii")

		self.init_radii(initial_positions, final_positions)
		self.set_boundary_conditions(boundary_conditions)

		if initial_final_filename is not None:
			self.info("writting initial/final data")
			self.write_initial_final(initial_final_filename)

		self.info("fully initialized")


	def info(self, str message):
		"""prints an info message if verbose is set"""
		if self.verbose:
			print("[migration info]    ", message)
	
	cpdef alloc_arrays(self):
		"""Allocates memory for each of the arrays"""
		self._R_birth = mu.array_3d(self.n_zones, self.n_t, self.n_stars)
		self._R_final = mu.array_3d(self.n_zones, self.n_t, self.n_stars)
		self._z_birth = mu.array_3d(self.n_zones, self.n_t, self.n_stars)
		self._z_final = mu.array_3d(self.n_zones, self.n_t, self.n_stars)


	cdef int set_migration_mode(self, str migration_mode) except -1:
		"""Sets the migration mode, see python class description"""
		if migration_mode == "sqrt":
			self.migration_func = mu.c_migration_sqrt
			self.migration_func_z = mu.c_migration_sqrt_z
		elif migration_mode == "linear":
			self.migration_func = mu.c_migration_linear
			self.migration_func_z = mu.c_migration_linear_z
		else:
			raise ValueError("migration mode not know")
			return -1
		return 0



	cdef int set_boundary_conditions(self, str boundary_conditions) except -1:
		""" See python initialization documentation for details. """
		if boundary_conditions == "reflect_final":
			self.apply_final_boundary(mu.c_reflect_boundary)
			self.boundary_func = no_boundary
		elif boundary_conditions == "absorb_final":
			self.apply_final_boundary(mu.c_absorb_boundary)
			self.boundary_func = no_boundary
		elif boundary_conditions == "reflect":
			self.boundary_func = reflect_boundary
		elif boundary_conditions == "absorb":
			self.boundary_func = absorb_boundary
		else:
			raise ValueError("Invalid boundary condition.")
			return -1
		return 0


	def __call__(self, int zone, double tform, double time, int n=0):
		"see python documentation for the class"
		return self.call(zone, tform, time, n)



	cdef call(self, int zone, double tform, double time, int n=0):
		"see __call__ documentation in python version"

		cdef int bin_id
		cdef double R_new
		cdef double z_new

		cdef int time_int = round(tform / self.dt)

		if time_int >= self.n_t or time_int < 0:
			return -1
		if zone >= self.n_zones or zone < 0:
			return -1
		if n >= self.n_stars or n < 0:
			return -1

		cdef mu.migration_star_2d star = self.get_star(zone, time_int, n)

		R_new = self.migration_func(star, time)
		R_new = self.boundary_func(R_new, self.R_min, self.R_max)

		bin_id = mu.c_bin_of(self._radial_bins, self.n_zones + 1, R_new)

		if self.write:
			z_new = self.migration_func_z(star, time)
			self.write_migration(
				zone=zone,
				time_int=time_int,
				n=n,
				time=time,
				R=R_new,
				z=z_new,
				bin_id=bin_id
			)
		return bin_id


	cpdef mu.migration_star_2d get_star(self, int zone, int t_idx, int n):
		"Retrieves a migration_star_2d particle matching the given index"
		cdef mu.migration_star_2d star
		star.R_birth = self._R_birth.get(zone, t_idx, n)
		star.R_final = self._R_final.get(zone, t_idx, n)
		star.z_birth = self._z_birth.get(zone, t_idx, n)
		star.z_final = self._z_final.get(zone, t_idx, n)
		star.t_birth = self.dt * t_idx
		star.t_final = self.t_end
		return star


	cpdef init_radii(self, f_initial, f_final):
		"""Initializes the radii for this class
		
		f_initial is expected to be a function which takes 
		three arguments, the initial radius, the time, and the star number.
		and returns a tuple of doubles for R and Z.

		f_final is similar except it also takes an additional fourth argument
		for the final time of the simulation.
		"""

		cdef double r_i, r_f, z_i, z_f
		cdef double time
		cdef int zone, i, n
		for zone in range(self.n_zones):
			for i in range(self.n_t):
				for n in range(self.n_stars):
					time = self.dt * i
					r_i = (self._radial_bins[zone] + self._radial_bins[zone + 1]) / 2
					r_i, z_i = f_initial(r_i, time, n)

					r_f, z_f = f_final(r_i, time, n, self.t_end)

					self._R_birth.set_value(zone, i, n, r_i)
					self._R_final.set_value(zone, i, n, r_f)
					self._z_birth.set_value(zone, i, n, z_i)
					self._z_final.set_value(zone, i, n, z_f)


	cpdef void apply_final_boundary(self, boundary_func):
		"""
		If the radii are initialized, applies boundary contitions to
		any values which may fall outside of the radial bins
		"""
		cdef int i, j, k
		cdef double R_new 
		for i in range(self.n_zones):
			for j in range(self.n_t):
				for k in range(self.n_stars):
					R_new = self._R_final.get(i, j, k)
					R_new = boundary_func(R_new, self.R_min, self.R_max)
					self._R_final.set_value(i, j, k, R_new)


	cpdef write_initial_final(self, filename):
		if filename == None:
			raise ValueError("filename is None")

		cdef int i, j, k
		cdef double R_birth, R_final, z_birth, z_final

		with open(filename, "w") as f:
			f.write("zone,i,n,t,R_birth,R_final,z_birth,z_final\n")
			for i in range(self.n_zones):
				for j in range(self.n_t):
					for k in range(self.n_stars):
						R_birth = self._R_birth.get(i, j, k)
						R_final = self._R_final.get(i, j, k)
						z_birth = self._z_birth.get(i, j, k)
						z_final = self._z_final.get(i, j, k)
						f.write(f"{i},{j},{k},{self.dt * j},"
								f"{R_birth},{R_final},{z_birth},{z_final}\n")


	@property
	def radial_bins(self):
		return [self._radial_bins[i] for i in range(self.n_zones + 1)]

	@radial_bins.setter
	def radial_bins(self, value):
		if self._radial_bins is not NULL: free(self._radial_bins)

		cdef double* value_c
		value_c, length = mu.to_double_ptr(value)
		self._radial_bins = value_c
		self.n_zones = length - 1


	def get_n_zones(self):
		return self.n_zones

	@property
	def write(self):
		return self._write


	@write.setter
	def write(self, a):
		if self.filename is None:
			print("warning, filename not set, so will not write")
			self._write = False
		else:
			self._write = a

		if a and self.filename is not None:
			self.write_header()

	def dealloc(self):
		"""Deallocates any memory managed used by this class."""
		if self._radial_bins is not NULL:
			free(self._radial_bins)
		self._R_birth.free()
		self._R_final.free()
		self._z_birth.free()
		self._z_final.free()

	def __dealloc__(self):
		self.dealloc()

	cpdef write_header(self):
		"writes the header for the migration data"
		if self.filename is None:
			return
		with open(self.filename, "w") as f:
			f.write(f"zone,time_int,n,time,R,z,bin_id\n")

	cpdef write_migration(self, zone, time_int, n, time, R, z, bin_id):
		"writes the migration data to the file"
		if self.filename is None:
			return

		with open(self.filename, "a") as f:
			f.write(f"{zone},{time_int},{n},{time},{R},{z},{bin_id}\n")
