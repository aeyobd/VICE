from __future__ import absolute_import
from ._gaussian_stars import c_gaussian_stars
import numpy as np


class gaussian_stars:

	r"""
	A stellar migration scheme based on gaussian pertubations of stars at 
	each timestep

	**Signature**: vice.toolkit.gaussian_stars.gaussian_stars(
		radial_bins, 
		n_stars = 1,
		dt = 0.01,
		t_end = 13.5
	)

	Parameters
	----------
	radial_bins : array-like [elements must be positive real numbers]
		The bins in galactocentric radius in kpc describing the disk model.
		This must extend from 0 to at least 20. Need not be sorted in any
		way. Will be stored as an attribute.
	n_stars : int [default : 1]
		The number of stars to create during each timestep
	dt : float [default : 0.01]
		The simulation timestep. This should really be set
	t_end : float [Default]
	tau_R: float [default : 8]
		Migration timescale in Gyr
	sigma_R: float [default : 3.6]
		Migration distance scale in kpc
	

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


	def __init__(self, rad_bins, name="example", n_stars=1, dt=0.01, t_end=13.5, tau_R=8,
			  sigma_R=3.6):
		if isinstance(rad_bins, list):
			rad_bins = np.array(rad_bins)
		self.__c_version = c_gaussian_stars(rad_bins, n_stars=n_stars, 
			  dt=dt, t_end=t_end, name=name)


	def __call__(self, zone, tform, time, n=0):
		return self.__c_version.__call__(zone, tform, time, n=n)


	def __enter__(self):
		# Opens a with statement
		return self


	def __exit__(self, exc_type, exc_value, exc_tb):
		# Raises all exceptions inside a with statement
		return exc_value is None



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

	@property
	def mode(self):
		return None

	@property
	def write(self):
		return self.__c_version.write

	@write.setter
	def write(self, a):
		self.__c_version.write = a
	




