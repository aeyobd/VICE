import sys
import argparse
import vice

from surp import __version__

y_cc_0 = 0.005
beta_n = 7e-4
y_cc_n = 9e-4


def main():
    args = parse_args()
    f_agb = args.agb_fraction
    beta = args.beta
    agb_model = args.agb_model
    eta = args.eta
    A = args.lateburst_amplitude
    lateburst = args.lateburst


    name = find_name(args)
    print(name)
    return name

def parse_args():
    parser = argparse.ArgumentParser(description="Runs a multizone model")

    parser.add_argument("prefix", help = "directory where to put outputs/ in ")
    parser.add_argument("-e", "--eta", help = "outflow factor", type=float, default=1)
    parser.add_argument("-b", "--beta", help = "C CCSNe Z-dependence",
            type=float, default=0.001)

    parser.add_argument("-l", "--lateburst", help = "sets sfh to lateburst", action="store_true")
    parser.add_argument("-f", "--agb_fraction", help="The fractional C AGB contribution", type=float, default=0.2)

    parser.add_argument("-o", "--out_of_box_agb", help="Use the published (unamplified) agb table yields. Overrides -f option", action="store_true")

    parser.add_argument("-m", "--agb_model", help="The AGB yield set to use",
            type=str, default="C11", 
                        choices=["C11", "K10", "V13", "K16"])

    parser.add_argument("-n", "--filename", help="The name of the file to write the output to")
    parser.add_argument("-A", "--lateburst_amplitude", help="The amplitude of the lateburst", type=float, default=1.5)

    parser.add_argument("-i", "--fe_ia_factor", help="The factor by which to chante SneIa Fe contribution", type=float)

    parser.add_argument("-t", "--traditional_f", help="Sets the AGB fraction to only imf averaged as is typical defined", action="store_false")

    args = parser.parse_args()

    return args


def find_name(args):
    f_agb = args.agb_fraction
    beta = args.beta
    agb_model = args.agb_model
    eta = args.eta
    A = args.lateburst_amplitude
    lateburst = args.lateburst
    trad = args.traditional_f
    oob = args.out_of_box_agb

    if args.filename:
        name = args.filename
    else:
        if oob:
            f_agb = "o"

        name = f"{agb_model}_f{f_agb}_Z{beta}_eta{eta}"

        if A == 1.5:
            pass
        else:
            name += "_A%s" % A

        if lateburst:
            name += "_lateburst"

        if not trad:
            name += "_adjf"

        if args.fe_ia_factor:
            name += "_ia%s" % args.fe_ia_factor

        name += f"_v{__version__}"

    return name


if __name__ == "__main__":
    main()
