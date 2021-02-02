"""
Created at 25.09.2019
"""

from typing import Iterable

import numba
import numpy
import numpy as np
import scipy

import PySDM
from PySDM.dynamics import condensation
from PySDM.dynamics.coalescence.kernels import Geometric
from PySDM.initialisation.spectra import Lognormal
from PySDM.initialisation.spectra import Sum
from PySDM.physics import constants as const
from PySDM.physics import formulae as phys
from PySDM.physics.constants import si


# from PyMPDATA import __version__ as TODO #339


class Settings:
    def __dir__(self) -> Iterable[str]:
        return 'dt', 'grid', 'size', 'n_spin_up', 'versions', 'outfreq'

    def __init__(self):
        key_packages = (PySDM, numba, numpy, scipy)
        self.versions = str({pkg.__name__: pkg.__version__ for pkg in key_packages})

    # TODO #308 move all below into __init__ as self.* variables

    condensation_coord = 'volume logarithm'

    condensation_rtol_x = condensation.default_rtol_x
    condensation_rtol_thd = condensation.default_rtol_thd
    condensation_adaptive = True

    coalescence_adaptive = True

    grid = (25, 25)
    size = (1500 * si.metres, 1500 * si.metres)
    n_sd_per_gridbox = 20
    rho_w_max = .6 * si.metres / si.seconds * (si.kilogram / si.metre ** 3)

    # output steps
    simulation_time = 90 * si.minute
    output_interval = 1 * si.minute
    dt = 5 * si.second
    spin_up_time = 1 * si.hour

    @property
    def n_steps(self) -> int:
        return int(self.simulation_time / self.dt) #TODO

    @property
    def steps_per_output_interval(self) -> int:
        return int(self.output_interval / self.dt)

    @property
    def n_spin_up(self) -> int:
        return int(self.spin_up_time / self.dt)

    v_bins = phys.volume(np.logspace(np.log10(0.001 * si.micrometre), np.log10(100 * si.micrometre), 101, endpoint=True))

    @property
    def output_steps(self) -> np.ndarray:
        return np.arange(0, self.n_steps + 1, self.steps_per_output_interval)

    mode_1 = Lognormal(
        norm_factor=60 / si.centimetre ** 3 / const.rho_STP,
        m_mode=0.04 * si.micrometre,
        s_geom=1.4
    )
    mode_2 = Lognormal(
      norm_factor=40 / si.centimetre**3 / const.rho_STP,
      m_mode=0.15 * si.micrometre,
      s_geom=1.6
    )
    spectrum_per_mass_of_dry_air = Sum((mode_1, mode_2))


    processes = {
        "particle advection": True,
        "fluid advection": True,
        "coalescence": True,
        "condensation": True,
        "sedimentation": True,
        # "relaxation": False  # TODO #338
    }

    enable_particle_temperatures = False

    mpdata_iters = 2
    mpdata_iga = True
    mpdata_fct = True
    mpdata_tot = True

    th_std0 = 289 * si.kelvins
    qv0 = 7.5 * si.grams / si.kilogram
    p0 = 1015 * si.hectopascals
    kappa = 1

    @property
    def field_values(self):
        return {
            'th': phys.th_dry(self.th_std0, self.qv0),
            'qv': self.qv0
        }

    @property
    def n_sd(self):
        return self.grid[0] * self.grid[1] * self.n_sd_per_gridbox

    def stream_function(self, xX, zZ):
        X = self.size[0]
        return - self.rho_w_max * X / np.pi * np.sin(np.pi * zZ) * np.cos(2 * np.pi * xX)

    def rhod(self, zZ):
        Z = self.size[1]
        z = zZ * Z  # :(!

        # TODO #337 move to PySDM/physics
        # hydrostatic profile
        kappa = const.Rd / const.c_pd
        arg = np.power(self.p0/const.p1000, kappa) - z * kappa * const.g / self.th_std0 / phys.R(self.qv0)
        p = const.p1000 * np.power(arg, 1/kappa)

        # density using "dry" potential temp.
        pd = p * (1 - self.qv0 / (self.qv0 + const.eps))
        rhod = pd / (np.power(p / const.p1000, kappa) * const.Rd * self.th_std0)

        return rhod

    kernel = Geometric(collection_efficiency=1)
    aerosol_radius_threshold = .5 * si.micrometre
    drizzle_radius_threshold = 25 * si.micrometre
