from __future__ import absolute_import

__all__ = ["test"]

from ..rand_walk_stars import rand_walk_stars
from ....testing import moduletest, unittest
import sys


_RAD_BINS_ = [0.25 * i for i in range(81) ]
_TEST_TIMES_ = [0.05 * i for i in range(245) ] 

@moduletest
def test():
    r"""
    The random walk module test
    """
    sys.stdout.write("Testing the random walk module\n")
    return ["vice.toolkit.rand_walk.rand_walk_stars",
        [
            test_initialize(),
            test_radial_bins_setter(),
            test_call(),
        ]
    ]


@unittest
def test_initialize():
    r"""
    The initialize test
    """
    def test():
        global _TEST_

        try:
            _TEST_ = rand_walk_stars(_RAD_BINS_)
        except:
            return False
        return isinstance(_TEST_, rand_walk_stars)

    return ["vice.toolkit.rand_walk.rand_walk_stars.initialize", test]


@unittest
def test_radial_bins_setter():
    def test():
        try:
            test1 = [0.5 * i for i in range(61)]
            _TEST_.radial_bins = test1
            assert _TEST_.radial_bins == test1

            test2 = list(range(31))
            _TEST_.radial_bins = test2
            assert _TEST_.radial_bins == test2
            _TEST_.radial_bins = _RAD_BINS_
            assert _TEST_.radial_bins == _RAD_BINS_
        except:
            return False
        return True
    return ["vice.toolkit.rand_walk.rand_walk_stars.radial_bins.setter", test]


@unittest 
def test_call():

    def test_particle_birth(bin_idx, time_idx):
        x = _TEST_(bin_idx, _TEST_TIMES_[time_idx], _TEST_TIMES_[time_idx])
        if not isinstance(x, int):
            sys.stdout.write("not an int at i = %d, j = %d, x=%d\n" % (bin_idx, time_idx, x))
            sys.stdout.write(str(type(x)))
            return False

        if not (x == bin_idx):
            sys.stdout.write("init failed at i = %d, j = %d, x=%d\n" % (bin_idx, time_idx, x))
            return False

        return True


    def test_particle_later(zone, birth_idx, time_idx):
        x = _TEST_(zone, _TEST_TIMES_[birth_idx], _TEST_TIMES_[time_idx])
        if not isinstance(x, int):
            sys.stdout.write("not an int at i = %d, j = %d, k = %d\n" % (zone, birth_idx, k))
            return False

        if not (0 <= x < len(_RAD_BINS_)):
            sys.stdout.write("out of bounds at i = %d, j = %d, k = %d\n" % (zone, birth_idx, k))
            return False
        return True

    def test_particle(bin_idx, time_idx):
        if not test_particle_birth(bin_idx, time_idx):
            return False

        for k in range(time_idx+1, len(_TEST_TIMES_)):
            if not test_particle_later(bin_idx, time_idx, k):
                return False

        return True

    def test():
        try:
            status = True
            i = 0
            while (i < len(_RAD_BINS_) - 1) and status:
                j = 0
                while (j < len(_TEST_TIMES_) - 1) and status:
                    status &= test_particle(i, j)
                    j += 1
                # end for j

                i += 1
            # end for i
        except Exception as e:
            sys.stdout.write(str(e))
            sys.stdout.write("\nexception\n")

            return False
        # end try

        return status

    # end test

    return ["vice.toolkit.rand_walk.rand_walk_stars.call", test]
