"""
Exp 07 — Point-value scan of hiv.dur_on_art.

Scan dur_on_art in {3, 10, 20} years mean, other priors at midpoints,
aggressive condom schedule (from exp_06). 5 seeds per value = 15 sims.
Adds a post-ART fraction panel to the diagnostic figure so we can
see churn collapse directly.
"""
from __future__ import annotations

import multiprocessing as mp
import os
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

os.environ.update(OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1',
                  NUMEXPR_NUM_THREADS='1', MKL_NUM_THREADS='1')

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
sys.path.insert(0, str(REPO))

from model import make_sim  # noqa: E402
from utils import set_font  # noqa: E402

set_font(size=12)

N_SEEDS   = int(os.environ.get('N_SEEDS', 5))
N_WORKERS = int(os.environ.get('N_WORKERS', 15))
N_AGENTS  = int(os.environ.get('N_AGENTS', 10_000))

OUT_DIR = HERE / 'outputs'
FIG_DIR = HERE / 'figures'
OUT_DIR.mkdir(exist_ok=True)
FIG_DIR.mkdir(exist_ok=True)

FIXED_PARS = {
    'hiv.beta_m2f':              0.0225,
    'hiv.rel_init_prev':         0.9,
    'structuredsexual.prop_f0':  0.725,
    'structuredsexual.m2_conc':  5.0,
    'structuredsexual.dur_sw':   8.5,
}

DUR_ON_ART_VALUES = [3, 10, 20]

CROSS_RISK = ['(0,1)', '(0,2)', '(1,0)', '(1,2)', '(2,0)', '(2,1)']

RESULT_COLS = [
    'hiv.prevalence_15_49', 'hiv.n_infected', 'hiv.n_on_art',
    'hiv.n_post_art', 'hiv.new_infections', 'hiv.new_deaths',
    'n_alive',
]


def aggressive_condom_df():
    d = pd.read_csv(REPO / 'data' / 'condom_use.csv')
    bumps = {'2010': 0.90, '2015': 0.95, '2020': 0.95}
    for pship in CROSS_RISK:
        row_idx = d.index[d.partnership == pship]
        for col, val in bumps.items():
            d.loc[row_idx, col] = val
    return d


def extract_ts(sim, dur_on_art, seed):
    ann = sim.results.annualize()
    years = ann.n_alive.timevec.years.astype(int)
    out = {'year': years, 'dur_on_art': dur_on_art, 'seed': seed}
    for col in RESULT_COLS:
        if '.' in col:
            mod, name = col.split('.', 1)
            out[col] = ann[mod][name]
        else:
            out[col] = ann[col]
    return pd.DataFrame(out)


def worker(args):
    dur_on_art, seed = args
    calib_pars = {**FIXED_PARS, 'hiv.dur_on_art': dur_on_art}
    try:
        sim = make_sim(seed=seed, n_agents=N_AGENTS,
                       start=1985, stop=2040, calib_pars=calib_pars,
                       verbose=0, condom_data=aggressive_condom_df())
        sim.run()
        return extract_ts(sim, dur_on_art, seed)
    except Exception as e:
        print(f'[dur={dur_on_art} seed={seed}] failed: {e}', flush=True)
        return None


PALETTE = {3: '#e2b64e', 10: '#8b6ba1', 20: '#2b8ea1'}


def plot(ts, targets):
    # Derived series
    ts['post_art_frac'] = ts['hiv.n_post_art'] / ts['hiv.n_infected'].where(ts['hiv.n_infected'] > 0)
    ts['on_art_frac']   = ts['hiv.n_on_art']   / ts['hiv.n_infected'].where(ts['hiv.n_infected'] > 0)

    panels = [
        ('hiv.n_infected',     'PLHIV', 1e-6, 'millions', 'hiv.n_infected'),
        ('post_art_frac',      'Post-ART fraction of PLHIV', 1.0, '', None),
        ('on_art_frac',        'On-ART fraction of PLHIV', 1.0, '', None),
        ('hiv.new_infections', 'New HIV infections/yr', 1e-3, 'thousands', 'hiv.new_infections'),
        ('hiv.new_deaths',     'AIDS-related deaths/yr', 1e-3, 'thousands', 'hiv.new_deaths'),
        ('hiv.prevalence_15_49', 'HIV prevalence, 15-49', 1.0, '', 'hiv.prevalence_15_49'),
    ]
    fig, axes = plt.subplots(2, 3, figsize=(13, 7), sharex=True)
    for ax, (sim_col, title, scale, unit, targ_col) in zip(axes.flat, panels):
        for dur in DUR_ON_ART_VALUES:
            g = ts[ts.dur_on_art == dur]
            by_year = g.groupby('year')[sim_col]
            med = by_year.median() * scale
            p05 = by_year.quantile(0.05) * scale
            p95 = by_year.quantile(0.95) * scale
            ax.fill_between(p05.index, p05, p95, alpha=0.15, color=PALETTE[dur])
            ax.plot(med.index, med, color=PALETTE[dur], lw=1.8,
                    label=f'dur_on_art = {dur} yr')
        if targ_col and targ_col in targets.columns:
            t = targets.dropna(subset=[targ_col])
            ax.scatter(t.time, t[targ_col] * scale, s=22, color='#c44e52',
                       zorder=5, label='UNAIDS')
        ax.set_title(title, fontsize=12)
        if unit:
            ax.set_ylabel(unit, fontsize=10)
        ax.set_xlim(1990, 2040)
        ax.grid(alpha=0.3)
    axes[0, 0].legend(loc='upper left', fontsize=9)
    fig.tight_layout()
    out = FIG_DIR / 'dur_on_art_scan.png'
    fig.savefig(out, dpi=130, bbox_inches='tight')
    print(f'wrote {out}')


def main():
    args = [(dur, seed) for dur in DUR_ON_ART_VALUES for seed in range(1, N_SEEDS + 1)]
    print(f'Launching {len(args)} sims across {N_WORKERS} workers...')
    with mp.Pool(N_WORKERS) as pool:
        results = pool.map(worker, args)
    results = [r for r in results if r is not None]
    ts = pd.concat(results, ignore_index=True)
    ts.to_parquet(OUT_DIR / 'scan.parquet')
    print(f'wrote {OUT_DIR / "scan.parquet"} ({len(ts)} rows, '
          f'{ts.dur_on_art.nunique()} dur values, {ts.seed.nunique()} seeds)')
    targets = pd.read_csv(REPO / 'data' / 'zimbabwe_hiv_calib.csv')
    plot(ts, targets)


if __name__ == '__main__':
    main()
