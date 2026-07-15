"""
Exp 06 — condom-use scale-up scenarios.

Three scenarios (current / modest / aggressive) x 30-draw paired LHS
(same seed across scenarios so per-draw comparisons are clean).
"""
from __future__ import annotations

import multiprocessing as mp
import os
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import qmc

os.environ.update(OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1',
                  NUMEXPR_NUM_THREADS='1', MKL_NUM_THREADS='1')

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
sys.path.insert(0, str(REPO))

from priors import calib_pars as PRIORS  # noqa: E402
from model import make_sim  # noqa: E402
from utils import set_font  # noqa: E402

set_font(size=12)

N_DRAWS = int(os.environ.get('N_DRAWS', 30))
N_WORKERS = int(os.environ.get('N_WORKERS', 30))
N_AGENTS = int(os.environ.get('N_AGENTS', 10_000))
LHS_SEED = 45

OUT_DIR = HERE / 'outputs'
FIG_DIR = HERE / 'figures'
OUT_DIR.mkdir(exist_ok=True)
FIG_DIR.mkdir(exist_ok=True)

RESULT_COLS = [
    'hiv.prevalence_15_49', 'hiv.prevalence_f', 'hiv.prevalence_m',
    'n_alive', 'hiv.n_infected', 'hiv.p_on_art',
    'hiv.new_infections', 'hiv.new_deaths', 'hiv.n_on_art',
]

# Cross-risk partnerships whose condom use gets bumped in the scale-up scenarios
CROSS_RISK = ['(0,1)', '(0,2)', '(1,0)', '(1,2)', '(2,0)', '(2,1)']


def build_condom_df(scenario):
    """Return a condom_use DataFrame for the named scenario."""
    d = pd.read_csv(REPO / 'data' / 'condom_use.csv')
    if scenario == 'current':
        return d
    bumps = {
        'modest':     {'2010': 0.80, '2015': 0.85, '2020': 0.90},
        'aggressive': {'2010': 0.90, '2015': 0.95, '2020': 0.95},
    }[scenario]
    for pship in CROSS_RISK:
        row_idx = d.index[d.partnership == pship]
        for col, val in bumps.items():
            d.loc[row_idx, col] = val
    return d


def lhs_draws(n):
    par_names = list(PRIORS.keys())
    d_ = len(par_names)
    U = qmc.LatinHypercube(d=d_, seed=LHS_SEED).random(n)
    rows = []
    for i, u in enumerate(U):
        row = {'draw_idx': i}
        for j, name in enumerate(par_names):
            _, lo, hi, log = PRIORS[name]
            val = np.exp(np.log(lo) + u[j]*(np.log(hi)-np.log(lo))) if log else lo + u[j]*(hi-lo)
            row[name] = val
        rows.append(row)
    return pd.DataFrame(rows)


def extract_ts(sim, draw_idx, scenario):
    ann = sim.results.annualize()
    years = ann.n_alive.timevec.years.astype(int)
    out = {'year': years, 'draw_idx': draw_idx, 'scenario': scenario}
    for col in RESULT_COLS:
        if '.' in col:
            mod, name = col.split('.', 1)
            out[col] = ann[mod][name]
        else:
            out[col] = ann[col]
    return pd.DataFrame(out)


def worker(args):
    scenario, draw_idx, draw_row = args
    calib_row = {k: v for k, v in draw_row.items() if k != 'draw_idx'}
    condom_df = build_condom_df(scenario)
    try:
        sim = make_sim(seed=int(draw_idx)+1, n_agents=N_AGENTS,
                       start=1985, stop=2040, calib_pars=calib_row,
                       verbose=0, condom_data=condom_df)
        sim.run()
        return extract_ts(sim, draw_idx, scenario)
    except Exception as e:
        print(f'[{scenario} draw {draw_idx}] failed: {e}', flush=True)
        return None


def load_targets():
    d = pd.read_csv(REPO / 'data' / 'zimbabwe_hiv_calib.csv')
    art_n = pd.read_csv(REPO / 'data' / 'n_art.csv').rename(columns={'year': 'time'})
    art_p = pd.read_csv(REPO / 'data' / 'p_art.csv').rename(columns={'year': 'time', 'p_art': 'unaids_art_coverage'})
    return d.merge(art_n[['time', 'n_art']], on='time', how='left').merge(art_p, on='time', how='left')


PALETTE = {'current': '#8b6ba1', 'modest': '#2b8ea1', 'aggressive': '#e2b64e'}


def plot(ens, targets):
    panels = [
        ('hiv.prevalence_15_49',  'HIV prevalence, 15-49', 1.0,   '',           'hiv.prevalence_15_49'),
        ('hiv.prevalence_f',      'HIV prevalence, female', 1.0,  '',           'hiv.prevalence_f'),
        ('hiv.prevalence_m',      'HIV prevalence, male', 1.0,    '',           'hiv.prevalence_m'),
        ('n_alive',               'Total population', 1e-6,       'millions',   'n_alive'),
        ('hiv.n_infected',        'PLHIV', 1e-6,                  'millions',   'hiv.n_infected'),
        ('hiv.p_on_art',          'ART coverage (of PLHIV)', 1.0, '',           'unaids_art_coverage'),
        ('hiv.new_infections',    'New HIV infections/yr', 1e-3,  'thousands',  'hiv.new_infections'),
        ('hiv.new_deaths',        'AIDS-related deaths/yr', 1e-3, 'thousands',  'hiv.new_deaths'),
        ('hiv.n_on_art',          'Number on ART', 1e-6,          'millions',   'n_art'),
    ]
    fig, axes = plt.subplots(3, 3, figsize=(14, 9), sharex=True)
    for ax, (sim_col, title, scale, unit, targ_col) in zip(axes.flat, panels):
        for scenario in ['current', 'modest', 'aggressive']:
            g = ens[ens.scenario == scenario]
            by_year = g.groupby('year')[sim_col]
            med = by_year.median() * scale
            p05 = by_year.quantile(0.05) * scale
            p95 = by_year.quantile(0.95) * scale
            ax.fill_between(p05.index, p05, p95, alpha=0.10, color=PALETTE[scenario])
            ax.plot(med.index, med, color=PALETTE[scenario], lw=1.8, label=scenario)
        if targ_col in targets.columns:
            t = targets.dropna(subset=[targ_col])
            ax.scatter(t.time, t[targ_col] * scale, s=22, color='#c44e52',
                       zorder=5, label='UNAIDS')
        ax.set_title(title, fontsize=12)
        if unit:
            ax.set_ylabel(unit, fontsize=10)
        ax.set_xlim(1990, 2040)
        ax.grid(alpha=0.3)
    axes[0, 0].legend(loc='upper left', fontsize=8)
    fig.tight_layout()
    out = FIG_DIR / 'condom_scale_up.png'
    fig.savefig(out, dpi=130, bbox_inches='tight')
    print(f'wrote {out}')


def main():
    draws = lhs_draws(N_DRAWS)
    draws.to_csv(OUT_DIR / 'draws.csv', index=False)
    args = []
    for scenario in ['current', 'modest', 'aggressive']:
        for _, row in draws.iterrows():
            args.append((scenario, row.draw_idx, row.to_dict()))
    print(f'Launching {len(args)} sims across {N_WORKERS} workers '
          f'(3 scenarios x {N_DRAWS} draws)...')
    with mp.Pool(N_WORKERS) as pool:
        results = pool.map(worker, args)
    results = [r for r in results if r is not None]
    ens = pd.concat(results, ignore_index=True)
    ens.to_parquet(OUT_DIR / 'condom_scale_up.parquet')
    print(f'wrote {OUT_DIR / "condom_scale_up.parquet"} ({len(ens)} rows, '
          f'{ens.scenario.nunique()} scenarios, {ens.draw_idx.nunique()} draws)')
    plot(ens, load_targets())


if __name__ == '__main__':
    main()
