# cython: language_level = 3, boundscheck = False

from __future__ import absolute_import
from ..._globals import _DIRECTORY_
from ...core import _pyutils
from ...core cimport _cutils


from libc.stdlib cimport malloc, free

from . cimport _rand_walk_stars



cdef class c_rand_walk_stars:
	"""
	The C-implementation of the rand_walk_stars object. See python version for
	documentation.
	"""
	cdef double * _radial_bins
	cdef int n_zones
	cdef int n_t
	cdef int n_stars
	cdef size_t N_idx
	cdef double dt
	cdef double sigma_R
	cdef double tau_R
	cdef bint _write
	cdef char* filename
	cdef public double r_max
	cdef public double r_min

	cdef double * _radii

	def __cinit__(self, radbins, int n_stars=2, 
				  double dt=0.01, double t_end=13.5, filename=None, 
				  double sigma_R=1.27):

		self.radial_bins = radbins
		self.n_zones = len(radbins) - 1
		self.n_t = round(t_end/dt)
		self.n_stars = n_stars
		self.dt = dt

		self.sigma_R = sigma_R
		self.r_max = radbins[self.n_zones]
		self.r_min = radbins[0]

		self.alloc_arrays()
		self.init_radii()

		self.set_filename(filename)
		self._write = False


	def set_filename(self, filename):
		cdef size_t f_len
		if filename is not None:
			f_len = <size_t> (2*len(filename))
			self.filename = <char *> malloc(f_len * sizeof(char))
			_cutils.set_string(self.filename, filename)
			self.write = True
		else:
			self.filename = ''

	def set_N_max(self):
		cdef int i_test = self.n_t * self.n_stars * (self.n_zones + 1)
		if i_test < 0:
			raise ValueError("negative max index, ", i_test)
		self.N_idx = <size_t> i_test

	def alloc_arrays(self):
		self.set_N_max()

		cdef double * arr = <double *> malloc(self.N_idx * sizeof(double))
		if not arr:
			raise MemoryError()

		self._radii = arr

	cpdef void init_radii(self):
		cdef double r_i

		for n in range(self.n_stars):
			for zone in range(self.n_zones):
				for i in range(self.n_t):
					tform = self.dt * i
					N = self.get_idx(zone, tform, n=n)
					# random sample in birth zone for variance
					r_i = rand_range(self._radial_bins[zone], self._radial_bins[zone+1])
					if r_i < self._radial_bins[zone] or r_i >= self._radial_bins[zone+1]:
						print(f"r_i={r_i} not in zone {zone}, but in {bin_of(self._radial_bins, self.n_zones, r_i)}")
					bin_new = bin_of(self._radial_bins, self.n_zones, r_i)
					if bin_of(self._radial_bins, self.n_zones, r_i) != zone:
						print(f"r_i={r_i} not in zone {zone}, but in {bin_of(self._radial_bins, self.n_zones, r_i)}")
					self._radii[N] = r_i

	def __dealloc__(self):
		free(self._radii)
		free(self._radial_bins)


	cpdef int call(self, int zone, double tform, double time, int n=0):
		cdef int bin_id
		cdef size_t N
		cdef int idx


		if zone < 0 or zone > self.n_zones or n < 0 or n >= self.n_stars:
			print(f"zone or n out of range for {zone}, {tform}, {n}")
			return -1

		#print(f"zone={zone}, tform={tform}, time={time}, n={n}")
		idx = self.get_idx(zone, tform, n=n)
		if idx < 0:
			print(f"idx out of range for {zone}, {tform}, {n}")

			return -1

		N = <size_t>idx


		cdef double R = self._radii[N]
		cdef double dR = self.dR()
		if self.get_t_int(time) == self.get_t_int(tform):
			#print(f"R = {R}")
			pass
		else:
			#print(f"R = {R}, dR = {dR}")
			R += dR

			# reflective boundary conditions
			if R < self.r_min:
				dR = abs(self.r_min - R)
				R = self.r_min + dR
			elif R > self.r_max:
				dR = abs(R - self.r_max)
				R = self.r_max - dR

		bin_id = bin_of(self._radial_bins, self.n_zones+1, R)
		
		if bin_id < 0:
			print(f"bin_id out of range {bin_id} for R={R}")
			return -1
		if bin_id > self.n_zones:
			print(f"bin_id out of range {bin_id} for R={R}")
			return -1

		self._radii[N] = R

		if self.write:
			self.write_migration(f"{N},{time},{R},{bin_id}\n")
			
		return bin_id

	cpdef int get_t_int(self, double time):
		cdef int t_int
		t_int = round(time / self.dt)
		return t_int



	cpdef get_idx(self, int zone, double tform, int n=0):
		cdef int t_int = self.get_t_int(tform)
		cdef size_t N	
		cdef int N_int

		if t_int > self.n_t:
			print("time out of range %f" % tform)
			return -1
		if n > self.n_stars:
			print("n out of range %i" % n)
			return -1

		if zone > self.n_zones:
			print("zone out of range %i" % zone)
			return -1

		N_int = (t_int * self.n_zones * self.n_stars 
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




	cpdef double dR(self):
		cdef double r
		r = randn() * self.dt**0.5 * self.sigma_R
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

	def write_migration(self, s):
		if self.filename is None:
			return

		with open(self.filename, "a") as f:
			f.write(s)


	@property
	def radial_bins(self):
		return [self._radial_bins[i] for i in range(self.n_zones + 1)]


	@radial_bins.setter
	def radial_bins(self, value):
		value = _pyutils.copy_array_like_object(value)
		_pyutils.numeric_check(value, TypeError,
			"Non-numerical value detected.")
		value = sorted(value)
		self.n_zones = len(value) - 1
		if self._radial_bins is not NULL: free(self._radial_bins)
		self._radial_bins = _cutils.copy_pylist(value)


@staticmethod
cdef int bin_of(double * bins, size_t n_bins, double R) nogil:
	"""
	Find the bin index of a value R in the bins array.
	Expects n_bins to be the length of the bins array.
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
