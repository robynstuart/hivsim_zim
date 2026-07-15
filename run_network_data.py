"""
Run a small number of sims with network snapshot analyzers and save
the extracted network data used by `plot_network.py`. Uses the top-ranked
draw from exp_09 for calibrated params. Network structure is largely
input-driven so 3 seeds is enough.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import sciris as sc
import starsim as ss

REPO = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO))

from model import make_sim  # noqa: E402
from analyzers import HIVCascadeAnalyzer, NetworkSnapshot, PartnerAgePairs  # noqa: E402

OUT_DIR = REPO / 'outputs'
OUT_DIR.mkdir(exist_ok=True)
OUT_PATH = OUT_DIR / 'network_data.obj'

DRAWS_CSV = Path(os.environ.get(
    'DRAWS_CSV',
    REPO / 'experiments' / 'exp_09_extended_lhs' / 'outputs' / 'draws_top50.csv'))

N_SIMS = int(os.environ.get('N_SIMS', 3))
N_AGENTS = int(os.environ.get('N_AGENTS', 10_000))
SNAP_YEAR = int(os.environ.get('SNAP_YEAR', 2020))


CALIB_PAR_COLS = [
    'hiv.beta_m2f', 'hiv.rel_init_prev',
    'hiv.dur_on_art', 'hiv.rel_death', 'hiv.rel_death_on_art',
    'structuredsexual.prop_f0', 'structuredsexual.m2_conc',
    'structuredsexual.dur_sw',
]


def load_top_draw():
    df = pd.read_csv(DRAWS_CSV)
    row = df.iloc[0]  # already sorted by gof
    return {c: float(row[c]) for c in CALIB_PAR_COLS if c in df.columns}


def make_one(seed, calib_pars):
    sim = make_sim(
        seed=seed, n_agents=N_AGENTS, start=1985, stop=SNAP_YEAR + 1,
        calib_pars=calib_pars, verbose=0,
    )
    sim.pars.analyzers += [
        NetworkSnapshot(year=SNAP_YEAR),
        PartnerAgePairs(year=SNAP_YEAR),
    ]
    return sim


def extract(sims):
    data = sc.objdict()

    lp_f, lp_m = [], []
    fa, ma = [], []
    for sim in sims:
        snap = sim.analyzers['network_snapshot']
        lp_f.extend(list(snap.lifetime_partners_data['Female']))
        lp_m.extend(list(snap.lifetime_partners_data['Male']))
        pap = sim.analyzers['partner_age_pairs']
        fa.extend(list(pap.f_ages))
        ma.extend(list(pap.m_ages))
    data.lifetime_partners_f = np.array(lp_f)
    data.lifetime_partners_m = np.array(lp_m)
    data.f_ages = np.array(fa)
    data.m_ages = np.array(ma)

    snap = sims[0].analyzers['network_snapshot']
    data.risk_group_data = snap.risk_group_data
    data.debut_data = snap.debut_data

    stables, casuals = [], []
    for sim in sims:
        s = sim.analyzers['network_snapshot']
        stables.append(s.partnership_by_age['prop_stable'])
        casuals.append(s.partnership_by_age['prop_casual'])
    data.partnership_by_age = dict(
        age_bins=snap.partnership_by_age['age_bins'],
        prop_stable=np.nanmean(stables, axis=0),
        prop_casual=np.nanmean(casuals, axis=0),
    )

    sc.saveobj(OUT_PATH, data)
    print(f'wrote {OUT_PATH}')
    return data


def main():
    calib_pars = load_top_draw()
    print(f'Using top calibrated draw from {DRAWS_CSV.name}')
    sims = [make_one(seed=s, calib_pars=calib_pars) for s in range(1, N_SIMS + 1)]
    sims = ss.parallel(sims).sims
    extract(sims)


if __name__ == '__main__':
    main()
