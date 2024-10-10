r"""
Pignitari et al. (2016), Ritter et al. (2018), and Battino et al. (2019, 2021)  Asymptotic Giant Branch (AGB) star yields.

**Signature**: from vice.yields.agb import pignatari16

Importing this module will set the AGB star yield settings for all elements
to "pignatari16". AGB star yields will then be calculated as linear interpolations
over the masses and metallicities of stars in these tables.
This module contains the recommended NuGrid yields, i.e.
- Z = [0.02, 0.01, 0.006, 0.001, 0.0001] for M = [1.  ,  1.65,  2.  ,  3.  ,  4.  ,  5.  ,  6.  ,  7. ] Msun from Ritter et al. (2018) [1]_
- Z = [0.02, 0.01] for M = 2 and 3 solar masses updates from Battino et al. (2019) [2]_
- Z = 0.001 updates for M = 2 and 3 solar masses from Battino et al. (2021) [3]_

Note that Pignatari et al. (2016) is the first NuGrid paper, but Ritter et al. (2018) both updates the yields (slightly) and expands the grid of masses and metallicities, so we do not use the Pignatari et al. (2016) [4]_ tables directly here.

note:: This module is not imported with a simple ``import vice`` statement.


.. [1] Ritter et al. (2018), MNRAS 480, 538
.. [2] Battino et al. (2019), MNRAS 489, 1082
.. [3] Battino et al. (2021), Universe 7, 25
.. [4] Pignatari et al. (2016), ApJS 225, 24

"""

from __future__ import absolute_import
try:
	__VICE_SETUP__
except NameError:
	__VICE_SETUP__ = False
try:
	__VICE_DOCS__
except NameError:
	__VICE_DOCS__ = False

if not __VICE_SETUP__:

	from .. import settings as __settings
	if not __VICE_DOCS__:
		for i in __settings.keys():
			__settings[i] = "pignatari16"
	else: pass

else:
	pass

