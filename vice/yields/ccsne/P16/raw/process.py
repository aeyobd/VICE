import re
import os
import numpy as np
from pathlib import Path


def read_csv(file_path, skip=0, num_rows=None, header=True, sep=r",", comment=None):
	"""
	Reads in a delimeter-separated file and returns a dictionary of lists for each column.

	Parameters
	----------
	file_path: `str`
		The path to the file to read
	skip: `int`
		The number of rows to skip at the beginning of the file
	num_rows: `int`
		The number of rows to read from the file. If None, reads all rows.
	header: `bool`
		Whether the file has a header row
	sep: `str`
		The delimiter used in the file
	comment: `str`
		The comment character used in the file
	"""
	data = {}
	columns = []

	if not header:
		d

	with open(file_path, 'r') as file:
		for _ in range(skip):
			next(file)

		for (row, line) in enumerate(file):
			if num_rows is not None and row >= num_rows:
				break

			if comment is not None and line.startswith(comment):
				continue

			parts = re.split(sep, line.strip())

			if header:
				header = False
				columns = parts
				data = {col: [] for col in columns}
			else:	
				if data == {}:
					data = {i: [] for i in range(len(parts))}

				assert len(columns) == len(parts), f"Header and data length mismatch {len(columns)} != {len(parts)} at row {row}\n parts={parts}"

				parts_num = []
				for p in parts:
					try:
						parts_num.append(float(p))
					except ValueError:
						parts_num.append(p)

				for i, col in enumerate(columns):
					data[col].append(parts_num[i])
	
	return data




	


def read_element_yields(file_path):
	"""
	Reads in the yields from the Fryer et al. 2012 table

	Returns a dictionary with keys of (M, Z) and values which are each a table with columns for Isotopes, Yields, X0 (initial mass), and Z (atomic number).

	"""

	yields = {}


	with open(file_path, 'r') as file:
		tablestart = -1
		tableend = -1
		comment = False
		table = False

		M = None
		Z = None

		for i, line in enumerate(file):
			if line.startswith("H"):
				if table:
					tableend = i
					df = read_csv(file_path, skip=tablestart, num_rows=tableend-tablestart, header=True, sep=r"\s*&")
					if (M, Z) in yields.keys():
						print(f"Duplicate found for M={M}, Z={Z}")
					yields[(M, Z)] = df

				comment = True
				table = False

			if line.startswith("&"):
				if comment:
					tablestart = i
				table = True
				comment = False


			if line.startswith("H Table"):
				match = re.search(r'\(M=([\d.]+),Z=([\d.]+)\)', line)
				M = float(match.group(1))
				Z = float(match.group(2))
				tablestart = i

		# read last table
		df = read_csv(file_path, skip=tablestart, header=True, sep=r"\s*&")
		if (M, Z) in yields.keys():
			print(f"Duplicate found for M={M}, Z={Z}")
		yields[(M, Z)] = df

			
	return yields




def pivot_yields(yields, values="Yields"):
	"""
	Pivots the yields table so that the columns are (M, Z) and the rows are the isotopes.
	"""

	pivoted = {}

	for (M, Z), data in yields.items():
		if pivoted == {}:
			pivoted = {iso: [] for iso in data["Isotopes"]}

		for i, iso in enumerate(data["Isotopes"]):
			if iso not in pivoted:
				pivoted[iso] = {}
			pivoted[iso].append((M, Z, data[values][i]))

	return pivoted


def save_yields(elements, yields, Z):
	"""
	Given a dictionary where each key contains a list of tuples of (M, Z, y_net_fractional), saves the data to a file in VICE's AGB yield format.
	"""

	Ms = sorted(list(set([ys[0] for ys in yields["C-12"]])))
	Zs = sorted(list(set([ys[1] for ys in yields["C-12"]])))

	for ele in elements:
		filename = f"{ele.lower()}.dat"
		isos = []
		for iso in yields.keys():
			if iso.split("-")[0] == ele:
				isos.append(iso)

		with open(filename, 'w') as file:
			# header
			file.write(f"#M\tZ")
			for iso in isos:
				file.write(f"\t{iso.lower()}")
			file.write("\n")

			for M in Ms:
				if M >= 8:
					file.write(f"{M:e}\t{Z:e}")
					for iso in isos:
						y = yields[iso]
						idx = next(i for i in range(len(y)) if
				 np.isclose(y[i][0], M)
                  and np.isclose(y[i][1], Z)
				 )
						file.write(f"\t{y[idx][2]:e}")
					file.write("\n")


def save_all_yields(elements, yields_wind, yields_explosive, Z):
	if not os.path.isdir("v0"):
		os.mkdir("v0")
		os.mkdir("v0/explosive")
		os.mkdir("v0/wind")

	os.chdir("v0/explosive")
	Path("__init__.py").touch()
	save_yields(elements, yields_explosive, Z)
	os.chdir("../..")

	os.chdir("v0/wind")
	Path("__init__.py").touch()
	save_yields(elements, yields_wind, Z)
	os.chdir("../..")

def write_birth(df_elem, Z):
	with open("birth_composition.dat", "w") as file:
		df = df_elem[(12.0, Z)]

		for i in range(len(df["Isotopes"])):
			ele = df["Isotopes"][i].lower()
			Z0 = df["X0"][i]
			file.write(f"{ele}\t{Z0:e}\n")

def main():
	df_elem = read_element_yields("element_yield_table_MESAonly_fryer12_delay_total.txt")
	elements = df_elem[(1.0, 0.01)]["Isotopes"]

	yields_total = pivot_yields(read_element_yields("isotope_yield_table_MESAonly_fryer12_delay_total.txt"))
	#print(yields_total)
	yields_wind = pivot_yields(read_element_yields("isotope_yield_table_MESAonly_fryer12_delay_winds.txt"))

	yields_explosive = {key: [(a[0], a[1], a[2] - b[2]) for a, b in zip(yields_total[key], yields_wind[key])] for key in yields_total.keys()}

	for [dirname, Z] in [("FeH0p15", 0.02), ("FeH-0p15", 0.01), ("FeH-0p37",
															  0.006), ("FeH-1p15", 0.001), ("FeH-2p15", 0.0001)]:
		os.chdir("../" + dirname)
		Path("__init__.py").touch()
		save_all_yields(elements, yields_wind, yields_explosive, Z)
		write_birth(df_elem, Z)

if __name__ == "__main__":
	main()
