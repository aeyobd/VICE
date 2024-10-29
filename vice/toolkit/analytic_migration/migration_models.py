from __future__ import absolute_import
from ._migration_models import c_final_positions_gaussian, c_initial_positions_uniform

from math import exp, sqrt, pi, atanh
from random import Random



class initial_positions_uniform_py:
	"""
	A class to initialize the positions of particles uniformly within
	each zone. The z component is always set to zero.
	Note that the zones are assumed to be uniformly spaced in R.

	Calling
	-------
	__call__(R_i, t, n)
	Given the birth radius (zone midpoint), birth time, and particle number, returns
	the initial radius and z coordinate of the particle.
	"""
	def __init__(self, *, zone_width, R_min, R_max, seed=-1):
		# Initialize to static defaults
		"""
		Parameters
		----------
		zone_width : float
			The width of the zone in which the stars are initialized.
		R_min : float
			The minimum radius of the zone.
		R_max : float
			The maximum radius of the zone.
		seed : int
			The seed for the random number generator. If negative, use system entropy.
		"""
		if seed < 0:
			self._random = Random()
		else:
			self._random = Random(seed)
		self.zone_width = zone_width
		self.R_min = R_min
		self.R_max = R_max

	def __call__(self, R_i, t, n):

		R_low = max(self.R_min, R_i - self.zone_width/2)
		R_high = min(self.R_max, R_i + self.zone_width/2)
		R = self._random.uniform(R_low, R_high)
		z = 0.

		return R, z



class final_positions_gaussian_py:
	r"""
	A class representing the migration model described in Dubay et al.'s (2024) appendix [1]

	The model is based on the h277 simulation. 
	The change in the radius (Rfinal - Rinitial) is sampled from a normal
	distribution centred at zero. The standard deviation of the distribution
	is given by the scaling relation
	
	.. math:: \sigma = \sigma_{\rm RM 8} \left(\frac{\tau}{8\,Gyr}\right)^{\tau_{\rm power}} \left(\frac{R}{8\,kpc}\right)^{R_{\rm power}}

	where :math:`\sigma_{\rm RM 8} = 2.68`, :math:`\tau_{\rm power} = 0.33`, and :math:`R_{\rm power} = 0.61`.
	The z components are all initially zero but the final height is drawn from the
	sech2 distribution

	.. math:: {\rm PDF}(z) = \frac{1}{4 h} sech^2\left(\frac{z}{2 h}\right)

	where the scale height is given by

	..math h_z = (h_{z,s}/e^2) \exp(t/\tau_{s,z} + R_{\rm final}/R_s)

	where :math:`h_{z,s} = 0.24`, :math:`\tau_{s,z} = 7`, and :math:`R_s = 6`, and :math:`t` is the time since the star's birth.


	.. [1] Dubay et al. (2024), arXiv, 2424, 08059
	
	"""
	def __init__(self, *,
			sigma_r8 = 2.68,
			tau_power = 0.33,
			R_power = 0.61,
			hz_s = 0.24,
			tau_s_z = 7,
			R_s = 6,
			seed=-1,
		):
		if seed < 0:
			self._random = Random()
		else:
			self._random = Random(seed)
		self.sigma_r8 = sigma_r8
		self.tau_power = tau_power
		self.R_power = R_power
		self.hz_s = hz_s
		self.tau_s_z = tau_s_z
		self.R_s = R_s


	def __call__(self, R, time_birth, n, time):
		"""
		Calculates the final position of a star given its initial position and time of birth.
		If the star has not yet been born, returns -1, -1.

		Parameters
		----------
		R : float
			The initial radius of the star.
		time_birth : float
			The time the star was born.
		n : int
			The number of the star.
		time : float
			The time to calculate the final position of the star.

		Returns
		-------
		R_f : float
			The final Galactic R coordinate of the star.
		z_f : float
			The final Galactic z coordinate of the star.
		"""
		if time < time_birth:
			return -1, -1

		delta_t = time - time_birth

		sigma = self.sigma_r8 * (R / 8.)**self.R_power * (delta_t / 8.)**self.tau_power
		R_f = R + sigma * self._random.gauss()

		hz = (self.hz_s / exp(2.0)) * exp(delta_t / self.tau_s_z + R_f / self.R_s)
		randsech2 = atanh(self._random.uniform(-1, 1))
		z_f = hz * 2 * randsech2

		return R_f, z_f

class final_positions_gaussian:
	def __init__(self, *,
			sigma_r8 = 2.68,
			tau_power = 0.33,
			R_power = 0.61,
			hz_s = 0.24,
			tau_s_z = 7,
			R_s = 6,
			seed=-1,
		):
		self.__c_version = c_final_positions_gaussian(
			sigma_r8=sigma_r8,
			tau_power=tau_power,
			R_power=R_power,
			hz_s=hz_s,
			tau_s_z=tau_s_z,
			R_s=R_s,
			seed=seed,
		)

	def __call__(self, R_birth, time, n, time_end):
		return self.__c_version.call(R_birth, time, n, time_end)


class initial_positions_uniform:
	"""
	Initial positions of stars in the disk are assumed to be uniformly distributed
	in the radial direction. This is a model for initializing the positions of stars which should be a good default. The limitation is the stars are always initialized with a z coordinate of zero
	"""

	def __init__(self, *, zone_width, R_min, R_max, seed=-1):
		"""
		Initializes an initial_positions_uniform object. The radial_bins parameter
		should be exactly the same as the migration class.
		"""
		self.__c_version = c_initial_positions_uniform( 
			zone_width=zone_width,
			R_min=R_min,
			R_max=R_max,
			seed=seed,
		)


	def __call__(self, R, time, n):
		return self.__c_version.call(R, time, n)


	def __dealloc__(self):
		self.__c_version.free()

