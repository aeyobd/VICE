import argparse
import subprocess


def parse_args():
    parser = argparse.ArgumentParser(description="Argument parser")

    parser.add_argument("-e", "--eta", type=float, default=1,
                        help="the efficiency multiplier of the supernova feedback")
    parser.add_argument("-b", "--beta", type=float, default=0.001, 
                        help="the power-law index of the star formation law")
    parser.add_argument("-s", "--spec", default="insideout", 
                        help="sf spec")
    parser.add_argument("-f", "--agb_fraction", type=float, default=0.2, 
                        help="the mass fraction of AGB stars in the initial mass function ")
    parser.add_argument("-o", "--out_of_box_agb", action="store_true", 
                        help="use an out-of-box AGB model ")
    parser.add_argument("-m", "--agb_model", default="C11", 
                        help="the name of the AGB model to use ")
    parser.add_argument("-F", "--filename", default=None,
                        help="the name of the output file ")
    parser.add_argument("-A", "--lateburst_amplitude", type=float, default=1.5, 
                        help="the amplitude of the late burst")
    parser.add_argument("-i", "--fe_ia_factor", default="None", 
                        help="the iron yield factor of type Ia supernovae ")
    parser.add_argument("-d", "--timestep", type=float, default=0.01, 
                        help="the size of the time step ")
    parser.add_argument("-n", "--n_stars", type=int, default=2, 
                        help="the number of stars")
    parser.add_argument("-a", "--alpha_n", type=float, default=0, 
                        help="the agb fraction of primary N (0.0)")
    parser.add_argument("-t", "--test", action="store_true", 
                        help="only run a test")
    return parser.parse_args()


def generate_filename(args):
    filename = args.agb_model

    if args.out_of_box_agb:
        filename += "_OOB"
    else:
        filename += "_f" + str(args.agb_fraction)

    filename += "_eta" + str(args.eta) + "_beta" + str(args.beta)

    if args.spec != "insideout":
        filename += "_" + args.spec + str(args.lateburst_amplitude)

    if args.fe_ia_factor != "None":
        filename += "_Fe" + str(args.fe_ia_factor)

    if args.timestep != 0.01:
        filename += "_dt" + str(args.timestep)

    if args.alpha_n != 0:
        filename += "_an" + str(args.alpha_n)

    return filename


def create_pycall(filename, args):
    # create call to python script
    pycall = f"""
from src.simulate import main
import sys
path = sys.argv[1]

main(path
    "{filename}",
     eta={args.eta}, 
     beta={args.beta}, 
     spec="{args.spec}",
     f_agb={args.agb_fraction},
     OOB={args.out_of_box_agb},
     agb_model="{args.agb_model}",
     A={args.lateburst_amplitude},
     fe_ia_factor={args.fe_ia_factor},
     dt={args.timestep},
     n_stars={args.n_stars},
     alpha_n={args.alpha_n}
    )
"""
    return pycall





if __name__ == "__main__":
    args = parse_args()
    filename = args.filename

    if not filename:
        filename = generate_filename(args)

    print(filename)

    pycall = create_pycall(filename, args)
    print(pycall)

    if "$test_run":
        from src.simulations import multizone_run
        multizone_run(".", filename, **args)
    else:
        subprocess.call(["bash", "simulate.sh", filename, pycall])




