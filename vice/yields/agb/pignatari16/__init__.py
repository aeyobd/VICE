r"""
Pignitari et al. (2016), Ritter et al. (2018), and Battino et al. (2019, 2021)  Asymptotic Giant Branch (AGB) star yields.

**Signature**: from vice.yields.agb import pignatari16

Importing this module will set the AGB star yield settings for all elements
to "pignatari16"

note:: This module is not imported with a simple ``import vice`` statement.

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

