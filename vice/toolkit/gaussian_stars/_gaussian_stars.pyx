# cython: language_level = 3, boundscheck = False

from __future__ import absolute_import
from ..._globals import _DIRECTORY_
from ...core import _pyutils
from ...core.dataframe import base as dataframe

import numpy as np


from ._gaussian_stars cimport randn



cdef class c_gaussian_stars:
	"""
	The C-implementation of the gaussian_stars object. See python version for
	documentation.
	"""
	cdef double[:] radial_bins
	cdef int n_bins
	cdef int n_t
	cdef int n_stars
	cdef int N_idx
	cdef double dt
	cdef double[:] radii
	cdef double sigma_R
	cdef double tau_R


	def __cinit__(self, radbins, int n_stars=2, 
				  double dt=0.01, double t_end=13.5):
		self.n_bins = len(radbins) - 1
		self.radial_bins = radbins
		self.n_t = np.round(t_end/dt)
		self.n_stars = n_stars
		self.dt = dt

		self.N_idx = self.n_t * self.n_stars * self.n_bins

		self.radii = np.zeros(self.N_idx, dtype=np.float64)

		self.sigma_R = 3.6
		self.tau_R = 8



	def __init__(self, radbins, int n_stars=1, 
				 double dt=0.01, double t_end=13.5):

		pass


	def __call__(self, int zone, double tform, double time, int n=0):

		if not (0 <= zone < self.n_bins):
			raise ValueError("Zone out of range: %d" % (zone))

		if tform > time:
			raise ValueError("Time out of range: %f < tform = %f" 
					% (time, tform))

		birth_radius = (self.radial_bins[zone]
						 + self.radial_bins[zone + 1]) / 2

		N = self.get_idx(zone, tform, n)
		if tform == time:
			self.radii[N] = birth_radius
			bin_ =  zone
		else:
			self.radii[N] += self.dR()
			bin_ = self.bin_of(self.radii[N])
			
		return bin_


	def get_idx(self, int zone, double tform, int n=0):
		cdef int N, t_int
		t_int = np.round(tform / self.dt) 
		if t_int > self.n_t:
			raise ValueError("time out of range %f" % tform)
		if n > self.n_stars:
			raise ValueError("n out of range %i" % n)


		N = (t_int * self.n_bins * self.n_stars 
			+ zone * self.n_stars
			+ n)

		return N


	def bin_of(self, double R):

		for i in range(self.n_bins):
			if self.radial_bins[i] <= R  <= self.radial_bins[i+1]:
				return i
		
		return -1


	def dR(self):
		return numpy.random.normal() * np.sqrt(self.dt/self.tau_R) * self.sigma_R



	@property
	def write(self):
		return self._write

	@write.setter
	def write(self, a):
		self._write = a



