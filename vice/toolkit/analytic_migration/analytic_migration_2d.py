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

	.. versionadded:: 1.4.0.dev1

	Parameters
	----------
	initial_positions : `function(birth_radius: float, time: float, n: int): tuple(float)`
            Likely never needs changed, initializes a star to be within the zone.
	    Defaults to `initial_positions_uniform` which uniformly samples R_birth within each zone.
	    Should be a function accepting the birth radius, time and n (the star number) of the zone,
	    returning the birth position as (R, z) in kpc in Galactocentric coordinates.

	final_positions : `function(birth_radius: float, time_birth: float, n: int, time_end: float)`
	    The function returning the final position of each star.
	    Defaults to `final_positions_gaussian` which samples the final
	    position from a Gaussian distribution.

	    Should be a function accepting the birth radius, time of birth, n
	    (the star number) of the zone, and the final time of the simulation, returning
	    a tuple of the final position as (R, z) in kpc in Galactocentric coordinates.

        migration_mode : ``str`` [default : "sqrt"]
            The functional form of the migration. Options are:
            - "linear" : linear migration in R and z
            - "sqrt" : sqrt(R) migration in R and z

	boundary_conditions: str [default : "reflect"]
		The boundary conditions to apply if a star would migrate outside the radial bins.
		Options are:
		- "reflect" : reflect the star back into the disk
		- "absorb" : star becomes stuck at the boundary
		- "reflect_final" : reflects the final position of the star
		- "absorb_final" : absorbs the final position of the star, so
		  the final position becomes the boundary. 

	radial_bins : array-like [elements must be positive real numbers]
		The bins in galactocentric radius in kpc describing the disk model.
		This must extend from 0 to at least 20. 
		Needs to match the multizone model.

	n_stars : int [default : 1]
		The number of stars to create during each timestep
		Should match the multizone instance.

	dt : `float` [default : 0.01]
		The simulation timestep in Gyr. 
		Should match the multizone model.

	t_end : `float` [default : 13.5]
		The end time of the simulation in Gyr.
		Should match the model.
		
	filename : str [default : None]
		The filename to write the migration to. If not set, than the migration
		will not be written to a file even if `write` is set.

	initial_file_filename : `str` [default : None]
		If set, then the initial and final posititions of each particle
		is written to the given filename. If None, then this information
		is not written.

	verbose : `bool` [default : False]
		If true, then prints some status messages as the class is initialized.

	Attributes
	----------
	radial_bins : `list`
		The bins in galactocentric radius in kpc describing the disk model.

	write : `bool`
		Whether or not to write the migration data to a file. If True, then the
		particle data is written each time the migration is called. 

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

	Returns an integer for the current zone of the star particle.
	"""


	def __init__(
			self, rad_bins, 
			filename=None, 
			initial_positions=None, 
			final_positions=None,
			boundary_conditions="reflect", 
			migration_mode="sqrt",
			n_stars=2, 
			dt=0.02, 
			t_end=13.5,
	      		initial_final_filename = None,
			verbose = False,

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

		self.migration_mode = migration_mode
		self.boundary_conditions = boundary_conditions
		self.initial_positions = initial_positions
		self.final_positions = final_positions
		

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
			initial_final_filename = initial_final_filename,
			verbose = verbose,
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



	def __str__(self):
		attrs = {
			"n_zones": self.n_zones,
			"write": self.write, 
			"filename": self.filename,
			"migration_mode": self.migration_mode,
			"boundary_conditions": self.boundary_conditions,
			"initial_positions": self.initial_positions,
			"final_positions": self.final_positions,
			"verbose": self.verbose,
			"radial_bins": sprint_zones(self.radial_bins),
		}

		s = "vice.toolkit.analytic_migration.analytic_migration_2d{\n"
		for i in attrs.keys():
			s += "    %s " % (i)
			for j in range(25 - len(i)):
				s += "-"

			s += "> %s\n" % str(attrs[i])

		s += "}"

		return s

	def __repr__(self):
		return self.__str__()

	@property
	def filename(self):
		"""The filename to write the migration data to if `write` is set"""
		return self.__c_version.filename

	@property
	def verbose(self):
		return self.__c_version.verbose

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
	def write(self, value):
		self.__c_version.write = value
	
	@property
	def n_zones(self):
		return self.__c_version.get_n_zones()


def sprint_zones(zones, precision=2):
	"""
	Prints the zones in a readable format.
	"""

	s = "["

	if len(zones) > 6:
		for zone in zones[:3]:
			s += "%f, " % round(zone, precision)

		s += "... , "

		for zone in zones[-3:]:
			s += "%f, " % round(zone, precision)

	else:
		for zone in zones:
			s += "%f, " % round(zone, precision)
	
	# remove trailing comma
	s = s[:-2]
	s += "]"
	return s
