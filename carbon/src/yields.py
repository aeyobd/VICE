import vice
import numpy as np
from vice.yields.agb import interpolator
from scipy.integrate import quad
from vice.yields import ccsne, sneia, agb


Z_Sun = 0.014
y_c_0 = 0.005
y_c_cc_0=0.0028
y_n_flat = 7.2e-4



YC_AGB0 = {
        "cristallo11": 3.47e-4,
        "karakas10": 5.85e-4,
        "ventura13": 6.0e-5,
        "karakas16": 4.21e-4
}

# default settings


def set_yields(eta=1, beta=0.001, fe_ia_factor=None,
               agb_model="cristallo11", oob=False, f_agb=0.2,
               alpha_n=0.5, ):

    set_fe(fe_ia_factor)

    alpha_agb, alpha_cc = calc_alpha(agb_model, eta, oob, f_agb)
    set_agb(agb_model, alpha_agb)

    set_n(eta, alpha_n)
    
    prefactor = y_c_0 * alpha_cc / (y_c_cc_0 + beta)
    vice.yields.ccsne.settings["c"] = LinCC(zeta=beta*prefactor, y0=prefactor*y_c_cc_0)

    set_eta(eta)

    print_yields()





class LinAGB:
    def __init__(self, zeta, y0):
        self.zeta = zeta
        self.y0 = y0

    def __call__(self, M, Z):
        return M*self.y0 + M*Z/Z_Sun * self.zeta

    def __str__(self):
        return f"{self.y0:0.2e} M + {self.zeta:0.2e} M Z/Z0"




class LinCC:
    def __init__(self, zeta, y0):
        self.zeta = zeta
        self.y0 = y0

    def __call__(self, Z):
        return self.y0 + self.zeta*(Z/Z_Sun) 

    def __str__(self):
        return f"{self.y0:0.2e} + {self.zeta:0.2e} Z/Z0"


def set_defaults():
    ccsne.settings["o"] = 0.015
    sneia.settings["o"] = 0

    ccsne.settings["fe"] = 0.0012
    sneia.settings["fe"] = 0.0017
    # sneia.settings["fe"] *= 10**0.1 # correction for mdf, used in

    ccsne.settings["sr"] = 3.5e-8
    sneia.settings["sr"] = 0

    ccsne.settings["n"] = 3.6e-4

    sneia.settings["c"] = 0
    sneia.settings["n"] = 0

    ccsne.settings["mg"] = 0.00185
    sneia.settings["mg"] = 0

set_defaults()




def set_agb_elem(elem, study, factor):
    if elem == "fe" and agb_model == "ventura13":
        study = "cristallo11"

    agb.settings[elem] = interpolator(elem, study, prefactor=factor)



def set_agb(study="cristallo11", factor=1):
    for elem in ["c", "o", "mg"]:
        set_agb_elem(elem, study, factor)


def set_fe(fe_ia_factor):
    if fe_ia_factor:
        fe_total = vice.yields.sneia.settings["fe"] + vice.yields.ccsne.settings["fe"]
        fe_ia = vice.yields.sneia.settings["fe"] * fe_ia_factor
        fe_cc = fe_total - fe_ia
        vice.yields.ccsne.settings["fe"] = fe_cc
        vice.yields.sneia.settings["fe"] = fe_ia



def set_eta(eta=1):
    if eta==1:
        return

    for elem in ["o", "fe", "mg", "sr", "n", "c"]:
        y = ccsne.settings[elem] 
        if isinstance(y, float):
            ccsne.settings[elem] *= eta

        y = sneia.settings[elem] 
        if isinstance(y, float):
            sneia.settings[elem] *= eta


def set_n(eta, alpha_n):
    y_cc_n = eta*y_n_flat * (1-alpha_n)
    y_n_0 = eta*y_n_flat * alpha_n
    vice.yields.agb.settings["n"] = LinAGB(zeta=9e-4, y0=y_n_0)
    vice.yields.ccsne.settings["n"] = y_cc_n





def calc_alpha(agb_model="cristallo11" , eta=1, oob=False, f_agb=0.2):
    y_agb = YC_AGB0[agb_model]
    y_c = y_c_0 * eta

    if oob:
        alpha_agb = 1
        f_agb = YC_AGB0[agb_model]/y_c_0
    else:
        alpha_agb = f_agb*y_c/y_agb

    alpha_cc = eta * (1 - f_agb)

    return alpha_agb, alpha_cc





def print_yields():
    # print header
    print("Yield settings")
    print_row("X", "CC", "agb", "SN Ia")

    # print values
    for elem in ["c", "n", "o", "mg", "fe"]:
        print_row(elem, 
                ccsne.settings[elem],
                agb.settings[elem],
                sneia.settings[elem])

    print()
    print()



def print_row(*args):
    for i in range(len(args)):
        arg = args[i]
        if isinstance(arg, float):
            s = "%0.2e" % arg
        else:
            s = str(arg)

        if i==0:
            print(f"{s:8}", end="")
        elif i==(len(args)-1):
            print(f"{s}", end="")
        else:
            print(f"{s:30}", end="")
    print()

