from __future__ import absolute_import

__all__ = ["test"]

from ..analytic_migration_2d import analytic_migration_2d
from ....testing import moduletest, unittest
import sys


_DT_ = 0.1
_DR_ = 0.25
_RAD_BINS_ = [_DR_ *  i for i in range(81) ]
_TEST_TIMES_ = [0.05 * i for i in range(240) ] 
_BIRTH_TIMES_ = [ _DT_ * i for i in range(120)]

@moduletest
def test():
	r"""
	The random walk module test
	"""
	return ["vice.toolkit.analytic_migration_2d.analytic_migration_2d",
		[
			test_initialize(),
			test_radial_bins_setter(),
			test_call(),
			test_sqrt_migration(),
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
			_TEST_ = analytic_migration_2d(_RAD_BINS_, dt=_DT_)
		except:
			return False
		return isinstance(_TEST_, analytic_migration_2d)

	return ["vice.toolkit.analytic_migration_2d.analytic_migration_2d.initialize", test]


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
		except Exception as e:
			sys.stdout.write("radial_bins_setter failed\n")
			sys.stdout.write(str(e))
			return False
		return True
	return ["vice.toolkit.analytic_migration_2d.analytic_migration_2d.radial_bins.setter", test]



def test_particle_birth(bin_idx, time_idx):
	t = _BIRTH_TIMES_[time_idx]
	x = _TEST_(bin_idx, t, t)
	if not isinstance(x, int):
		sys.stdout.write("migration returned non-integer at bin_idx=%d, t_birth_idx = %d, t_idx = %d\n" % (bin_idx, time_idx, time_idx))
		sys.stdout.write(str(type(x)))
		return False

	if not (x == bin_idx):
		sys.stdout.write("particle not born in correct bin, got %d" % x)
		sys.stdout.write("bin_idx = %d, time_idx = %d, x = %d\n" % (bin_idx, time_idx, x))
		return False

	return True


def test_particle_later(zone, birth_idx, time_idx):
	x = _TEST_(zone, _BIRTH_TIMES_[birth_idx], _BIRTH_TIMES_[time_idx])
	if not isinstance(x, int):
		sys.stdout.write("migration returned non-integer at zone_birth=%d, t_birth_idx = %d, t_idx = %d\n" % (zone, birth_idx, time_idx))
		return False

	if not (0 <= x < len(_RAD_BINS_)):
		sys.stdout.write("migration returned star out of bounds at zone_birth=%d, t_birth_idx = %d, t_idx = %d\n" % (zone, birth_idx, time_idx))
		sys.stdout.write("binid = %d\n" % x)
		return False
	return True

def test_particle(bin_idx, time_idx):
	if not test_particle_birth(bin_idx, time_idx):
		return False

	for k in range(time_idx+1, len(_BIRTH_TIMES_)):
		if not test_particle_later(bin_idx, time_idx, k):
			return False

	return True

@unittest 
def test_call():
	def test():
		try:
			status = True
			i = 0
			while (i < len(_RAD_BINS_) - 1) and status:
				j = 0
				while (j < len(_BIRTH_TIMES_) - 1) and status:
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

	return ["vice.toolkit.analytic_migration_2d.analytic_migration_2d.call", test]




@unittest 
def test_sqrt_migration():
	def test():
		zone_birth = 40
		t_idx_birth = 100
		n = 1
		
		star = _TEST_._analytic_migration_2d__c_version.get_star(zone_birth, t_idx_birth, n)

		R_birth = star["R_birth"]
		R_final = star["R_final"]
		t_birth = star["t_birth"]
		t_end = star["t_end"]

		for i in range(t_idx_birth, len(_BIRTH_TIMES_)):
			time = _BIRTH_TIMES_[i]
			delta_t = time - t_birth

			R_expected = R_birth + (R_final - R_birth) * (delta_t / (t_end - t_birth))**0.5
			R_actual = _RAD_BINS_[_TEST_(zone_birth, t_birth, time, n)]

			if not (abs(R_expected - R_actual) < _DR_):
				sys.stdout.write("R_expected = %f, R_actual = %f\n" % (R_expected, R_actual))
				sys.stdout.write("zone_birth = %d, t_birth = %f, time = %f\n" % (zone_birth, t_birth, time))
				return False
		return True

	return ["vice.toolkit.analytic_migration_2d.analytic_migration_2d.sqrt_migration", test]

