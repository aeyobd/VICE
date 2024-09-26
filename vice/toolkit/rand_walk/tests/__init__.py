from __future__ import absolute_import

try:
    ___VICE_SETUP__
except NameError:
    __VICE_SETUP__ = False

if not __VICE_SETUP__:
    __all__ = ["test"]
    from ....testing import moduletest
    from . import rand_walk_stars
    
    @moduletest
    def test():
        """
        vice.toolkit.rand_walk_stars module test
        """
        return ["vice.toolkit.rand_walk_stars", 
            rand_walk_stars.test()
        ]
else:
    pass
