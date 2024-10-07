from __future__ import absolute_import
from . import _migration_utils
from . import _migration_models
from ._analytic_migration_2d import c_analytic_migration_2d
from .migration_models import initial_positions_uniform, final_positions_gaussian



class analytic_migration_2d:
	r"""
	A generalized, fast function migration for vice.
	Given functions which populate the initial and final positions in (R, z)
	of each star and a functional form to interpolate between the endpoints,
	this class implements the resulting migration.

	**Signature**: vice.toolkit.analytic_migration.analytic_migration_2d(
		radial_bins, 
		n_stars = 1,
		dt = 0.01,
		t_end = 13.5
	)

	Parameters
	----------
	initial_positions : function(birth_radius, time, n)
            Likely never needs changed, initializes a star to be within the zone

	final_positions : function(birth_radius, time_birth, n, time_end)
            Returns the final position of a star given its birth radius and time. 
            May be any function returning (R, z) as floats.

        migration_mode : str [default : "sqrt"]
            The functional form of the migration. Options are:
            - "linear" : linear migration in R and z
            - "sqrt" : sqrt(R) migration in R and z

	radial_bins : array-like [elements must be positive real numbers]
		The bins in galactocentric radius in kpc describing the disk model.
		This must extend from 0 to at least 20. Need not be sorted in any way.
		Will be stored as an attribute.
	n_stars : int [default : 1]
		The number of stars to create during each timestep
	dt : float [default : 0.01]
		The simulation timestep. This should really be set
	t_end : float [Default]
	tau_R: float [default : 8]
		Migration timescale in Gyr
	sigma_R: float [default : 1.27]
		Migration distance scale in kpc
	boundary_conditions: str [default : "reflect"]
	filename : str [default : None]
		The filename to write the migration to. If not set, than the migration
		cannot be written.
	

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


	def __init__(self, rad_bins, 
				filename=None, 
				initial_positions=None, final_positions=None,
				boundary_conditions="reflect", migration_mode="sqrt",
				n_stars=2, dt=0.02, t_end=13.5

		):
		if initial_positions is None:
			zone_width = rad_bins[1] - rad_bins[0]

			initial_positions = initial_positions_uniform(
				zone_width = zone_width,
				R_min = min(rad_bins),
				R_max = max(rad_bins),
			)

		if final_positions is None:
			final_positions = final_positions_gaussian()
		

		self.__c_version = c_analytic_migration_2d(
			rad_bins, 
			filename = filename, 
			initial_positions = initial_positions,
			final_positions = final_positions,
			migration_mode = migration_mode,
			boundary_conditions = boundary_conditions, 
			n_stars = n_stars,
			dt = dt,
			t_end = t_end,
		)


	def __call__(self, zone, tform, time, n=0):
		val = self.__c_version(zone, tform, time, n=n)
		if val < -1:
			raise ValueError("could not calculate bin")

		return val

	def __dealloc__(self):
		self.__c_version.dealloc()

	def get_star(self, zone, tint, n):
		"""
		Returns a dictionary of the stars initial and final positions given the 
		stars birth zone, integer formation time, and number (in bin).
		"""
		return self.__c_version.get_star(zone, tint, n)


	def write_initial_final(self):
		"""
		Writes the initial and final positions of each star to a file to the
		given filename Because the migration form is analytic, the initial and
		final positions are sufficient to characterize the migration of each
		particle, so this allows for the migration information to be stored
		without writing the particle positions for every timestep.
		"""
		self.__c_version.write_initial_final()


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
	def write(self):
		return self.__c_version.write

	@write.setter
	def write(self, a):
		self.__c_version.write = a
	
	@property
	def n_zones(self):
		return self.__c_version.get_n_zones()

