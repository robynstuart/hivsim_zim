"""
HIVsim Zimbabwe: HIV-only model on the Starsim / STIsim stack.

Slim wrapper around stisim's HIV module + StructuredSexual network +
Zimbabwe demographics. Calibration parameters (HIV beta, initial-prev
scaling, network shape) can be overridden via `calib_pars`.

The calibration this repo ships with was joint HIV + syphilis + NG/CT/TV/BV
in the sti_notification project. When run HIV-only, dropping the STIs
removes weak HIV-syph coupling; HIV trajectories are essentially unchanged
because the coupling in that calibration was `hiv -> syph` (susceptibility
of HIV+ to syph), not the reverse.
"""

import pandas as pd
import starsim as ss
import stisim as sti

from hiv_model import make_hiv, make_hiv_intvs

LOCATION = 'zimbabwe'
DATA_DIR = 'data'


def make_networks():
    sexual = sti.StructuredSexual(
        prop_f0=0.67, prop_m0=0.55,
        prop_f2=0.10, prop_m2=0.20,
        concurrency_dist=ss.nbinom(n=2, p=0.5),
        f1_conc=0.15, m1_conc=0.20,
        f2_conc=1.0, m2_conc=4.4,
        recall_prior=True,
        condom_data=pd.read_csv(f'{DATA_DIR}/condom_use.csv'),
        fsw_shares=ss.bernoulli(p=0.10),
        client_shares=ss.bernoulli(p=0.20),
        sw_seeking_rate=ss.permonth(20),
    )
    return [sexual, ss.MaternalNet()]


def apply_calib_pars(sim, calib_pars):
    """Override module parameters from a calibration row.

    `calib_pars` is a dict keyed on `module.param`, e.g.
    {'hiv.beta_m2f': 0.012, 'structuredsexual.prop_f0': 0.7}.

    stisim's Sim stores modules in lists rather than dicts, so we
    resolve each override by matching module.name.
    """
    if not calib_pars:
        return sim
    for key, val in calib_pars.items():
        mod_name, par = key.split('.', 1)
        # Search across diseases, networks, and connectors.
        containers = [sim.diseases, sim.networks]
        if getattr(sim, 'connectors', None):
            containers.append(sim.connectors)
        for container in containers:
            for mod in container.values() if hasattr(container, 'values') else container:
                if getattr(mod, 'name', None) == mod_name:
                    mod.pars[par] = val
    return sim


def make_sim(seed=1, n_agents=1e4, start=1985, stop=2040,
             calib_pars=None, verbose=1/12):
    """Build a Zimbabwe HIV sim. 1985 default start matches the calibration."""
    hiv = make_hiv()
    interventions = make_hiv_intvs()
    networks = make_networks()

    simpars = dict(
        rand_seed=seed, n_agents=n_agents,
        start=start, stop=stop,
        use_migration=False, verbose=verbose,
        total_pop=8.7e6,  # actual 1985 Zimbabwe population
    )
    sim = sti.Sim(
        pars=simpars,
        datafolder=f'{DATA_DIR}/',
        demographics=LOCATION,
        diseases=[hiv],
        networks=networks,
        interventions=interventions,
    )
    sim.init()
    apply_calib_pars(sim, calib_pars)
    return sim


if __name__ == '__main__':
    sim = make_sim(seed=1, start=1985, stop=1990, n_agents=1000)
    sim.run()
    print(f'HIV prev (final): {sim.results.hiv.prevalence[-1]:.4f}')
