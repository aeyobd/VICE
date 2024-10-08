from __future__ import absolute_import

from ....testing import moduletest, unittest

from .._migration_utils import rand_sech2, array_3d
from .._migration_utils import bin_of, migration_sqrt, migration_linear
from .._migration_utils import migration_sqrt_z, migration_linear_z
from .._migration_utils import reflect_boundary, absorb_boundary, no_boundary


from math import exp, isnan


@moduletest
def test():
	"""
	The migration utils module test
	"""

	return ["vice.toolkit.analytic_migration_2d._migration_utils",
		[
			test_rand_sec2(),
			test_sqrt_migration_2d(),
			test_linear_migration_2d(),
			test_bin_of(),
			test_array_3d(),
			test_reflect_boundary(),
			test_absorb_boundary(),
			test_no_boundary(),
		]
	]

@unittest 
def test_bin_of():
	def test():
		try:
			bins = [1, 2, 3]
			assert bin_of(bins, 1.5) == 0
			assert bin_of(bins, 1) == 0
			assert bin_of(bins, 2.9) == 1
			assert bin_of(bins, 3.02) == -1
			assert bin_of(bins, 0.9) == -1
		except Exception as e:
			print(e)
			return False
		return True

	return ["vice.toolkit.analytic_migration_2d._migration_utils.bin_of", test]



@unittest
def test_array_3d():
	def test():
		try:
			arr = array_3d(1,2,3)
			arr = array_3d(3, 6, 10)
			arr[0, 1, 2] = 1
			assert arr[0, 1, 2] == 1, f"arr[0, 1, 2] == {arr[0, 1, 2]} != 1"
			val = 3.1415926
			arr[2, 5, 4] = val
			assert arr[2, 5, 4] == val, f"arr[2, 5, 4] = {arr[2, 5, 4]} != {val}"
		except Exception as e:
			print(e)
			return False

		return True
	

	return ["vice.toolkit.analytic_migration_2d._migration_utils.array_3d", test]


@unittest
def test_rand_sec2():
	def generate_samples(N):
		return [rand_sech2() for i in range(N)]

	def histogram(samples, bins):
		"""Returns the pdf of the samples using the provided bins"""
		hist = [0. for i in range(len(bins) - 1)]
		for sample in samples:
			for i in range(len(bins) - 1):
				if bins[i] <= sample < bins[i + 1]:
					hist[i] += 1
		binwidths = [bins[i + 1] - bins[i] for i in range(len(bins) - 1)]

		hist_pdf = [hist[i] / binwidths[i] / len(samples) for i in range(len(hist))]
		return hist_pdf, hist

	def pdf(x):
		return 2 / (exp(x) + exp(-x))**2


	def test():
		try:
			N = 10000
			samples = [rand_sech2() for i in range(N)]
			bins = [i / 10. for i in range(-20, 20)]

			hist_pdf, counts = histogram(samples, bins)
			bin_mids = [(bins[i] + bins[i + 1]) / 2 for i in range(len(bins) - 1)]
			chi2_max = 5

			chi2 = 0.
			expected = [pdf(x) for x in bin_mids]
			for i in range(len(bins) - 1):
				chi2 += (hist_pdf[i] - expected[i])**2 / (expected[i] / counts[i]**0.5 ) ** 2

			chi2_reduced = chi2 / len(bins)
			assert chi2_reduced < chi2_max, "reduced chi2 = %f" % chi2_reduced

		except Exception as e:
			print(e)
			return False

		return True

	return ["vice.toolkit.analytic_migration_2d._migration_utils.rand_sech2", test]


@unittest 
def test_sqrt_migration_2d():
	def test():
		try:
			star = {
					"t_birth": 5,
					"t_final": 10, 
					"R_birth": 1,
					"R_final": 2,
					"z_birth": 0,
					"z_final": -0.5,
					}

			R = migration_sqrt(star, 5)
			assert R == 1
			z = migration_sqrt_z(star, 5)
			assert z == 0

			R = migration_sqrt(star, 10)
			z = migration_sqrt_z(star, 10)
			assert R == 2
			assert z == -0.5

			
			R = migration_sqrt(star, 6.25)
			z = migration_sqrt_z(star, 6.25)
			assert R == 1.5
			assert z == -0.25

		except Exception as e:
			print(e)
			return False

		return True

	return ["vice.toolkit.analytic_migration_2d._migration_utils.sqrt_migration_2d", test]



@unittest
def test_linear_migration_2d():
	def test():
		try:
			star = {
					"t_birth": 5,
					"t_final": 10, 
					"R_birth": 1,
					"R_final": 2,
					"z_birth": 0,
					"z_final": -0.5,
					}

			R = migration_linear(star, 5)
			z = migration_linear_z(star, 5)

			assert R == 1
			assert z == 0

			R = migration_linear(star, 10)
			z = migration_linear_z(star, 10)
			assert R == 2
			assert z == -0.5

			R = migration_linear(star, 6.25)
			z = migration_linear_z(star, 6.25)
			assert R == 1.25
			assert z == -0.125
		except Exception as e:
			print(e)
			return False
		return True

	return ["vice.toolkit.analytic_migration_2d._migration_utils.linear_migration_2d", test]



@unittest
def test_absorb_boundary():
	def test():
		try:
			R_min = 3.4
			R_max = 5

			assert absorb_boundary(-2.32, R_min, R_max) == R_min
			assert absorb_boundary(3.3, R_min, R_max) == R_min
			assert absorb_boundary(3.4, R_min, R_max) == 3.4
			assert absorb_boundary(4.56, R_min, R_max) == 4.56
			assert absorb_boundary(6.2, R_min, R_max) == 5

		except Exception as e:
			print(e)
			return False

		return True

	return ["vice.toolkit.analytic_migration_2d._migration_utils.absorb_boundary", test]



@unittest
def test_reflect_boundary():
	def test():
		try:
			R_min = 2.5
			R_max = 5

			assert reflect_boundary(2, R_min, R_max) == 3
			assert reflect_boundary(3.14, R_min, R_max) == 3.14
			assert reflect_boundary(4.56, R_min, R_max) == 4.56
			assert reflect_boundary(R_max, R_min, R_max) == 5

		except Exception as e:
			print(e)
			return False

		return True

	return ["vice.toolkit.analytic_migration_2d._migration_utils.reflect_boundary", test]


@unittest
def test_no_boundary():
	def test():
		try:
			R_min = 2.5
			R_max = 5

			assert no_boundary(3.14, R_min, R_max) == 3.14
			assert no_boundary(4.56, R_min, R_max) == 4.56
			# TODO: add assertRaises tests here

		except Exception as e:
			print(e)
			return False

		return True

	return ["vice.toolkit.analytic_migration_2d._migration_utils.no_boundary", test]
