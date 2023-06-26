VICE: Versatile Integrator for Chemical Evolution

* 77 elements on the periodic table
* Fast integration of one-zone models
* Enrichment from single stellar populations
* Highly flexible nucleosynthetic yield calculations
* User-defined mathematical forms describing:
	- Nucleosynthetic yields in simulations
	- Mixing processes in multi-zone models
	- Infall and star formation histories
	- The stellar initial mass function
	- The star formation law
	- Element-by-element infall metallicities
	- Type Ia supernova delay-time distributions

How to Access the Documentation:
--------------------------------
Documentation is available in several forms:

	1. Online: http://vice-astro.readthedocs.io
	2. In PDF format, available for download at the same address
	3. In the docstrings embedded within the software

Running ``vice --docs`` from the terminal will open the online documentation
in the default web browser.

First time users should go through VICE's QuickStartTutorial jupyter notebook,
available under examples/ in the git repository. This can be launched from
the command line by running ``vice --tutorial``. Other example scripts can
be found there as well.

Contents
--------
singlezone : ``object``
	Simulate a single-zone galactic chemical evolution model
multizone : ``object``
	Simulate a multi-zone galactic chemical evolution model
milkyway : ``object``
	A ``multizone`` object optimized for modeling the Milky Way.
output : ``object``
	Read and store output from ``singlezone`` simulations.
multioutput : ``object``
	Read and store output from ``multizone`` simulations.
migration : <module>
	Utilities for mixing prescriptions in multizone simulations.
single_stellar_population : <function>
	Simulate enrichment from a single conatal star cluster
cumulative_return_fraction : <function>
	Calculate the cumulative return fraction of a star cluster of known age
main_sequence_mass_fraction : <function>

