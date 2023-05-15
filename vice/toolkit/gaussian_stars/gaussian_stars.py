from __future__ import absolute_import
from ._gaussian_stars import c_gaussian_stars


class gaussian_stars:

	r"""
	A stellar migration scheme based on gaussian pertubations of stars at 
	each timestep

	**Signature**: vice.toolkit.gaussian_stars.gaussian_stars(radial_bins, N = 1e5,
	mode = "diffusion")

	Parameters
	----------
	radial_bins : array-like [elements must be positive real numbers]
		The bins in galactocentric radius in kpc describing the disk model.
		This must extend from 0 to at least 20. Need not be sorted in any
		way. Will be stored as an attribute.
	N : int [default : 1e5]
		An approximate number of star particles from the hydrodynamical
	mode : str [case-insensitive] or ``None`` [default : "diffusion"]
		The attribute 'mode', initialized via keyword argument.
	Currently only implements the diffusion mode

	Attributes
	----------
	radial_bins : list
		The bins in galactocentric radius in kpc describing the disk model.
	analog_data : dataframe
		The raw star particle data from the hydrodynamical simulation.
	analog_index : int
		The index of the star particle acting as the current analog. -1 if the
		analog has not yet been set (see note below under `Calling`_).
	Calling
	-------
	As all stellar migration prescriptions must, this object can be called
	with three parameters, in the following order:

		zone : int
			The zone index of formation of the stellar population. Must be
			non-negative.
		tform : float
			The time of formation of the stellar population in Gyr.
		time : float
			The simulation time in Gyr (i.e. not the age of the star particle).

        n: int
            The id of the star particle
	"""


	def __init__(self, rad_bins, N = 1e5, mode = "diffusion"):
		self.__c_version = c_gaussian_stars(rad_bins, N = N, mode = mode)


	def __call__(self, zone, tform, time):
		return self.__c_version.__call__(zone, tform, time)


	def __enter__(self):
		# Opens a with statement
		return self


	def __exit__(self, exc_type, exc_value, exc_tb):
		# Raises all exceptions inside a with statement
		return exc_value is None

	def __object_address(self):
		r"""
		Returns the memory address of the HYDRODISKSTARS object in C. For
		internal usage only; usage of this function by the user is strongly
		discouraged.
		"""
		return self.__c_version.object_address()


	@property
	def radial_bins(self):
		r"""
		Type : list [elements are positive real numbers]

		The bins in galactocentric radius in kpc describing the disk model.
		Must extend from 0 to at least 20 kpc. Need not be sorted in any way
		when assigned.
		"""
		return self.__c_version.radial_bins

	@radial_bins.setter
	def radial_bins(self, value):
		self.__c_version.radial_bins = value


	@property
	def idx(self):
		return self.__c_version.idx


