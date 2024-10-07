from __future__ import absolute_import
from ._migration_models import c_final_positions_gaussian, c_initial_positions_uniform


class final_positions_gaussian:
	def __init__(self, 
		sigma_r8 = 2.68,
		tau_power = 0.33,
		R_power = 0.61,
		hz_s = 0.24,
		tau_s_z = 7,
		R_s = 6,
			  ):
		self.__c_version = c_final_positions_gaussian(
			sigma_r8=sigma_r8,
			tau_power=tau_power,
			R_power=R_power,
			hz_s=hz_s,  
			tau_s_z=tau_s_z,
			R_s=R_s,
			)

	def __call__(self, R_birth, delta_t, n):
		return self.__c_version.call(R_birth, delta_t, n)


class initial_positions_uniform:
	"""
	Initial positions of stars in the disk are assumed to be uniformly distributed
	in the radial direction. This is a model for initializing the positions of stars which should be a good default. The limitation is the stars are always initialized with a z coordinate of zero
	"""

	def __init__(self, radial_bins):
		"""
		Initializes an initial_positions_uniform object. The radial_bins parameter
		should be exactly the same as the migration class.
		"""
		n_zones = len(radial_bins) - 1
		self.__c_version = c_initial_positions_uniform(
				radial_bins, n_zones
			)

	def __call__(self, zone, time, n):
		return self.__c_version.call(zone, time, n)


	def __dealloc__(self):
		self.__c_version.free()

