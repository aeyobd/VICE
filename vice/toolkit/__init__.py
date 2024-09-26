r"""
VICE Toolkit : General utilities to maximize VICE's computational power and
user-friendliness.

.. versionadded:: 1.2.0

Contents
--------
hydrodisk : <module>
	Utilities for simulating migration in disk galaxies.
gaussian: <module>
	Utilities for a gaussian migration scheme for disk galaxies.
rand_walk: <module>
	Utilities for a random walk migration scheme for disk galaxies.
interpolation : <module>
	Interpolation schema.
J21_sf_law : <module>
	The observationally motivated star formation law from Johnson et al. (2021)
	[1]_, intended for use as the attribute ``tau_star`` of the ``singlezone``
	class.

.. [1] Johnson et al. (2021), MNRAS, 508, 4484
"""

from __future__ import absolute_import
try:
	__VICE_SETUP__
except NameError:
	__VICE_SETUP__ = False

if not __VICE_SETUP__:

	__all__ = ["hydrodisk", "analytic_migration", "rand_walk", "interpolation", "J21_sf_law", "test"]
	from ..testing import moduletest
	from .J21_sf_law import J21_sf_law
	from . import interpolation
	from . import hydrodisk
	from . import analytic_migration
	from . import rand_walk

	@moduletest
	def test():
		r"""
		vice.toolkit module test
		"""
		return ["vice.toolkit",
			[
				hydrodisk.test(run = False),
				interpolation.test(run = False)
			]
		]

else:
	pass
