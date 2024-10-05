import re
import os

elements = "H, He, Li, B, C, N, O, F, Ne, Na, Mg, Al, Si, P, Pb, S, Cl, Ar, K, Ca, Sc, Ti, V, Cr, Mn, Fe, Co, Ni, Cu, Zn, Ga, Ge, As, Se, Br, Kr, Rb, Sr, Y, Zr, Nb, Mo, Ru, Rh, Pd, Ag, Cd, In, Sn, Sb, Te, I, Xe, Cs, Ba, La, Ce, Pr, Nd, Sm, Eu, Gd, Tb, Dy, Ho, Er, Tm, Yb, Lu, Hf, Ta, W, Re, Os, Ir, Pt, Au, Hg, Tl, Bi".split(", ")

def read_battino(file_path, skip_rows):
    data = {}
    with open(file_path, 'r') as file:
        for _ in range(skip_rows):
            next(file)

        header_line = next(file).strip()
        header = re.split(r'\s+', header_line)

        for line in file:
            parts = re.split(r'\s+', line.strip())
            idx = parts[0]
            values = parts[1:]
            data[idx] = [float(v) for v in values]

    return data, header

def sum_isotopes(data):
    summed_data = {}
    for iso in data:
        ele = iso.split("-")[0]
        dat = data[iso]

        if ele not in summed_data:
            summed_data[ele] = dat
        else:
            old = summed_data[ele].copy()
            summed_data[ele] = [x + y for x, y in zip(old, dat)]

    return summed_data


def calc_net_fractional(y, Z_A0, M, M_rem):
    Mej = M - M_rem
    Z_A_ej = y / Mej
    return (Z_A_ej - Z_A0) * Mej / M


def read_element_yields(file_path, elements):
    """
    Reads in the yields from the Fryer et al. 2012 table

    Returns a dictionary of lists of tuples:

    {
        "H" : [(M, M_rem, Z, y, Z_A0), ...],
        "He" : [(M, M_rem, Z, y, Z_A0), ...],
        ...
    }

    where the keys of the dictionary each correspond to an element, 
    each "row" of the list corresponds to an initial mass and metallicity pair,
    and each tuple inside the list is the tuple of 

    1. initial mass
    2. reminant mass,
    3. initial metallicity
    4. total yield of the element
    5. initial mass fraction of the element

    """

    yields = {ele: [] for ele in elements}
    skip = 6
    M = None
    M_ej = None
    with open(file_path, 'r') as file:
        for line in file:
            if skip > 0:
                skip -= 1
                continue

            # reads in mass / metallicity for each group
            if line.startswith("H Table"):
                match = re.search(r'\(M=([\d.]+),Z=([\d.]+)\)', line)

                if match is None:
                    continue
                M = float(match.group(1))
                Z = float(match.group(2))

                skip = 1
                continue
            
            # reads in reminant mass for the group
            if line.startswith("H Mfinal"):
                M_rem = float(line.split()[2])
                M_ej = M - M_rem
                skip = 1
                continue
            
            _, ele, y, Z_A0, _ = line.split("&")
            y = float(y)
            Z_A0 = float(Z_A0)

            ele = ele.strip()

            yields[ele].append((M, M_rem, Z, y, Z_A0))
    
    return yields



def update_yields(yields, b_data, suffixes):

    for ele, data in yields.items():
        for idx, (M, M_rem, Z, y, Z_A0) in enumerate(data):
            for i, suffix in enumerate(suffixes):
                if (M, Z) == suffix:
                    updated_y = b_data[i][ele]
                    if ele == "C":
                        print(f"Updating C yield for {ele} at M={M}, Z={Z} from {y} to {updated_y}")

                    new_row = (M, M_rem, Z, updated_y, Z_A0)
                    yields[ele][idx] = new_row

    return yields



def save_yields(yields):
    for ele, data in yields.items():
        filename = f"{ele.lower()}.dat"
        with open(filename, 'w') as file:
            for M, Z, y_net_fractional in sorted(data, key=lambda x: (x[0], x[1])):
                if M < 8:
                    file.write(f"{M}\t{Z}\t{y_net_fractional}\n")


def remove_duplicates(yields):
    for ele in yields:
        seen = set()
        unique_yields = []
        for entry in yields[ele]:
            M_Z_pair = (entry[0], entry[2])  # (M, Z)
            if M_Z_pair not in seen:
                seen.add(M_Z_pair)
                unique_yields.append(entry)
            else:
                print(f"Duplicate found and removed for element {ele} at M={entry[0]}, Z={entry[2]}")
        yields[ele] = unique_yields


def make_net_fractional(yields):
    nf_yields = {}

    for ele in yields:
        nf_yields[ele] = []
        for idx, entry in enumerate(yields[ele]):
            M, M_rem, Z, y, Z_A0 = entry
            y_net_fractional = calc_net_fractional(y, Z_A0, M, M_rem)

            nf_yields[ele].append((M, Z, y_net_fractional))

    return nf_yields

def get_battino_model(B_data, header, model):
    for i, h in enumerate(header):
        if model in h:
            return {ele: B_data[ele][i] for ele in B_data}


def main():
    yields = read_element_yields("element_yield_table_MESAonly_fryer12_delay_total.txt", elements)

    remove_duplicates(yields)
    B19, B19_header = read_battino("B19.txt", 0)
    B21, B21_header = read_battino("B21.txt", 2)
    B19 = sum_isotopes(B19)
    B21 = sum_isotopes(B21)
    print(B19["C"])

    print(B19_header)
    print(B21_header)


    suffixes = [
        (2., 0.01), 
        (3., 0.01), 
        (2., 0.02), 
        (3., 0.02),
        (2., 0.001), 
        (3., 0.001)
    ]
    models = [
        get_battino_model(B19, B19_header, "m2z1m2"),
        get_battino_model(B19, B19_header, "m3z1m2"),
        get_battino_model(B19, B19_header, "m2z2m2"),
        get_battino_model(B19, B19_header, "m3z2m2"),
        get_battino_model(B21, B21_header, "m2z1m3-bigpoc"),
        get_battino_model(B21, B21_header, "m3z1m3-bigpoc")
        ]


    update_yields(yields, models, suffixes)
    nf_yields = make_net_fractional(yields)

    os.chdir("..")
    save_yields(nf_yields)



if __name__ == "__main__":
    main()
