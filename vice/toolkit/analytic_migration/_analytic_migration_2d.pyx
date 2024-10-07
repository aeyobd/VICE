# cython: language_level = 3, boundscheck = False, wraparound = False, cdivision = True

from __future__ import absolute_import
from ..._globals import _DIRECTORY_
from ...core import _pyutils
from ...core cimport _cutils

from libc.math cimport NAN, sqrt, atanh, log, exp
cimport cython

from libc.stdlib cimport malloc, free

from . cimport _migration_utils 
from ._migration_utils cimport bin_of, no_boundary, reflect_boundary, absorb_boundary, array_3d, migration_star_2d, sqrt_migration_2d, linear_migration_2d, to_double_ptr
from ._migration_utils import sqrt_migration_2d_py, linear_migration_2d_py, reflect_boundary_py, absorb_boundary_py, no_boundary_py


ctypedef (double, double) (*MigrationFunc)(migration_star_2d*, double )
ctypedef double (*BoundaryFunc)(double, double, double )

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

	cdef object _R_birth
	cdef object _R_final
	cdef object _z_birth
	cdef object _z_final

	cdef double R_min
	cdef double R_max

	cdef double* _radial_bins

	cdef bint _write
	cdef object migration_func
	cdef object boundary_func

	cdef str filename


	def __cinit__(self, radbins,*,
			str migration_mode,
			object initial_positions,
			object final_positions,
			int n_stars,
			double dt,
			double t_end, 
			str filename=None,
			str boundary_conditions="reflect",
		):
		# initialize all the variables to null/default values unless numeric

		self.dt = dt
		self.t_end = t_end

		self.n_stars = n_stars
		self.n_t = round(t_end / dt)
		self.n_zones = len(radbins) - 1
		self._write = False
		self.filename = ""
		self.R_min = NAN
		self.R_max = NAN

		self._radial_bins = NULL

		self.alloc_arrays()


	def __init__(self, radbins,
			str migration_mode, 
	      		object initial_positions,
			object final_positions, 
			int n_stars, 
			double dt, 
			double t_end, 
			str filename=None,
			str boundary_conditions="reflect",
		):
		"""
		see python version of class (vice.toolkit.analytic_migration.analytic_migration_2d)
		"""

		self.radial_bins = radbins
		self.filename = filename
		self._write = False

		self.R_min = self._radial_bins[0]
		self.R_max = self._radial_bins[self.n_zones]

		self.set_migration_mode(migration_mode)
		self.set_boundary_conditions(boundary_conditions)
		self.init_radii(initial_positions, final_positions)


	cpdef alloc_arrays(self):
		"Allowocates the array objects of the class to hold the star properties."
		self._R_birth = array_3d(self.n_zones, self.n_t, self.n_stars)
		self._R_final = array_3d(self.n_zones, self.n_t, self.n_stars)
		self._z_birth = array_3d(self.n_zones, self.n_t, self.n_stars)
		self._z_final = array_3d(self.n_zones, self.n_t, self.n_stars)


	cdef set_migration_mode(self, migration_mode):
		if migration_mode == "sqrt":
			self.migration_func = sqrt_migration_2d_py
		elif migration_mode == "linear":
			self.migration_func = linear_migration_2d_py
		else:
			raise ValueError("migration mode not know")



	cdef set_boundary_conditions(self, boundary_conditions):
		"""
		Sets the boundary conditions for the migration model.

		Parameters
		----------
		boundary_conditions : str
			The boundary conditions to apply. Options are
			"reflect", "absorb", "reflect_final", "absorb_final".
		"""
		if boundary_conditions == "reflect_final":
			self.apply_final_boundary(reflect_boundary)
			self.boundary_func = no_boundary_py
		elif boundary_conditions == "absorb_final":
			self.apply_final_boundary(absorb_boundary)
			self.boundary_func = no_boundary_py
		elif boundary_conditions == "reflect":
			self.boundary_func = reflect_boundary_py
		elif boundary_conditions == "absorb":
			self.boundary_func = absorb_boundary_py
		else:
			raise ValueError("Invalid boundary condition.")


	def __call__(self, int zone, double tform, double time, int n=0):
		"""
		Applies the migration model to a star.

		Parameters
		----------
		zone : int
			The zone of the star.
		tform : float
			The formation time of the star.
		time : float
			The time to migrate to.
		n : int
			The star number.

		Returns
		-------
		int
			The new zone of the star.
		"""
		return self.call(zone, tform, time, n)

	cdef call(self, int zone, double tform, double time, int n=0):
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

		cdef migration_star_2d star = self.get_star(zone, time_int, n)

		R_new, z_new = self.migration_func(star, time)
		R_new = self.boundary_func(R_new, self.R_min, self.R_max)

		bin_id = bin_of(self._radial_bins, self.n_zones + 1, R_new)

		if self.write:
			self.write_migration(f"{zone},{time_int},{n},{time},{R_new},{z_new},{bin_id}\n")
			
		return bin_id


	cpdef migration_star_2d get_star(self, int zone, int t_idx, int n):

		cdef migration_star_2d star
		star.R_birth = self._R_birth.get(zone, t_idx, n)
		star.R_final = self._R_final.get(zone, t_idx, n)
		star.z_birth = self._z_birth.get(zone, t_idx, n)
		star.z_final = self._z_final.get(zone, t_idx, n)
		star.t_birth = self.dt * t_idx
		star.t_end = self.t_end
		return star


	cpdef init_radii(self, f_initial, f_final):
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
		cdef int i, j, k
		cdef double R_new 
		for i in range(self.n_zones):
			for j in range(self.n_t):
				for k in range(self.n_stars):
					R_new = self._R_final.get(i, j, k)
					R_new = boundary_func(R_new, self.R_min, self.R_max)
					self._R_final.set_value(i, j, k, R_new)


	cpdef write_initial_final(self, filename):
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
		value_c, length = to_double_ptr(value)
		self._radial_bins = value_c
		self.n_zones = length - 1


	def get_n_zones(self):
		return self.n_zones

	@property
	def write(self):
		return self._write

	@write.setter
	def write(self, a):
		if self.filename == "":
			print("warning, filename not set, so will not write")
			self._write = False
		else:
			self._write = a

		if a and self.filename != "":
			self.write_header()

	def dealloc(self):
		if self._radial_bins is not NULL:
			free(self._radial_bins)
		self._R_birth.free()
		self._R_final.free()
		self._z_birth.free()
		self._z_final.free()

	def __dealloc__(self):
		self.dealloc()

	def write_header(self):
		if self.filename == "":
			return
		with open(self.filename, "w") as f:
			f.write(f"zone,time_int,n,time,R,z,bin_id\n")

	def write_migration(self, s):
		if self.filename == "":
			return

		with open(self.filename, "a") as f:
			f.write(s)
