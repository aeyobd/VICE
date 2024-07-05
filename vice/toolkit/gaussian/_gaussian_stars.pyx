# cython: language_level = 3, boundscheck = False

from __future__ import absolute_import
from ..._globals import _DIRECTORY_
from ...core import _pyutils
from ...core cimport _cutils


from libc.stdlib cimport malloc, free
from libc.math cimport NAN, sqrt, pow
cimport cython

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
	cdef double * _r_birth
	cdef double * _r_final
	cdef double sigma_R
	cdef double tau_R
	cdef double t_end
	cdef bint _write
	cdef char* filename
	cdef public double r_max
	cdef public double r_min


	def __cinit__(self, radbins, int n_stars=2, 
				  double dt=0.01, double t_end=13.5, filename=None, 
				  double sigma_R=1.27):
		self.dt = dt
		self.t_end = t_end
		self.n_stars = n_stars
		self.radial_bins = radbins
		self.sigma_R = sigma_R
		self.set_filename(filename)

		self._write = False
		self.n_t = round(t_end/dt)
		self.n_bins = len(radbins)
		self.r_min = radbins[0]
		self.r_max = radbins[self.n_bins-1]
		self.alloc_arrays()
		self.init_radii()

	def set_N_max(self):
		cdef int i_test = self.n_t * self.n_stars * self.n_bins
		if i_test < 0:
			raise ValueError("negative max index, ", i_test)
		self.N_idx = <size_t> i_test


	def alloc_arrays(self):
		self.set_N_max()
		cdef double * arr = <double *> malloc(self.N_idx * sizeof(double))
		if not arr:
			raise MemoryError()
		cdef double * arr2 = <double *> malloc(self.N_idx * sizeof(double))
		if not arr2:
			raise MemoryError()

		self._r_birth = arr
		self._r_final = arr2


	def set_filename(self, filename):
		cdef size_t f_len
		if filename is not None:
			f_len = <size_t> (2*len(filename))
			self.filename = <char *> malloc(f_len * sizeof(char))
			_cutils.set_string(self.filename, filename)
			self.write = True
		else:
			self.filename = ''


	cpdef void init_radii(self):
		cdef double r_i

		for n in range(self.n_stars):
			for zone in range(self.n_bins):
				for i in range(self.n_t):
					tform = self.dt * i
					N = self.get_idx(zone, tform, n=n)
					r_i = rand_range(self._radial_bins[zone], self._radial_bins[zone+1])
					# random sample in birth zone for variance
					self._r_birth[N] = r_i
					self._r_final[N] = self.calc_r_final(r_i, tform)
				# end
			# endfor
		# endfor

	cpdef double calc_r_final(self, double r_birth, double tform):
		cdef double r
		r = r_birth + self.delta_R(self.t_end - tform)
		
		# boundary limits
		if r > self.r_max:
			r = self.r_max
		if r < self.r_min:
			r = self.r_min # could also wrap around, etc.

		return r


	def __dealloc__(self):
		free(self._r_birth)
		free(self._r_final)
		free(self._radial_bins)

	def call(self, int zone, double tform, double time, int n=0):
		cdef int bin_id
		cdef size_t N
		cdef double td
		cdef int idx

		if zone < 0 or zone >= self.n_bins or n < 0 or n >= self.n_stars:
			return -1

		idx = self.get_idx(zone, tform, n=n)
		if idx < 0:
			return - 1

		N = <size_t>idx

		final_radius = self._r_final[N]
		birth_radius = self._r_birth[N]
		td = (time - tform) / (self.t_end - tform)
		R_new = birth_radius + (final_radius - birth_radius) * sqrt(td)
		
		bin_id = bin_of(self._radial_bins, self.n_bins, R_new)

		if self.write:
			self.write_migration(f"{N},{time},{R_new},{bin_id}\n")
			
		return bin_id


	def write_migration(self, s):
		with open(self.filename, "a") as f:
			f.write(s)


	def get_idx(self, int zone, double tform, int n=0):
		cdef int t_int
		cdef size_t N	
		cdef int N_int

		t_int = round(tform / self.dt) 
		if t_int > self.n_t:
			print("time out of range %f" % tform)
			return -1
		if n > self.n_stars:
			print("n out of range %i" % n)
			return -1

		if zone > self.n_bins:
			print("zone out of range %i" % zone)
			return -1

		N_int = (t_int * self.n_bins * self.n_stars 
			+ zone * self.n_stars
			+ n)
		if N_int < 0:
			print(f"Index must be positive, instead got {N_int}")
			return -1
		N = <size_t> N_int

		if N > self.N_idx:
			print(f"got out of range index {N}, values zone={zone}, tform={tform}, n={n}")
			return -1

		return N




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

		if self.filename.decode() == '':
			print("warning, filename not set, so will not write")
			self._write = False
		else:
			self._write = a

		if a and self.filename.decode() != '':
			self.write_header()

	@property
	def radial_bins(self):
		return [self._radial_bins[i] for i in range(self.n_bins + 1)]

	def get_r_birth(self, i):
		if 0 <= i < self.N_idx:
			return self._r_birth[i]

	def get_r_final(self, i):
		if 0 <= i < self.N_idx:
			return self._r_final[i]

	@radial_bins.setter
	def radial_bins(self, value):
		value = _pyutils.copy_array_like_object(value)
		_pyutils.numeric_check(value, TypeError,
			"Non-numerical value detected.")
		value = sorted(value)
		self.n_bins = len(value) - 1
		if self._radial_bins is not NULL: 
			free(self._radial_bins)
		self._radial_bins = _cutils.copy_pylist(value)


@staticmethod
cdef int bin_of(double * bins, size_t n_bins, double R) nogil:
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

