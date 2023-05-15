# cython: language_level = 3, boundscheck = False

from __future__ import absolute_import
from ..._globals import _VERSION_ERROR_
from ..._globals import _DIRECTORY_
from ..._globals import ScienceWarning
from ...core import _pyutils
from ...core.dataframe import base as dataframe
import numbers
import sys
if sys.version_info[:2] == (2, 7):
	strcomp = basestring
elif sys.version_info[:2] >= (3, 5):
	strcomp = str
else:
	_VERSION_ERROR_()
# from libc.stdlib cimport srand
from libc.stdlib cimport malloc, free
from libc.string cimport strcpy, strcmp, strlen
from ...core._cutils cimport copy_pylist
from ...core._cutils cimport set_string
# from . cimport _gaussian_stars



cdef class c_gaussian_stars:

	"""
	The C-implementation of the gaussian_stars object. See python version for
	documentation.
	"""

	def __cinit__(self, radbins, N = 1e5, mode = "diffusion"):
		# allocate memory for hydrodiskstars object in C and import the data
		self._gns = _gaussian_stars.gaussian_stars_initialize()

		if (isinstance(N, numbers.Number)) and (N % 1 == 0):
			_gaussian_stars.seed_random()
		else:
			raise TypeError("Keyword arg 'N' must be an integer.")

		self.radial_bins = radbins


	def __init__(self, radbins, N = 1e5, mode = "diffusion"):
		self._analog_idx = -1l


	def __dealloc__(self):
		_gaussian_stars.gaussian_stars_free(self._gns)


	def __call__(self, zone, tform, time):
		if not isinstance(zone, int):
			raise TypeError("Zone must be of type int. Got: %s" % (type(zone)))

		if not (0 <= zone < self._gns[0].n_rad_bins):
			raise ValueError("Zone out of range: %d" % (zone))

		if not (isinstance(tform, numbers.Number) and
				isinstance(time, numbers.Number)):
			raise TypeError("""Time parameters must be numerical \
values. Got: (%s, %s)""" % (type(tform), type(time)))

		birth_radius = (self._gns[0].rad_bins[zone] +
			self._gns[0].rad_bins[zone + 1]) / 2

		if tform == time:
			self._analog_idx = (i * (self.n_zones * self.n_tracers) +
                j * self.n_tracers + k)

			return zone

        bin_ = int(_gaussian_stars.calczone_gaussian_stars(self._gns[0],
                    self.analog_index))

		if bin_ != -1:
			return bin_
		else:
			raise ValueError("""\
Radius out of bin range. Relevant information:
Analog ID: %d
Zone of formation: %d
Time of formation: %.4e Gyr
Time in simulation: %.4e Gyr""" % (self.analog_data["id"][self.analog_index],
						zone, tform, time))


	def object_address(self):
		"""
		Returns the memory address of the GAUSSIAN_STARS object in C.
		"""
		return <long> (<void *> self._gns)


	@property
	def radial_bins(self):
		# docstring in python version
		return [self._gns[0].rad_bins[i] for i in range(
			self._gns[0].n_rad_bins + 1)]


	@radial_bins.setter
	def radial_bins(self, value):
		value = _pyutils.copy_array_like_object(value)

		_pyutils.numeric_check(value, TypeError,
			"Non-numerical value detected.")

		value = sorted(value)

		if not value[-1] >= 20: 
			raise ValueError("Maximum radius must be at least 20 kpc. Got: %g" 
					% (value[-1]))
		if value[0] != 0: 
			raise ValueError("Minimum radius must be zero. Got: %g kpc." 
					% (value[0]))

		self._gns[0].n_rad_bins = len(value) - 1

		if self._gns[0].rad_bins is not NULL: 
			free(self._gns[0].rad_bins)

		self._gns[0].rad_bins = copy_pylist(value)



	@property
	def analog_index(self):
		# docstring in python version
		return self._analog_idx



