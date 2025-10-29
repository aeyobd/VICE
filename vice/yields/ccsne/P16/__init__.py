r"""
Pignatari et al. (2016) and Ritter et al. (2018) core collapse supernovae
yields

**Signature**: from vice.yields.ccsne import P16

Importing this module will automatically set the CCSN yield settings for all
elements to the IMF-averaged yields calculated with the Chieffi & Limongi
(2004) yield table for [M/H] = 0.15 stars. This will adopt an upper mass limit
of 35 :math:`M_\odot`.

We provide core collapse supernova yields for non-rotating progenitors as
reported by Pignatari et al. (2016) and Ritter et al. (2018) at metallicities
relative to solar of
:math:`\log_{10}(Z / Z_\odot)` =

	- -inf
	- -2.15
	- -1.15
	- -0.37
	- -0.15
	- 0.15

assuming :math:`Z_\odot` = 0.014 according to Asplund et al. (2009) [1]_.

.. tip:: By importing this module, the user does not sacrifice the ability to
	specify their yield settings directly.

.. note:: This module is not imported with a simple ``import vice`` statement.

.. note:: When this module is imported, the yields will be updated with a
	maximum of 10^5 bins in quadrature to decrease computational overhead. For
	some elements, the yield calculation may not converge. To rerun the yield
	calculation with higher numerical precision, simply call ``set_params``
	with a new value for the keyword ``Nmax`` (see below).

Contents
--------
set_params : <function>
	Update the parameters with which the yields are calculated.

.. [1] Asplund et al. (2009), ARA&A, 47, 481
"""

from __future__ import absolute_import
try:
	__VICE_SETUP__
except NameError:
	__VICE_SETUP__ = False
try:
	__VICE_DOCS__
except NameError:
	__VICE_DOCS__ = False

if not __VICE_SETUP__:

	__all__ = ["set_params", "test"]
	from ...._globals import _RECOGNIZED_ELEMENTS_
	from .. import fractional as __fractional
	from .. import settings as __settings
	from .tests import test

	def set_params(**kwargs):
		r"""
		Update the parameter with which the yields are calculated from the
		Ritter et al. (2018) [1]_ data.

		**Signature**: vice.yields.ccsne.P16.set_params(\*\*kwargs)

		Parameters
		----------
		kwargs : varying types
			Keyword arguments to pass to vice.yields.ccsne.fractional.

		Raises
		------
		* TypeError
			 - 	Received a keyword argument "study". This will always be
                "P16"
				when called from this module.

		Other exceptions are raised by vice.yields.ccsne.fractional.

		"""
		if "study" in kwargs.keys():
			raise TypeError("Got an unexpected keyword argument: 'study'")
		else:
			if "MoverH" not in kwargs.keys():
				# fractional will default to 0, override this
				kwargs["MoverH"] = 0.15
			else:
				pass
			for i in _RECOGNIZED_ELEMENTS_:
				__settings[i] = __fractional(i, study = "P16", **kwargs)[0]

	if not __VICE_DOCS__: set_params(MoverH = 0.15, m_upper = 35, Nmax = 1e5)

else:
	pass

