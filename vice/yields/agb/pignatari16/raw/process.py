import re
import os


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

	tablestart = -1
	tableend = -1
	comment = False
	table = False

	M_rem = None
	M = None
	Z = None

	with open(file_path, 'r') as file:
		for i, line in enumerate(file):
			if line.startswith("H"):
				if table:
					tableend = i
					df = read_csv(file_path, skip=tablestart, num_rows=tableend-tablestart, header=True, sep=r"\s*&")
					df["M_rem"] = M_rem
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

				if match is None:
					continue
				M = float(match.group(1))
				Z = float(match.group(2))
				tablestart = i
			
			# reads in reminant mass for the group
			if comment and line.startswith("H Mfinal"):
				M_rem = float(line.split()[2])


			
	return yields



def read_battino(file_path):
	"""Reads in the tables from either B19 or B21"""
	df =  read_csv(file_path, header=True, sep=r"\s+", comment="H ")
	df = sum_isotopes(df)
	
	return df


def sort_battino_eles(df, elements):
	"""Sorts each column in the dictionary `df` in the order of the arrays `elements`"""
	df_new = {
		k: [] for k in df.keys()
		}

	missing = set(df["Isotopes"]) - set(elements)
	if len(missing) > 0:
		print("warning, missing elements", missing)

	for ele in elements:
		idx = df["Isotopes"].index(ele)
		for k in df.keys():
			df_new[k].append(df[k][idx])
	
	return df_new




def sum_isotopes(data, iso_key="Isotope"):
	"""
	Sums the isotopes of an element in a dictionary
	where each column is a yield except for a column called Isotope.
	Returns a new dictionary.
	"""

	N = len(data[iso_key])
	summed_data = { "Isotopes": [] }

	for k in data.keys():
		if k == iso_key:
			continue
		summed_data[k] = []


	for i in range(N):
		iso = data[iso_key][i]
		ele = iso.split("-")[0]

		if ele not in summed_data["Isotopes"]:
			for k in data.keys():
				if k != iso_key:
					summed_data[k].append(float(data[k][i]))
			summed_data["Isotopes"].append(ele)
		else:
			j = summed_data["Isotopes"].index(ele)
			for k in data.keys():
				if k != iso_key:
					summed_data[k][j] += float(data[k][i])

	return summed_data


def calc_net_fractional(y, Z_A0, M, M_rem):
	r"""
	Calculates the net fractional yield of an element.

	**signature**: (y, Z0, M, M_rem) -> y_net_fractional

	Parameters
	----------
	y: `float`
		The total ejected mass yield of the element
	Z_A0: `float`
		The initial mass fraction of the element in the star
	M: `float`
		The initial (ZAMS) mass of the star
	M_rem: `float`
		The remnant mass of the star at the end of AGB evolution


	Returns
	-------
	y_net_fractional: `float`
		The net fractional yield of the element

	.. math::
	y_{\text{net}} = \frac{y - Z_A0 M_ej}{M}

	"""

	Mej = M - M_rem
	Z_A_ej = y / Mej
	return (Z_A_ej - Z_A0) * Mej / M




def pivot_yields(yields, values="y"):
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


def save_yields(yields):
	"""
	Given a dictionary where each key contains a list of tuples of (M, Z, y_net_fractional), saves the data to a file in VICE's AGB yield format.
	"""
	for ele, data in yields.items():
		filename = f"{ele.lower()}.dat"
		with open(filename, 'w') as file:
			for M, Z, y_net_fractional in sorted(data, key=lambda x: (x[0], x[1])):
				if M < 8:
					file.write(f"{M}\t{Z}\t{y_net_fractional}\n")



def add_net_fractional(yields):
	"""
	For each element in the yields dictionary, calculates the net fractional yield and adds it to the dictionary as a key y.
	"""
	for (M, Z), data in yields.items():
		M_rem = data["M_rem"]
		data["y"] = []

		for i, iso in enumerate(data["Isotopes"]):
			y_tot = data["Yields"][i]
			Z_A0 = data["X0"][i]
			y_net = calc_net_fractional(y_tot, Z_A0, M, M_rem)
			data["y"].append(y_net)
	
	return data


def main():
	yields = read_element_yields("element_yield_table_MESAonly_fryer12_delay_total.txt")

	elements = yields[(1.0, 0.01)]["Isotopes"]

	B19 = read_battino("B19.txt")
	B21 = read_battino("B21.txt")

	B19 = sort_battino_eles(B19, elements)
	B21 = sort_battino_eles(B21, elements)

	assert elements == B19["Isotopes"], "Isotopes do not match between Fryer and Battino"
	assert elements == B21["Isotopes"], "Isotopes do not match between Fryer and Battino"

	# adds in the updated yields
	yields[(2., 0.01)]["Yields"] = B19["m2z1m2"]
	yields[(3., 0.01)]["Yields"] = B19["m3z1m2"]
	yields[(2., 0.02)]["Yields"] = B19["m2z2m2"]
	yields[(3., 0.02)]["Yields"] = B19["m3z2m2"]
	yields[(2., 0.001)]["Yields"] = B21["m2z1m3-bigpoc"]
	yields[(3., 0.001)]["Yields"] = B21["m3z1m3-bigpoc"]


	add_net_fractional(yields)
	nf_yields = pivot_yields(yields)

	os.chdir("..")
	save_yields(nf_yields)



if __name__ == "__main__":
	main()
