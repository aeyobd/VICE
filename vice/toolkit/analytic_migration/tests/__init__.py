from __future__ import absolute_import

try:
    ___VICE_SETUP__
except NameError:
    __VICE_SETUP__ = False

if not __VICE_SETUP__:
    __all__ = ["test"]
    from ....testing import moduletest
    from . import analytic_migration_2d
    
    @moduletest
    def test():
        """
        vice.toolkit.analytic_migration_2d module test
        """
        return ["vice.toolkit.analytic_migration_2d", 
            analytic_migration_2d.test()
        ]
else:
    pass
