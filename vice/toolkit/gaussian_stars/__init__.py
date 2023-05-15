r"""
gaussian_stars : ``object``

The gaussian migration approximation object

"""

from __future__ import absolute_import
try:
	__VICE_SETUP__
except NameError:
	__VICE_SETUP__ = False

if not __VICE_SETUP__:

	__all__ = ["gaussian_stars"]
	from .gaussian_stars import gaussian_stars

else:
	pass

