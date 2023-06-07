from subprocess import Popen, PIPE
import sys
import os

if os.name != "posix": raise OSError("""\
Sorry, Windows is not supported. Please install and run VICE from within the \
Windows Subsystem for Linux.""")


from setuptools import setup, Extension, Command
from setuptools.command.build_ext import build_ext as _build_ext
from setuptools.command.install import install
from setuptools import find_packages as _find_packages

from Cython.Build import cythonize


bugs_url = "https://github.com/giganano/VICE/issues"



def openmp_enabled():
	# if ("VICE_ENABLE_OPENMP" in os.environ.keys() 
	# and os.environ["VICE_ENABLE_OPENMP"] == "true"):
	return True


class build_ext(_build_ext):
	r"""
	Extends the ``build_ext`` base class provided by ``setuptools`` to
	determine compiler flags on a case-by-case basis and filter the extensions
	to be (re-)compiled.
	"""

	def build_extensions(self):
		self.filter_extensions()

		compile_args, link_args = self.get_flags()

		for ext in self.extensions:
			for flag in compile_args: ext.extra_compile_args.append(flag)
			for flag in link_args: ext.extra_link_args.append(flag)

		_build_ext.build_extensions(self)

	

	def filter_extensions(self):
		if "VICE_SETUP_EXTENSIONS" in os.environ.keys():
			specified = os.environ["VICE_SETUP_EXTENSIONS"].split(',')
			self.extensions = list(filter(lambda x: x.name in specified,
				self.extensions))
		else: pass


	def get_flags(self):
		compile_args = ["-fPIC", "-Wsign-conversion", "-Wsign-compare"]
		link_args = []

		if openmp_enabled():
			c_args, l_args = self.get_openmp_flags()
			compile_args += c_args
			link_args += l_args

		else: pass

		return compile_args, link_args



	def get_openmp_flags(self):
		if not openmp_enabled():
			return [], []

		compile_args = []
		link_args = []

		if sys.platform == "darwin":
			self.add_openmp_mac()

		compiler = get_compiler()

		if compiler == "gcc":
			compile_args.append("-fopenmp")
			link_args.append("-fopenmp")
		elif compiler == "clang":
			compile_args.append("-Xpreprocessor")
			compile_args.append("-fopenmp")
			link_args.append("-Xpreprocessor")
			link_args.append("-fopenmp")
			link_args.append("-lomp")
		else:
			raise RuntimeError()

		return compile_args, link_args


	def add_openmp_mac(self):
		# find the OpenMP header and library files by brute force
		# on Mac OS -> this should get around issues with linking
		# through -Xpreprocessor or -Xclang by specifying the
		# locations of the files directly.
		find_openmp_darwin()
		for ext in self.extensions:
			ext.library_dirs.append(os.environ["LIBOMP_LIBRARY_DIR"])
			ext.include_dirs.append(os.environ["LIBOMP_INCLUDE_DIR"])


def find_openmp_darwin():
	r"""
	Determine the path to the OpenMP library and header files on Mac OS
	using Homebrew.

	Notes
	-----
	This function first runs ``brew`` to determine if Homebrew is
	installed, and the users who have not done so will be directed
	accordingly. It then runs ``brew list libomp`` to list the files
	associated with OpenMP, if any. If the necessary header and library
	files are found, their directories are assigned to the environment
	variables ``LIBOMP_INCLUDE_DIR`` and ``LIBOMP_LIBRARY_DIR`` to then
	be included in the call to ``build_extensions``. IF the OpenMP files
	are not found, then the user is directed to run ``brew install libomp``
	or ``brew reinstall libomp`` before reattempting their VICE
	installation.
	"""
	kwargs = {
		"stdout": PIPE,
		"stderr": PIPE,
		"shell": True,
		"text": True
	}
	with Popen("brew", **kwargs) as proc:
		out, err = proc.communicate()
		if err != "" and "command not found" in err:
			raise RuntimeError("""\
It appears that Homebrew is not installed. Please install Homebrew by \
following the instructions at https://brew.sh/ and then install OpenMP \
by running

$ brew install libomp

from your Unix command line before reattempting your VICE installation.""")
		else: pass

	with Popen("brew list libomp", **kwargs) as proc:
		out, err = proc.communicate()
		out = out.split('\n')
		if (any([_.endswith("omp.h") for _ in out]) and 
			any([_.endswith("libomp.dylib") for _ in out])):
			# found header and library files to link
			idx = 0
			while not out[idx].endswith("omp.h"): idx += 1
			os.environ["LIBOMP_INCLUDE_DIR"] = os.sep.join(
				out[idx].split(os.sep)[:-1])
			idx = 0
			while not out[idx].endswith("libomp.dylib"): idx += 1
			os.environ["LIBOMP_LIBRARY_DIR"] = os.sep.join(
				out[idx].split(os.sep)[:-1])
		else:
			raise RuntimeError("""\
Homebrew is installed, but the OpenMP header and library files were not found. \
If you have not installed OpenMP, please run

$ brew install libomp

from your Unix command line. If you have installed OpenMP, please reinstall it \
by running

$ brew reinstall libomp

and then reattempting your VICE installation. If you continue to have trouble \
linking VICE with OpenMP, then please open an issue at %s.""" % (bugs_url))




def find_extensions(path = './src/vice'):
	r"""
	Finds all of VICE's extensions. If the user is either running
	``setup.py extensions`` or has (equivalently) assigned the environment
	variable "VICE_SETUP_EXTENSIONS"", then this list will be filtered down
	later when ``setuptools`` runs the ``build_extensions`` function.

	Parameters
	----------
	path : str [default : './src/vice']
		The path to the package directory

	Returns
	-------
	exts : list
		A list of ``Extension`` objects to build.
	"""
	extensions = []
	for root, dirs, files in os.walk(path):
		for i in files:
			if i.endswith(".pyx"):
				# The name of the extension
				name = "%s.%s" % (root[6:].replace('/', '.'),
					i.split('.')[0])
				# The source files in the C library
				src_files = ["%s/%s" % (root[2:], i)]
				src_files += find_c_extensions(name)
				extensions.append(Extension(name, src_files))
				print("extension ", name)
				print("sources ", src_files)
			else: continue

	return extensions




def setup_package():
	r"""
	Build and install VICE.
	"""

	# directories with .h header files, req'd by setup
	include_dirs = []
	for root, dirs, files in os.walk("./src/vice"):
		if "__pycache__" not in root: include_dirs.append(root)

	metadata = dict(
		# long_description = _LONG_DESCRIPTION_,
		platforms = ["Linux", "Mac OS X", "Unix"],
		cmdclass = {
			"build_ext": build_ext,
		},
		packages = _find_packages(where="src"),
		package_dir = {"": "src"},
        package_data = {"": ["*.dat"]},
		ext_modules = find_extensions(),
		include_dirs = include_dirs,
		zip_safe = False,
		verbose = "-q" not in sys.argv and "--quiet" not in sys.argv
	)


	# set_path_variable()
	setup(**metadata)

	check_dill()





def find_c_extensions(name):
	r"""
	Finds the paths to the C extensions required for the specified
	extension based on the _CFILES_ mapping in
	vice/_build_utils/c_extensions.py.

	Parameters
	----------
	name : str
		The name of the extension to compile.

	Returns
	-------
	exts : list
		A list of the relative paths to all C extensions.

	Notes
	-----
	If the extension does not have an entry in the _CFILES_ dictionary,
	VICE will compile the extension with ALL C files in it's C library,
	omitting those under a directory named "tests" if "tests" is not in the
	name of the extension.
	"""
	extensions = []
	if name in _CFILES_.keys():
		print("known: ", name)
		extensions += find_known_c_ext(name)
	else:
		print("unknown: ", name)
		extensions += find_generic_c_ext(name)

	return extensions


def find_known_c_ext(name):
    extensions = []
    for item in _CFILES_[name]:
        fname = "./src/" + item
        if os.path.exists(fname) and (item.endswith(".c")):
            extensions.append(fname)
        elif os.path.isdir(fname):
            for i in os.listdir(fname):
                if i.endswith(".c"): 
                    extensions.append("%s/%s" % (fname, i))
        else:
            raise SystemError("""Internal Error. Invalid C Extension \
listing for extension %s: %s""" % (name, item))

    return extensions


def find_generic_c_ext(name):
    extensions = []
    path = "./src/vice/src"
    for root, dirs, files in os.walk(path):
        for i in files:
            if i.endswith(".c"):
                if "tests" in root and "tests" not in name:
                    continue
                else:
                    extensions.append(
                        ("%s/%s" % (root, i)).replace(os.getcwd(), '.')
                    )
            else: pass

    return extensions


def get_compiler():
	if "CC" in os.environ.keys():
		os.environ["CC"] = check_compiler(os.environ["CC"])

		# don't use == because it could be, e.g., gcc-10
		if os.environ["CC"].startswith("gcc"):
			return "gcc"
		elif os.environ["CC"].startswith("clang"):
			return "clang"
		else:
			raise RuntimeError("""\
Unix C compiler must be either 'gcc' or 'clang'. Got %s from environment \
variable 'CC'.""" % (os.environ["CC"]))


	if sys.platform == "linux":
		os.environ["CC"] = "gcc"
	elif sys.platform == "darwin":
		os.environ["CC"] = "clang"
	else:
		raise OSError("Sorry, Windows is not supported.")

	return os.environ["CC"]



def check_compiler(compiler):
	r"""
	Determine if the specified compiler is supported and whether or not
	it corresponds to gcc or clang.

	Parameters
	----------
	compiler : ``str``
		The compiler that may or may not be supported.

	Returns
	-------
	The plain name of the compiler (i.e. "gcc" or "clang" as opposed to,
	e.g., "gcc-10" or "clang-11") if it is supported. ``None`` if the
	compiler is not found on the user's PATH, and ``False`` if it is
	outrightly not supported.

	Notes
	-----
	This test determines whether to compiler corresponds to a version of
	gcc or clang by using the `which` bash command and the `--version`
	flag the compiler should accept on the command-line, then looking for
	the strings "gcc" and "clang" in the output string. This allows a
	compiler invoked with a version number (e.g. gcc-10, clang-11) to work
	with this function.
	"""
	kwargs = {
		"stdout": PIPE,
		"stderr": PIPE,
		"shell": True,
		"text": True
	}

	check_has_compiler(compiler, **kwargs)


	return check_compiler_runs(compiler, **kwargs)


def check_has_compiler(compiler, **kwargs):
	with Popen("which %s" % (compiler), **kwargs) as proc:
		out, err = proc.communicate()
		if sys.platform == "linux":
			# The error message printed on Linux `which`
			if "no %s" % (compiler) in err: return None
		elif sys.platform == "darwin":
			# On Mac OS, `which` prints nothing on error
			if out == "" and err == "": return None
		else:
			raise OSError("Sorry, Windows is not supported.")


def check_compiler_runs(compiler, **kwargs):
	# check if the command `$compiler --version` runs properly and
	# has either "gcc" or "clang" in the output along with a version number
	with Popen("%s --version" % (compiler), **kwargs) as proc:
		out, err = proc.communicate()
		# Should catch all typos
		if err != "" and "command not found" in err: return None
		# Should catch anything that isn't a compiler
		if err != "" and "illegal" in err: return False
		recognized = False
		contains_version_number = False
		for word in out.split():
			for test in openmp.supported_compilers:
				# startswith as opposed to == works with, e.g., gcc-10
				if word.startswith(test):
					compiler = word # catches gcc -> clang alias on Mac OS
					recognized = True
				else: pass
				contains_version_number |= is_version_number(word)
		if recognized and contains_version_number: return compiler
		return False


def is_version_number(word):
	r"""
	Looks for what could be a version number in a single string by
	determining if it is simply numbers separated by decimals.
	Returns ``True`` if the string could be interpreted as a version
	number and ``False`` otherwise.
	"""
	if '.' in word:
		_is_version_number = True
		for item in word.split('.'): _is_version_number &= item.isdigit()
		return _is_version_number
	else:
		return False


def check_dill():
	try:
		import dill
	except (ImportError, ModuleNotFoundError):
		print("""\
===============================================================================
Package 'dill' not found. This package is required for encoding functional
attributes with VICE outputs. It is recommended that VICE users install this
package to make use of these features. This can be done via 'pip install dill'.
===============================================================================\
""")

# def set_path_variable(filename = "~/.bash_profile"):
# 	r"""
# 	Permanently adds ~/.local/bin/ to the user's $PATH for local
# 	installations (i.e. with [--user] directive).
# 
# 	Parameters
# 	----------
# 	filename : str [default : "~/.bash_profile"]
# 		The filename to put the PATH modification in.
# 	"""
# 	if ("--user" in sys.argv and "%s/.local/bin" % (os.environ["HOME"]) not in
# 		os.environ["PATH"].split(':')):
# 		cnt = """\
# 
# # This line added by vice setup.py %(version)s
# export PATH=$HOME/.local/bin:$PATH
# 
# """
# 		cmd = "echo \'%s\' >> %s" % (cnt % {"version": VERSION}, filename)
# 		os.system(cmd)
# 	else:
# 		pass


# def write_version_info(filename = "./vice/version_breakdown.py"):
# 	r"""
# 	Writes the version info to disk within the source tree
# 
# 	Parameters
# 	----------
# 	filename : str [default : "./vice/version_breakdown.py"]
# 		The file to write the version info to.
# 
# 	.. note:: vice/version.py depends on the file produced by this function.
# 	"""
# 	cnt = """\
# # This file is generated from vice setup.py %(version)s
# 
# MAJOR = %(major)d
# MINOR = %(minor)d
# MICRO = %(micro)d
# DEV = %(dev)s
# ALPHA = %(alpha)s
# BETA = %(beta)s
# RC = %(rc)s
# POST = %(post)s
# ISRELEASED = %(isreleased)s
# MIN_PYTHON_VERSION = \"%(minversion)s\"
# """
# 	with open(filename, 'w') as f:
# 		try:
# 			f.write(cnt % {
# 					"version":		VERSION,
# 					"major":		MAJOR,
# 					"minor":		MINOR,
# 					"micro":		MICRO,
# 					"dev":			str(DEV),
# 					"alpha":		str(ALPHA),
# 					"beta":			str(BETA),
# 					"rc":			str(RC),
# 					"post":			str(POST),
# 					"isreleased":	str(ISRELEASED),
# 					"minversion":	MIN_PYTHON_VERSION
# 				})
# 		finally:
# 			f.close()
# 
_CFILES_ = {
	"vice.core._cutils": [
		"./vice/src/objects/callback_1arg.c",
		"./vice/src/objects/callback_2arg.c",
		"./vice/src/io/progressbar.c",
		"./vice/src/multithread.c",
		"./vice/src/utils.c"
	],
	"vice.core._mlr": [
		"./vice/src/ssp/mlr",
		"./vice/src/ssp/mlr.c",
		"./vice/src/objects/interp_scheme_1d.c",
		"./vice/src/objects/interp_scheme_2d.c",
		"./vice/src/toolkit/interp_scheme_1d.c",
		"./vice/src/toolkit/interp_scheme_2d.c",
		"./vice/src/io/utils.c",
		"./vice/src/utils.c"
	],
	"vice.core.dataframe._agb_yield_settings": [],
	"vice.core.dataframe._base": [],
	"vice.core.dataframe._ccsn_yield_table": [],
	"vice.core.dataframe._elemental_settings": [],
	"vice.core.dataframe._entrainment": [],
	"vice.core.dataframe._evolutionary_settings": [],
	"vice.core.dataframe._fromfile": [
		"./vice/src/dataframe/calclogz.c",
		"./vice/src/dataframe/calclookback.c",
		"./vice/src/dataframe/calcz.c",
		"./vice/src/dataframe/fromfile.c",
		"./vice/src/dataframe/utils.c",
		"./vice/src/objects/fromfile.c",
		"./vice/src/io/utils.c",
		"./vice/src/utils.c"
	],
	"vice.core.dataframe._history": [
		"./vice/src/dataframe/calclogz.c",
		"./vice/src/dataframe/calclookback.c",
		"./vice/src/dataframe/calcz.c",
		"./vice/src/dataframe/fromfile.c",
		"./vice/src/dataframe/history.c",
		"./vice/src/dataframe/utils.c",
		"./vice/src/objects/fromfile.c",
		"./vice/src/io/utils.c",
		"./vice/src/utils.c"
	],
	"vice.core.dataframe._noncustomizable": [],
	"vice.core.dataframe._saved_yields": [],
	"vice.core.dataframe._tracers": [
		"./vice/src/dataframe/calclogz.c",
		"./vice/src/dataframe/calclookback.c",
		"./vice/src/dataframe/calcz.c",
		"./vice/src/dataframe/fromfile.c",
		"./vice/src/dataframe/tracers.c",
		"./vice/src/dataframe/utils.c",
		"./vice/src/objects/fromfile.c",
		"./vice/src/io/utils.c",
		"./vice/src/utils.c"
	],
	"vice.core.dataframe._yield_settings": [],
	"vice.core.multizone._migration": [
		"./vice/src/io",
		"./vice/src/multizone",
		"./vice/src/objects",
		"./vice/src/singlezone",
		"./vice/src/ssp",
		"./vice/src/ssp/mlr",
		"./vice/src/toolkit",
		"./vice/src/yields",
		"./vice/src"
	],
	"vice.core.multizone._multizone": [
		"./vice/src/io",
		"./vice/src/multizone",
		"./vice/src/objects",
		"./vice/src/singlezone",
		"./vice/src/ssp",
		"./vice/src/ssp/mlr",
		"./vice/src/toolkit",
		"./vice/src/yields",
		"./vice/src"
	],
	"vice.core.multizone._zone_array": [],
	"vice.core.multizone.tests._multizone": [],
	"vice.core.objects._imf": [
		"./vice/src/objects/callback_1arg.c",
		"./vice/src/objects/imf.c"
	],
	"vice.core.objects.tests._agb": [
		"./vice/src/objects/agb.c",
		"./vice/src/objects/callback_1arg.c",
		"./vice/src/objects/callback_2arg.c",
		"./vice/src/objects/interp_scheme_2d.c",
		"./vice/src/objects/tests/agb.c",
		"./vice/src/objects/tests/callback_1arg.c",
		"./vice/src/objects/tests/callback_2arg.c",
		"./vice/src/objects/tests/interp_scheme_2d.c"
	],
	"vice.core.objects.tests._callback_1arg": [
		"./vice/src/objects/callback_1arg.c",
		"./vice/src/objects/tests/callback_1arg.c"
	],
	"vice.core.objects.tests._callback_2arg": [
		"./vice/src/objects/callback_1arg.c",
		"./vice/src/objects/callback_2arg.c",
		"./vice/src/objects/tests/callback_1arg.c",
		"./vice/src/objects/tests/callback_2arg.c"
	],
	"vice.core.objects.tests._ccsne": [
		"./vice/src/objects/ccsne.c",
		"./vice/src/objects/callback_1arg.c",
		"./vice/src/objects/tests/ccsne.c",
		"./vice/src/objects/tests/callback_1arg.c"
	],
	"vice.core.objects.tests._channel": [
		"./vice/src/objects/channel.c",
		"./vice/src/objects/callback_1arg.c",
		"./vice/src/objects/tests/channel.c",
		"./vice/src/objects/tests/callback_1arg.c"
	],
	"vice.core.objects.tests._element": [
		"./vice/src/objects/element.c",
		"./vice/src/objects/agb.c",
		"./vice/src/objects/ccsne.c",
		"./vice/src/objects/sneia.c",
		"./vice/src/objects/channel.c",
		"./vice/src/objects/callback_1arg.c",
		"./vice/src/objects/callback_2arg.c",
		"./vice/src/objects/interp_scheme_2d.c",
		"./vice/src/objects/tests/element.c",
		"./vice/src/objects/tests/agb.c",
		"./vice/src/objects/tests/ccsne.c",
		"./vice/src/objects/tests/sneia.c",
		"./vice/src/objects/tests/channel.c",
		"./vice/src/objects/tests/callback_1arg.c",
		"./vice/src/objects/tests/callback_2arg.c",
		"./vice/src/objects/tests/interp_scheme_2d.c"
	],
	"vice.core.objects.tests._fromfile": [
		"./vice/src/objects/fromfile.c",
		"./vice/src/objects/tests/fromfile.c"
	],
	"vice.core.objects.tests._hydrodiskstars": [
		"./vice/src/objects/hydrodiskstars.c",
		"./vice/src/objects/tests/hydrodiskstars.c"
	],
	"vice.core.objects.tests._imf": [
		"./vice/src/objects/imf.c",
		"./vice/src/objects/callback_1arg.c",
		"./vice/src/objects/tests/imf.c",
		"./vice/src/objects/tests/callback_1arg.c"
	],
	"vice.core.objects.tests._integral": [
		"./vice/src/objects/integral.c",
		"./vice/src/objects/tests/integral.c"
	],
	"vice.core.objects.tests._interp_scheme_1d": [
		"./vice/src/objects/interp_scheme_1d.c",
		"./vice/src/objects/tests/interp_scheme_1d.c"
	],
	"vice.core.objects.tests._interp_scheme_2d": [
		"./vice/src/objects/interp_scheme_2d.c",
		"./vice/src/objects/tests/interp_scheme_2d.c"
	],
	"vice.core.objects.tests._ism": [
		"./vice/src/objects/ism.c",
		"./vice/src/objects/callback_1arg.c",
		"./vice/src/objects/callback_2arg.c",
		"./vice/src/objects/tests/ism.c",
		"./vice/src/objects/tests/callback_1arg.c",
		"./vice/src/objects/tests/callback_2arg.c"
	],
	"vice.core.objects.tests._mdf": [
		"./vice/src/objects/mdf.c",
		"./vice/src/objects/tests/mdf.c"
	],
	"vice.core.objects.tests._migration": [
		"./vice/src/objects/migration.c",
		"./vice/src/objects/tracer.c",
		"./vice/src/objects/tests/migration.c"
	],
	"vice.core.objects.tests._multizone": [
		"./vice/src/objects/multizone.c",
		"./vice/src/objects/migration.c",
		"./vice/src/objects/tracer.c",
		"./vice/src/objects/tests/multizone.c"
	],
	"vice.core.objects.tests._singlezone": [
		"./vice/src/io",
		"./vice/src/multizone",
		"./vice/src/objects",
		"./vice/src/objects/tests",
		"./vice/src/singlezone",
		"./vice/src/ssp",
		"./vice/src/ssp/mlr",
		"./vice/src/toolkit",
		"./vice/src/yields",
		"./vice/src"
	],
	"vice.core.objects.tests._sneia": [
		"./vice/src/objects/sneia.c",
		"./vice/src/objects/callback_1arg.c",
		"./vice/src/objects/tests/sneia.c",
		"./vice/src/objects/tests/callback_1arg.c"
	],
	"vice.core.objects.tests._ssp": [
		"./vice/src/objects/ssp.c",
		"./vice/src/objects/callback_1arg.c",
		"./vice/src/objects/imf.c",
		"./vice/src/objects/tests/ssp.c",
		"./vice/src/objects/tests/callback_1arg.c",
		"./vice/src/objects/tests/imf.c"
	],
	"vice.core.objects.tests._tracer": [
		"./vice/src/objects/tracer.c",
		"./vice/src/objects/tests/tracer.c"
	],
	"vice.core.outputs._history": [],
	"vice.core.outputs._mdf": [],
	"vice.core.outputs._multioutput": [],
	"vice.core.outputs._output": [],
	"vice.core.outputs._tracers": [],
	"vice.core.singlezone._singlezone": [
		"./vice/src/io",
		"./vice/src/multizone",
		"./vice/src/objects",
		"./vice/src/singlezone",
		"./vice/src/ssp",
		"./vice/src/ssp/mlr",
		"./vice/src/toolkit",
		"./vice/src/yields",
		"./vice/src"
	],
	"vice.core.singlezone.tests._singlezone": [],
	"vice.core.ssp._crf": [
		"./vice/src/io",
		"./vice/src/multizone",
		"./vice/src/objects",
		"./vice/src/singlezone",
		"./vice/src/ssp",
		"./vice/src/ssp/mlr",
		"./vice/src/toolkit",
		"./vice/src/yields",
		"./vice/src"
	],
	"vice.core.ssp._imf": [
		"./vice/src/imf.c",
		"./vice/src/callback.c",
		"./vice/src/utils.c"
	],
	"vice.core.ssp._msmf": [
		"./vice/src/io",
		"./vice/src/multizone",
		"./vice/src/objects",
		"./vice/src/singlezone",
		"./vice/src/ssp",
		"./vice/src/ssp/mlr",
		"./vice/src/toolkit",
		"./vice/src/yields",
		"./vice/src"
	],
	"vice.core.ssp._ssp": [
		"./vice/src/io",
		"./vice/src/multizone",
		"./vice/src/objects",
		"./vice/src/singlezone",
		"./vice/src/ssp",
		"./vice/src/ssp/mlr",
		"./vice/src/toolkit",
		"./vice/src/yields",
		"./vice/src"
	],
	"vice.core.ssp.tests._crf": [
		"./vice/src/io",
		"./vice/src/multizone",
		"./vice/src/objects",
		"./vice/src/objects/tests",
		"./vice/src/singlezone",
		"./vice/src/ssp",
		"./vice/src/ssp/mlr",
		"./vice/src/ssp/tests",
		"./vice/src/toolkit",
		"./vice/src/yields",
		"./vice/src"
	],
	"vice.core.ssp.tests._msmf": [
		"./vice/src/io",
		"./vice/src/multizone",
		"./vice/src/objects",
		"./vice/src/objects/tests",
		"./vice/src/singlezone",
		"./vice/src/ssp",
		"./vice/src/ssp/mlr",
		"./vice/src/ssp/tests",
		"./vice/src/toolkit",
		"./vice/src/yields",
		"./vice/src"
	],
	"vice.core.ssp.tests._remnants": [
		"./vice/src/io",
		"./vice/src/multizone",
		"./vice/src/objects",
		"./vice/src/objects/tests",
		"./vice/src/singlezone",
		"./vice/src/ssp",
		"./vice/src/ssp/mlr",
		"./vice/src/ssp/tests",
		"./vice/src/toolkit",
		"./vice/src/yields",
		"./vice/src"
	],
	"vice.core.tests._cutils": [
		"./vice/src/objects/callback_1arg.c",
		"./vice/src/objects/callback_2arg.c",
		"./vice/src/objects/imf.c"
	],
	"vice.src.io.tests._agb": [
		"./vice/src/io/tests/agb.c",
		"./vice/src/io/agb.c",
		"./vice/src/objects/agb.c",
		"./vice/src/objects/callback_1arg.c",
		"./vice/src/objects/callback_2arg.c",
		"./vice/src/objects/ccsne.c",
		"./vice/src/objects/channel.c",
		"./vice/src/objects/element.c",
		"./vice/src/objects/interp_scheme_2d.c",
		"./vice/src/objects/sneia.c",
		"./vice/src/io/utils.c"
	],
	"vice.src.io.tests._ccsne": [
		"./vice/src/io/tests/ccsne.c",
		"./vice/src/io/ccsne.c",
		"./vice/src/io/utils.c"
	],
	"vice.src.io.tests._sneia": [
		"./vice/src/io/tests/sneia.c",
		"./vice/src/io/sneia.c",
		"./vice/src/io/utils.c"
	],
	"vice.src.io.tests._utils": [
		"./vice/src/io/tests/utils.c",
		"./vice/src/io/utils.c"
	],
	"vice.src.multizone.tests.cases._generic": [
		"./vice/src/io",
		"./vice/src/multizone",
		"./vice/src/multizone/tests",
		"./vice/src/objects",
		"./vice/src/singlezone",
		"./vice/src/ssp",
		"./vice/src/ssp/mlr",
		"./vice/src/toolkit",
		"./vice/src/yields",
		"./vice/src"
	],
	"vice.src.multizone.tests.cases._no_migration": [
		"./vice/src/io",
		"./vice/src/multizone",
		"./vice/src/multizone/tests",
		"./vice/src/objects",
		"./vice/src/singlezone",
		"./vice/src/ssp",
		"./vice/src/ssp/mlr",
		"./vice/src/toolkit",
		"./vice/src/yields",
		"./vice/src"
	],
	"vice.src.multizone.tests.cases._separation": [
		"./vice/src/io",
		"./vice/src/multizone",
		"./vice/src/multizone/tests",
		"./vice/src/objects",
		"./vice/src/singlezone",
		"./vice/src/ssp",
		"./vice/src/ssp/mlr",
		"./vice/src/toolkit",
		"./vice/src/yields",
		"./vice/src"
	],
	"vice.src.singlezone.tests._singlezone": [
		"./vice/src/io",
		"./vice/src/multizone",
		"./vice/src/objects",
		"./vice/src/singlezone",
		"./vice/src/singlezone/tests/agb.c",
		"./vice/src/singlezone/tests/ccsne.c",
		"./vice/src/singlezone/tests/element.c",
		"./vice/src/singlezone/tests/ism.c",
		"./vice/src/singlezone/tests/mdf.c",
		"./vice/src/singlezone/tests/recycling.c",
		"./vice/src/singlezone/tests/singlezone.c",
		"./vice/src/singlezone/tests/sneia.c",
		"./vice/src/ssp",
		"./vice/src/ssp/mlr",
		"./vice/src/toolkit",
		"./vice/src/yields",
		"./vice/src"
	],
	"vice.src.singlezone.tests.cases._generic": [
		"./vice/src/io",
		"./vice/src/multizone",
		"./vice/src/objects",
		"./vice/src/singlezone",
		"./vice/src/singlezone/tests",
		"./vice/src/ssp",
		"./vice/src/ssp/mlr",
		"./vice/src/toolkit",
		"./vice/src/yields",
		"./vice/src"
	],
	"vice.src.singlezone.tests.cases._max_age_ssp": [
		"./vice/src/io",
		"./vice/src/multizone",
		"./vice/src/objects",
		"./vice/src/singlezone",
		"./vice/src/singlezone/tests",
		"./vice/src/ssp",
		"./vice/src/ssp/mlr",
		"./vice/src/toolkit",
		"./vice/src/yields",
		"./vice/src"
	],
	"vice.src.singlezone.tests.cases._quiescence": [
		"./vice/src/io",
		"./vice/src/multizone",
		"./vice/src/objects",
		"./vice/src/singlezone",
		"./vice/src/singlezone/tests",
		"./vice/src/ssp",
		"./vice/src/ssp/mlr",
		"./vice/src/toolkit",
		"./vice/src/yields",
		"./vice/src"
	],
	"vice.src.singlezone.tests.cases._zero_age_ssp": [
		"./vice/src/io",
		"./vice/src/multizone",
		"./vice/src/objects",
		"./vice/src/singlezone",
		"./vice/src/singlezone/tests",
		"./vice/src/ssp",
		"./vice/src/ssp/mlr",
		"./vice/src/toolkit",
		"./vice/src/yields",
		"./vice/src"
	],
	"vice.src.tests._callback": [
		"./vice/src/tests/callback.c",
		"./vice/src/callback.c",
		"./vice/src/objects/callback_1arg.c",
		"./vice/src/objects/callback_2arg.c",
		"./vice/src/objects/tests/callback_1arg.c",
		"./vice/src/objects/tests/callback_2arg.c"
	],
	"vice.src.tests._imf": [
		"./vice/src/tests/imf.c",
		"./vice/src/imf.c",
		"./vice/src/callback.c",
		"./vice/src/utils.c",
		"./vice/src/objects/imf.c",
		"./vice/src/objects/callback_1arg.c"
	],
	"vice.src.tests._stats": [
		"./vice/src/tests/stats.c",
		"./vice/src/stats.c",
		"./vice/src/utils.c"
	],
	"vice.src.tests._utils": [
		"./vice/src/tests/utils.c",
		"./vice/src/utils.c"
	],
	"vice.toolkit.hydrodisk._hydrodiskstars": [
		"./vice/src/objects/hydrodiskstars.c",
		"./vice/src/toolkit/hydrodiskstars.c",
		"./vice/src/io/utils.c",
		"./vice/src/utils.c"
	],
	"vice.toolkit.interpolation._interp_scheme_1d": [
		"./vice/src/objects/interp_scheme_1d.c",
		"./vice/src/toolkit/interp_scheme_1d.c",
		"./vice/src/utils.c"
	],
	"vice.toolkit.interpolation._interp_scheme_2d": [
		"./vice/src/objects/interp_scheme_2d.c",
		"./vice/src/toolkit/interp_scheme_2d.c",
		"./vice/src/utils.c"
	],
	"vice.yields.agb._grid_reader": [
		"./vice/src/objects/agb.c",
		"./vice/src/objects/callback_1arg.c",
		"./vice/src/objects/callback_2arg.c",
		"./vice/src/objects/ccsne.c",
		"./vice/src/objects/channel.c",
		"./vice/src/objects/element.c",
		"./vice/src/objects/interp_scheme_2d.c",
		"./vice/src/objects/sneia.c",
		"./vice/src/io/agb.c",
		"./vice/src/io/utils.c"
	],
	"vice.yields.ccsne._yield_integrator": [
		"./vice/src/yields",
		"./vice/src/objects/callback_1arg.c",
		"./vice/src/objects/integral.c",
		"./vice/src/objects/imf.c",
		"./vice/src/objects/ccsne.c",
		"./vice/src/io/ccsne.c",
		"./vice/src/io/utils.c",
		"./vice/src/io/progressbar.c",
		"./vice/src"
	],
	"vice.yields.sneia._yield_lookup": [
		"./vice/src/io/sneia.c",
		"./vice/src/io/utils.c"
	],
	"vice.yields.tests._integral": [
		"./vice/src/yields/tests/integral.c",
		"./vice/src/yields/integral.c",
		"./vice/src/objects/integral.c",
		"./vice/src/utils.c"
	]

}



if __name__ == "__main__":
    setup_package()

