import vice
import numpy as np
from vice.toolkit.gaussian_stars.gaussian_stars import gaussian_stars
from vice.toolkit.hydrodisk.hydrodiskstars import hydrodiskstars

import sys
import gc
import os

from src.simulations.disks import star_formation_history
import src.yields
from src.yields import set_yields

MAX_SF_RADIUS = 15.5 #kpc
END_TIME = 13.2

def run_model(filename, prefix=None, 
              eta=1,
              beta=0.001,
              spec="insideout",
              agb_fraction=0.2,
              out_of_box_agb=False,
              agb_model="C11",
              lateburst_amplitude=1.5,
              fe_ia_factor=1,
              timestep=0.01,
              n_stars=2,
              alpha_n=0,
              test=False, # these are not used
              seed=None, 
              ratio_reduce=False):
    """
    This function wraps various settings to make running VICE multizone models
    easier for the carbon paper investigation
    
    Parameters
    ----------
    name: ``str``
        The name of the model
        
    migration_mode: ``str``
        Default value: diffusion
        The migration mode for the simulation. 
        Can be one of diffusion (most physical), linear, post-process, ???

    spec: ``str`` [default: "insideout"]
        The star formation specification. 
        Accepable values are
        - "insideout"
        - "constant"
        - "lateburst"
        - "outerburst"
        - "twoexp"
        - "threeexp"
        see vice.migration.src.simulation.disks.star_formation_history

    n_stars: ``int`` [default: 2]
        The number of stars to create during each timestep of the model.

    dt: ``float`` [default: 0.01]
        The timestep of the simulation, measured in Gyr.
        Decreasing this value can significantly speed up results

    burst_size: ``float`` [default: 1.5]
        The size of the SFH burst for lateburst model.

    eta_factor: ``float`` [default: 1]
        A factor by which to reduce the model's outflows. 

    ratio_reduce: ``bool``
        
    """

    # collects the first argument of the command as the directory to write
    # the simulation output to
    # this allows OSC to use the temperary directory
    if prefix is None:
        prefix = sys.argv[1]

    agb_model = {
            "C11": "cristallo11",
            "K10": "karakas10",
            "V13": "ventura13",
            "K16": "karakas16"
            }[agb_model]

    set_yields(eta=eta, beta=beta, fe_ia_factor=fe_ia_factor,
        agb_model=agb_model, oob=OOB, f_agb=f_agb, alpha_n=alpha_n)

    print("configured")

    zone_width = 0.1
    simple = False
    if migration_mode == "post-process":
        simple = True
        migration_mode = "diffusion"
    else:
        simple = False
    
    model = create_model()
    print(model)
    model.run(np.arange(0, END_TIME, timestep), overwrite=True, pickle=False)

    print("finished")



def create_model(timestep, spec, ratio_reduce):
    model = vice.milkyway(zone_width=zone_width,
            name=prefix + filename,
            n_stars=n_stars,
            verbose=False,
            N = Nstars,
            simple=simple
            )

    model.elements = ("fe", "o", "mg", "n", "c", "au", "ag")
    model.mode = "sfr"
    model.dt = timestep
    model.bins = np.arange(-3, 3, 0.01)
            

    Nstars = 2*MAX_SF_RADIUS/zone_width * END_TIME/dt * n_stars


    if migration_mode != "gaussian" and Nstars > N_MAX:
        Nstars = N_MAX

    print("using %i stars particles" % Nstars)

    model.evolution = create_evolution()


    model.mass_loading = create_mass_loading()


    return model




def create_evolution():
    if spec == "lateburst":
        evolution = star_formation_history(spec = spec,
                zone_width = zone_width,
                burst_size = burst_size)
    elif spec == "twoexp":
        evolution = star_formation_history(spec = spec,
                zone_width = zone_width, timescale2=1, amplitude=burst_size, t1=5)
    elif spec == "threeexp":
        evolution = star_formation_history(spec = spec,
                zone_width = zone_width, timescale2=1, amplitude=burst_size, 
                t1=5, amplitude3=0.2, t2=12)
    else:
        evolution = star_formation_history(spec = spec,
                zone_width = zone_width)

    return evolution


def create_mass_loading():
    # for changing value of eta
    if ratio_reduce:
        def mass_loading(R):
            eta_0 = model.default_mass_loading(R)
            r = 0.4 # this is an approximation
            eta =  (1 - r) * (eta_factor - 1) + eta_factor * eta_0
            if eta < 0:
                eta = 0
            return eta
        mass_loading = mass_loading
    else:
        mass_loading = lambda R: model.default_mass_loading(R) * eta_factor

    return mass_loading



