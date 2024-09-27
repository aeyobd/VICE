import numpy as np
import re
import os

print("reading data")
def read_data(file_path, skip_rows):
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
            ele, _ = idx.split("-")
            if ele not in data:
                data[ele] = np.array([float(v) for v in values])
            else:
                data[ele] += np.array([float(v) for v in values])

    return data, header


def read_element_yields(file_path, elements):
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
            
            _, ele, y, x0, _ = line.split("&")
            y = float(y)
            x0 = float(x0)
            xf = y / M_ej
            y_net_fractional = (xf - x0) * M_ej / M

            ele = ele.strip()
            yields[ele].append((M, M_rem, Z, y, x0, y_net_fractional))
    
    return yields



def update_yields(yields, b_data, suffixes):
    for ele, data in yields.items():
        for idx, (M, M_rem, Z, y, x0, y_net_fractional) in enumerate(data):
            for i, suffix in enumerate(suffixes):
                if (M, Z) == suffix:
                    updated_y = b_data[i][ele]
                    if ele == "C":
                        print(f"Updating yield for {ele} at M={M}, Z={Z} from {y} to {updated_y}")
                    Mej = M - M_rem
                    xf = updated_y / Mej
                    y_net_fractional = (xf - x0) * Mej / M
                    new_row = (M, M_rem, Z, updated_y, x0, y_net_fractional)
                    yields[ele][idx] = new_row



def save_yields(yields):
    for ele, data in yields.items():
        filename = f"{ele.lower()}.dat"
        with open(filename, 'w') as file:
            for M, M_rem, Z, y, x0, y_net_fractional in sorted(data, key=lambda x: (x[0], x[2])):
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


def get_model(B_data, header, model):
    for i, h in enumerate(header):
        if model in h:
            return {ele: B_data[ele][i] for ele in B_data}


def main():
    elements = "H, He, Li, B, C, N, O, F, Ne, Na, Mg, Al, Si, P, Pb, S, Cl, Ar, K, Ca, Sc, Ti, V, Cr, Mn, Fe, Co, Ni, Cu, Zn, Ga, Ge, As, Se, Br, Kr, Rb, Sr, Y, Zr, Nb, Mo, Ru, Rh, Pd, Ag, Cd, In, Sn, Sb, Te, I, Xe, Cs, Ba, La, Ce, Pr, Nd, Sm, Eu, Gd, Tb, Dy, Ho, Er, Tm, Yb, Lu, Hf, Ta, W, Re, Os, Ir, Pt, Au, Hg, Tl, Bi".split(", ")

    yields = read_element_yields("element_yield_table_MESAonly_fryer12_delay_total.txt", elements)

    remove_duplicates(yields)
    B19, B19_header = read_data("B19.txt", 0)
    print(B19)
    B21, B21_header = read_data("B21.txt", 2)

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
        get_model(B19, B19_header, "m2z1m2"),
        get_model(B19, B19_header, "m3z1m2"),
        get_model(B19, B19_header, "m2z2m2"),
        get_model(B19, B19_header, "m3z2m2"),
        get_model(B21, B21_header, "m2z1m3-bigpoc"),
        get_model(B21, B21_header, "m3z1m3-bigpoc")
        ]


    update_yields(yields, models, suffixes)

    os.chdir("..")
    save_yields(yields)



if __name__ == "__main__":
    main()
