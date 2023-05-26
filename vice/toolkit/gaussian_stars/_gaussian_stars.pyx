# cython: language_level = 3, boundscheck = False

from __future__ import absolute_import
from ..._globals import _DIRECTORY_
from ...core import _pyutils
from ...core.dataframe import base as dataframe
import os


import numpy as np


from . cimport _gaussian_stars



cdef class c_gaussian_stars:
	"""
	The C-implementation of the gaussian_stars object. See python version for
	documentation.
	"""


	def __cinit__(self, radbins, int n_stars=2, 
				  double dt=0.01, double t_end=13.5, name="example"):
		self.n_bins = len(radbins) - 1
		self._radial_bins = radbins
		self.n_t = np.round(t_end/dt)
		self.n_stars = n_stars
		self.dt = dt

		cdef i_test = self.n_t * self.n_stars * self.n_bins
		if i_test < 0:
			raise ValueError("negative max index, ", i_test)
		self.N_idx = <Py_ssize_t> i_test

		self.radii = np.zeros(self.N_idx, dtype=np.double)

		self.sigma_R = 3.6
		self.tau_R = 8
		self._write = False

		dirname = (name + ".vice")
		if os.path.exists(dirname):
			fname = os.path.join(dirname, "gauss_migration.txt")
			self.filename = fname
			self.write = True




# 	def __init__(self, radbins, int n_stars=1, 
# 				 double dt=0.01, double t_end=13.5, str name="example"):
# 
# 		pass


	def __call__(self, int zone, double tform, double time, *, int n=0):
		cdef int bin_id
		cdef double r


		if not (0 <= zone < self.n_bins):
			raise ValueError("Zone out of range: %d" % (zone))

		if tform > time:
			raise ValueError("Time out of range: %f < tform = %f" 
					% (time, tform))

		birth_radius = (self.radial_bins[zone]
						 + self.radial_bins[zone + 1]) / 2

		cdef Py_ssize_t N
		N = self.get_idx(zone, tform, n=n)

		if tform == time:
			self.radii[N] = birth_radius
			bin_id =  zone
		else:
			self.radii[N] = np.abs(self.dR() + self.radii[N])
			if self.radii[N] > 20:
				self.radii[N] = 20
			
			bin_id = self.bin_of(self.radii[N])

		if (0 > bin_id) or (self.n_bins < bin_id):
			raise RuntimeError("calculated a nonsense bin, %i" % bin_id )

		if self.write:
			r = self.radii[N]
			self.write_migration(f"{N},{time},{r},{bin_id}\n")
			
		return bin_id

	def write_migration(self, s):
		with open(self.filename, "a") as f:
			f.write(s)


	def get_idx(self, int zone, double tform, *, int n=0):
		cdef int t_int
		cdef Py_ssize_t N	
		cdef int Na

		t_int = np.round(tform / self.dt) 
		if t_int > self.n_t:
			raise ValueError("time out of range %f" % tform)
		if n > self.n_stars:
			raise ValueError("n out of range %i" % n)


		Na = (t_int * self.n_bins * self.n_stars 
			+ zone * self.n_stars
			+ n)
		if Na < 0 or Na > self.N_idx:
			raise ValueError(f"got out of range index {Na}, values zone={zone}, tform={tform}, n={n}")
		N = Na

		return N


	def bin_of(self, double R):
		if R < 0:
			return -1

		for i in range(self.n_bins):
			if self.radial_bins[i] <= R  <= self.radial_bins[i+1]:
				return int(i)
		return self.n_bins


	def dR(self):
		cdef double r
		r = np.random.normal() * np.sqrt(self.dt/self.tau_R) * self.sigma_R
		return r


	def write_header(self):
		with open(self.filename, "w") as f:
			f.write("N,t,R,zone\n")


	@property
	def write(self):
		return self._write


	@write.setter
	def write(self, a):
		self._write = a
		if a:
			self.write_header()

	@property
	def radial_bins(self):
		return self._radial_bins




