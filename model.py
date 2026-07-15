"""
HIVsim Zimbabwe: HIV-only model created using STIsim.
Calibration parameters (HIV beta, initial-prev scaling, network shape)
can be overridden via `calib_pars`.
"""

import pandas as pd
import starsim as ss
import stisim as sti

from analyzers import HIVCascadeAnalyzer
from hiv_model import make_hiv, make_hiv_intvs

LOCATION = 'zimbabwe'
DATA_DIR = 'data'


def make_networks(dur_recall=ss.years(0.25), condom_data=None):
    if condom_data is None:
        condom_data = pd.read_csv(f'{DATA_DIR}/condom_use.csv')
    sexual = sti.StructuredSexual(
        prop_f0=0.67, prop_m0=0.55,
        prop_f2=0.10, prop_m2=0.20,
        concurrency_dist=ss.nbinom(n=2, p=0.5),
        f1_conc=0.15, m1_conc=0.20,
        f2_conc=1.0, m2_conc=4.4,
        recall_prior=True,
        condom_data=condom_data,
        fsw_shares=ss.bernoulli(p=0.10),
        client_shares=ss.bernoulli(p=0.20),
        sw_seeking_rate=ss.permonth(20),
    )
    return [sexual, sti.PriorPartners(dur_recall=dur_recall), ss.MaternalNet()]


def apply_calib_pars(sim, calib_pars):
    """Override module parameters from a calibration row.

    `calib_pars` is a dict keyed on `module.param`, e.g.
    {'hiv.beta_m2f': 0.012, 'structuredsexual.dur_sw': 5.0}.

    stisim's Sim stores modules in lists rather than dicts, so we
    resolve each override by matching module.name. Values that map
    onto starsim distributions (e.g. `dur_sw`) go through `.set(mean=..)`;
    plain scalars overwrite directly.
    """
    if not calib_pars:
        return sim
    for key, val in calib_pars.items():
        mod_name, par = key.split('.', 1)
        for category in ('diseases', 'networks', 'interventions',
                         'connectors', 'analyzers', 'demographics'):
            container = sim.pars.get(category)
            if not container:
                continue
            for mod in container:
                if getattr(mod, 'name', None) == mod_name:
                    existing = mod.pars.get(par) if hasattr(mod, 'pars') else None
                    if hasattr(existing, 'set'):
                        existing.set(mean=val)
                    else:
                        mod.pars[par] = val
                    break
    return sim


DEM_MODULES = {'migration', 'pregnancy', 'deaths'}


def make_sim(seed=1, n_agents=1e4, start=1985, stop=2040,
             calib_pars=None, verbose=1/12, condom_data=None):
    """Build a Zimbabwe HIV sim. 1985 default start matches the calibration."""
    hiv = make_hiv()
    interventions = make_hiv_intvs()
    networks = make_networks(condom_data=condom_data)

    # Demographics come from the 'zimbabwe' location string and are only
    # resolved into modules during sti.Sim's init. Params targeting those
    # modules must be routed through the dem_pars kwarg — apply_calib_pars
    # can't touch them post-hoc because sim.pars.demographics is still a
    # string at that point.
    # rel_migration=0.5 fixed from exp_03 point-value scan: halves the
    # UN-WPP net migration outflows to match Zimbabwe pop 1990-2024 within
    # ~3% at every UNAIDS survey year.
    calib_pars = dict(calib_pars or {})
    dem_pars = {'rel_migration': 0.5}
    for key in list(calib_pars):
        mod_name, par = key.split('.', 1)
        if mod_name in DEM_MODULES:
            dem_pars[par] = calib_pars.pop(key)

    simpars = dict(
        rand_seed=seed, n_agents=n_agents,
        start=start, stop=stop,
        use_migration=True, verbose=verbose,
        total_pop=8.7e6,  # actual 1985 Zimbabwe population
    )
    sim = sti.Sim(
        pars=simpars,
        datafolder=f'{DATA_DIR}/',
        demographics=LOCATION,
        dem_pars=dem_pars,
        diseases=[hiv],
        networks=networks,
        interventions=interventions,
        analyzers=[HIVCascadeAnalyzer()],
    )
    # Apply remaining calib pars BEFORE init: while sim.pars containers are
    # still lists. After sim.init() they become objdicts/ndicts and the
    # list-iteration in apply_calib_pars silently no-ops.
    apply_calib_pars(sim, calib_pars)
    return sim


if __name__ == '__main__':
    sim = make_sim(seed=1, start=1985, stop=1990, n_agents=1000)
    sim.run()
    print(f'HIV prev (final): {sim.results.hiv.prevalence[-1]:.4f}')
