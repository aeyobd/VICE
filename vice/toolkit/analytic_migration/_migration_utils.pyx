# cython: language_level = 3, boundscheck = False, wraparound = False, cdivision = True

from __future__ import absolute_import

cimport cython
from libc.math cimport NAN, sqrt, log, exp, atanh
from libc.stdlib cimport malloc, free

from ...core import _pyutils
from ...core cimport _cutils

from . cimport _migration_utils
from ._migration_utils cimport migration_star_2d, array_3d



cdef (double*, int) to_double_ptr(arr, bint sort=False):
	"""
	Converts a python numeric array-like object to a c-pointer
	Returns a double* pointer and an int length.
	If sort is true, then the array is first sorted before converting to a pointer.
	"""

	cdef double* arr_c
	cdef int n

	arr = _pyutils.copy_array_like_object(arr)
	_pyutils.numeric_check(arr, TypeError,
		"Non-numerical value detected.")
	if sort:
		arr = sorted(arr)
	n = len(arr) 
	arr_c = _cutils.copy_pylist(arr)

	return arr_c, n


cpdef double rand_sech2():
	"""
	Returns a random number drawn from a sech2 distribution.
	"""
	cdef double u = rand_range(-1, 1)
	return atanh(u)


cdef (double, double) sqrt_migration_2d(migration_star_2d* star, double time):
	"""
	A migration function that migrates a star in 2D with a square root
	time dependence, i.e. moving between the initial and final position
	as a linear function of the square root of time.
	"""
	cdef double x = (time - star.t_birth) / (star.t_end - star.t_birth)
	cdef double R = star.R_birth + (star.R_final - star.R_birth) * sqrt(x)
	cdef double z = star.z_birth + (star.z_final - star.z_birth) * sqrt(x)
	return R, z



cdef (double, double) linear_migration_2d(migration_star_2d* star, double time):
	"""
	A migration function that linearly interpolates the radius and height of a
	star in time
	"""
	cdef double x = (time - star.t_birth) / (star.t_end - star.t_birth)
	cdef double R = star.R_birth + (star.R_final - star.R_birth) * x
	cdef double z = star.z_birth + (star.z_final - star.z_birth) * x
	return R, z


cdef int bin_of(double * bins, size_t n_bins, double R):
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

	When R passes either boundary (R_min or R_max), it is set to the boundary
	value.
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

cdef class array_3d:
	"""
	A c-type 3D array of doubles to be called in cython.
	
	Attributes:
		array: A pointer to the 3D array.
		dim1: The first dimension of the array.
		dim2: The second dimension of the array.
		dim3: The third dimension of the array.
		length: The total length of the array.
	

	Methods:
		__cinit__: Initializes the 3D array with dimensions dim1 x dim2 x dim3.
		__dealloc__: Deallocates the memory used by the 3D array.
		set_value: Sets the value of the array at position (i, j, k) to value.
		get: Returns the value of the array at position (i, j, k).
		get_idx: Returns the index of the array at position (i, j, k).
		shape: Returns the shape of the 3D array.
	"""

	def __cinit__(self, int dim1, int dim2, int dim3):
		"""
		Initializes a 3D array of doubles with dimensions dim1 x dim2 x dim3.
		"""
		self.dim1 = dim1
		self.dim2 = dim2
		self.dim3 = dim3
		self.length = dim1 * dim2 * dim3

		self.array = <double*>malloc(self.length * sizeof(double))
		if self.array == NULL:
			raise MemoryError("Could not allocate memory for 3D array")


	def __dealloc__(self):
		"""
		Deallocates the memory used by the 3D array.
		"""
		self.free()

	cpdef void free(self):
		"""
		Deallocates the memory used by the 3D array.
		"""
		if self.array != NULL:
			free(self.array)
			self.array = NULL


	cpdef void set_value(self, int i, int j, int k, double value):
		"""
		Sets the value of the array at position (i, j, k) to value.
		"""
		idx = self.get_idx(i, j, k)
		if self.array == NULL:
			raise MemoryError("Array is not allocated")
		self.array[idx] = value


	cpdef double get(self, int i, int j, int k):
		"""
		Returns the value of the array at position (i, j, k).
		"""
		idx = self.get_idx(i, j, k)
		if self.array == NULL:
			raise MemoryError("Array is not allocated")
		return self.array[idx]


	cpdef int get_idx(self, int i, int j, int k):
		"""
		Returns the index of the array at position (i, j, k).
		"""
		if (i < 0) or (i >= self.dim1):
			raise IndexError("Index i out of bounds")
		if (j < 0) or (j >= self.dim2):
			raise IndexError("Index j out of bounds")
		if (k < 0) or (k >= self.dim3):
			raise IndexError("Index k out of bounds")

		return i * self.dim2 * self.dim3 + j * self.dim3 + k

	def __getitem__(self, tuple idx):
		"""
		Returns the value of the array at position (i, j, k).
		"""
		if len(idx) != 3:
			raise IndexError("Index must be a tuple of length 3")
		return self.get(idx[0], idx[1], idx[2])

	def __setitem__(self, tuple idx, double value):
		"""
		Sets the value of the array at position (i, j, k) to value.
		"""
		if len(idx) != 3:
			raise IndexError("Index must be a tuple of length 3")
		self.set_value(idx[0], idx[1], idx[2], value)

	cpdef (int, int, int) shape(self):
		"""
		Returns the shape of the 3D array.
		"""
		return self.dim1, self.dim2, self.dim3


def sqrt_migration_2d_py(star_dict, time):
	"""
	A migration function that migrates a star in 2D with a square root
	time dependence, i.e. moving between the initial and final position
	as a linear function of the square root of time.
	"""
	star = migration_star_2d(t_birth=star_dict["t_birth"], t_end=star_dict["t_end"],
		R_birth=star_dict["R_birth"], R_final=star_dict["R_final"],
		z_birth=star_dict["z_birth"], z_final=star_dict["z_final"])

	result = sqrt_migration_2d(&star, time)
	return result


def linear_migration_2d_py(star_dict, double time):
	"""
	A migration function that linearly interpolates the radius and height of a
	star in time
	"""
	star = migration_star_2d(t_birth=star_dict["t_birth"], t_end=star_dict["t_end"],
		R_birth=star_dict["R_birth"], R_final=star_dict["R_final"],
		z_birth=star_dict["z_birth"], z_final=star_dict["z_final"])

	result = linear_migration_2d(&star, time)

	return result


def bin_of_py(bins, double R):
	"""
	Efficient binary search for the bin index of a given radius R. 

	The array `bins` must be sorted and of length `n_bins`. Returns the
	index of the bin that contains the radius R (left-closed, right-open).

	If R is outside the range of the bins, returns -1.
	"""
	bins_c, n_bins = to_double_ptr(bins, sort=True)
	return bin_of(bins_c, n_bins, R)


def reflect_boundary_py(R, R_min, R_max):
	"""
	Reflects the radius R off of the boundaries R_min and R_max.
	"""
	return reflect_boundary(R, R_min, R_max)


def absorb_boundary_py(R, R_min, R_max):
	"""
	Absorbs the radius R into the boundaries R_min and R_max.

	When R passes either boundary (R_min or R_max), it is set to the boundary
	value.
	"""
	return absorb_boundary(R, R_min, R_max)

def no_boundary_py(R, R_min, R_max):
	"""
	Does nothing to the radius R.
	"""
	return no_boundary(R, R_min, R_max)
