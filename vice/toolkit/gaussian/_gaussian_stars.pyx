# cython: language_level = 3, boundscheck = False

from __future__ import absolute_import
from ..._globals import _DIRECTORY_
from ...core import _pyutils
from ...core cimport _cutils


from libc.stdlib cimport malloc, free

from . cimport _gaussian_stars



cdef class c_gaussian_stars:
	"""
	The C-implementation of the gaussian_stars object. See python version for
	documentation.
	"""
	cdef double * _radial_bins
	cdef int n_bins
	cdef int n_t
	cdef int n_stars
	cdef size_t N_idx
	cdef double dt
	cdef double * radii
	cdef double sigma_R
	cdef double tau_R
	cdef double t_end
	cdef bint _write
	cdef char* filename


	def __cinit__(self, radbins, int n_stars=2, 
				  double dt=0.01, double t_end=13.5, filename=None, 
				  double sigma_R=1.27):
		self.radial_bins = radbins
		self.n_t = round(t_end/dt)
		self.t_end = t_end
		self.n_stars = n_stars
		self.dt = dt

		cdef int i_test = self.n_t * self.n_stars * self.n_bins
		if i_test < 0:
			raise ValueError("negative max index, ", i_test)
		self.N_idx = <size_t> i_test

		cdef double * arr = <double *> malloc(self.N_idx * sizeof(double))
		if not arr:
			raise MemoryError()

		self.radii = arr

		self.sigma_R = sigma_R
		self._write = False
		cdef size_t f_len
		if filename is not None:
			f_len = <size_t> (2*len(filename))
			self.filename = <char *> malloc(f_len * sizeof(char))
			_cutils.set_string(self.filename, filename)
			self.write = True


	def __dealloc__(self):
		free(self.radii)
		free(self._radial_bins)


	def __call__(self, int zone, double tform, double time, *, int n=0):
		cdef int bin_id
		cdef double r


		if not (0 <= zone < self.n_bins):
			raise ValueError("Zone out of range: %d" % (zone))
		cdef Py_ssize_t zone_idx = zone

		if tform > time:
			raise ValueError("Time out of range: %f < tform = %f" 
					% (time, tform))

		birth_radius = (self.radial_bins[zone_idx]
						 + self.radial_bins[zone_idx + 1]) / 2

		cdef size_t N
		N = self.get_idx(zone_idx, tform, n=n)

		if tform == time:
			R_final = birth_radius + self.delta_R(self.t_end - tform)
			if R_final < 0:
				R_final = 0
			if R_final > 20:
				R_final = 20
			self.radii[N] = R_final
			R_new = birth_radius
			bin_id =  zone
		else:
			final_radius = self.radii[N]
			R_new = birth_radius + (final_radius - birth_radius) * (time - tform)**0.5 / (self.t_end - tform)**0.5
			
			
			bin_id = self.bin_of(R_new)

		if (0 > bin_id) or (self.n_bins < bin_id):
			raise RuntimeError("calculated a nonsense bin, %i" % bin_id )

		if self.write:
			self.write_migration(f"{N},{time},{R_new},{bin_id}\n")
			
		return bin_id


	def write_migration(self, s):
		if self.filename is None:
			return

		with open(self.filename, "a") as f:
			f.write(s)


	def get_idx(self, int zone, double tform, *, int n=0):
		cdef int t_int
		cdef size_t N	
		cdef int N_int

		t_int = round(tform / self.dt) 
		if t_int > self.n_t:
			raise ValueError("time out of range %f" % tform)
		if n > self.n_stars:
			raise ValueError("n out of range %i" % n)


		N_int = (t_int * self.n_bins * self.n_stars 
			+ zone * self.n_stars
			+ n)
		if N_int < 0:
			raise ValueError(f"Index must be positive, instead got {N_int}")
		N = <size_t> N_int

		if N > self.N_idx:
			raise ValueError(f"got out of range index {N}, values zone={zone}, tform={tform}, n={n}")

		return N


	def bin_of(self, double R):
		if R < 0:
			return -1

		for i in range(self.n_bins):
			if self.radial_bins[i] <= R  <= self.radial_bins[i+1]:
				return int(i)
		return self.n_bins


	def delta_R(self, delta_t):
		cdef double r
		r = randn() * delta_t**0.5 * self.sigma_R
		return r


	def write_header(self):
		if self.filename is None:
			return
		with open(self.filename, "w") as f:
			f.write("N,t,R,zone\n")


	@property
	def write(self):
		return self._write


	@write.setter
	def write(self, a):
		self._write = a
		if a:
			self.write_header()

	@property
	def radial_bins(self):
		return [self._radial_bins[i] for i in range(self.n_bins + 1)]


	@radial_bins.setter
	def radial_bins(self, value):
		value = _pyutils.copy_array_like_object(value)
		_pyutils.numeric_check(value, TypeError,
			"Non-numerical value detected.")
		value = sorted(value)
		self.n_bins = len(value) - 1
		if self._radial_bins is not NULL: free(self._radial_bins)
		self._radial_bins = _cutils.copy_pylist(value)

