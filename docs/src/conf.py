# Configuration file for the Sphinx documentation builder.

import sys
if sys.version_info[:2] < (3, 5):
	raise RuntimeError("Python >= 3.5 required to compile VICE documentation.")
else: pass

try:
	ModuleNotFoundError
except NameError:
	ModuleNotFoundError = ImportError
try:
	import sphinx
except (ModuleNotFoundError, ImportError):
	raise RuntimeError("""Sphinx >= 2.0.0 is required to compile VICE's \
documentation.""")
version_info_from_string = lambda s: tuple([int(i) for i in s.split('.')])
if version_info_from_string(sphinx.__version__)[:2] < (2, 0):
	raise RuntimeError("Must have Sphinx version >= 2.0.0. Current: %s" % (
		sphinx.__version__))
else: pass
try:
	import vice
except (ModuleNotFoundError, ImportError):
	raise RuntimeError("""VICE not found. VICE must be installed before the \
documentation can be compiled.""")
import warnings
warnings.filterwarnings("ignore")
import os
# Generates the comprehensive API reference
os.system("make -C %s/api" % (
	os.path.dirname(os.path.abspath(__file__))))




# -- Project information -----------------------------------------------------
project = "VICE"
copyright = "2020-2023, James W. Johnson"
author = vice.__author__
release = vice.__version__

_PATH_ = os.path.dirname(os.path.abspath(__file__))

with open("%s/cover.tex" % (_PATH_), 'w') as f:
	f.write(r"""
%%%%%% VICE documentation PDF cover %%%%%%
%%%%%% generated by: docs/src/conf.py %%%%%%

\begin{center}
\begin{figure}[!h]
\centering
\includegraphics{%s/../../logo/logo.png}
\end{figure}
\underline{\LARGE \textbf{Versatile Integrator for Chemical Evolution}}
\par
{\Large \textbf{Version %s}}
\end{center}
""" % (_PATH_, vice.__version__))

with open("%s/index.rst" % (_PATH_), 'w') as f:
	f.write(r"""
.. VICE documentation root file
.. generated by: docs/src/conf.py

VICE: Versatile Integrator for Chemical Evolution
=================================================
Welcome!
This is the documentation for **VICE version %(version)s**.
First time users should familiarize themselves with VICE's API by going
through our `tutorial`__, which can be launched automatically by running
``python -m vice --tutorial`` from a Unix terminal after
:ref:`installing VICE <install>`.
Usage instructions for all of the functions and objects that VICE provides can
be found in our :ref:`comprehensive API reference <apiref>`.
Details on VICE's implementation and justification thereof can be found in
our :ref:`science documentation <scidocs>`.

VICE's developers are happy to consult with scientists looking to
incorporate it into their research.
Email one of our :ref:`contributors <contributors>` or `join us on Slack`__
and start collaborating now!

__ tutorial_
__ slack_

.. _tutorial: https://github.com/giganano/VICE/blob/main/examples/QuickStartTutorial.ipynb
.. _slack: https://join.slack.com/t/vice-astro/shared_invite/zt-tqwa1syp-faiQu0P9oe83cazb0q9tJA


.. toctree::
	:maxdepth: 2

	install
	getting_started
	science_documentation/index
	api/index
	developers/index
""" % {"version": vice.__version__})


# -- General configuration ---------------------------------------------------
extensions = []

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']


# -- Options for HTML output -------------------------------------------------
html_theme = "nature"
html_logo = "../../logo/logo_transparent.png"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

latex_elements = {
	"maketitle": "\\input{%s/cover.tex}" % (
		os.path.dirname(os.path.abspath(__file__))
	)
}

