r"""
rand_walk_stars : ``object``

The gaussian/random walk migration approximation object

"""

from __future__ import absolute_import
try:
	__VICE_SETUP__
except NameError:
	__VICE_SETUP__ = False

if not __VICE_SETUP__:

	__all__ = ["rand_walk_stars"]
	from .rand_walk_stars import rand_walk_stars

else:
	pass

