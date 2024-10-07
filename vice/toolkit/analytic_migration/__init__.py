r"""
analytic_migration_2d : ``object``

The analytic_migration_2d object.

"""

from __future__ import absolute_import
try:
	__VICE_SETUP__
except NameError:
	__VICE_SETUP__ = False

if not __VICE_SETUP__:

	__all__ = ["analytic_migration_2d", "test"]
	from .analytic_migration_2d import analytic_migration_2d
	from .tests import test
	from . import _migration_utils, _analytic_migration_2d, _migration_models

else:
	pass

