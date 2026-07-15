"""
Exp 04 coverage check — rel_migration=0.5 locked in model.py, 6 remaining
priors LHS-sampled. 3x3 diagnostic figure with ART scale-up as the
new panel (alongside PLHIV, new infections, deaths).
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

N_DRAWS = int(os.environ.get('N_DRAWS', 50))
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


def lhs_draws(n):
    par_names = list(PRIORS.keys())
    d = len(par_names)
    U = qmc.LatinHypercube(d=d, seed=LHS_SEED).random(n)
    rows = []
    for i, u in enumerate(U):
        row = {'draw_idx': i}
        for j, name in enumerate(par_names):
            _, lo, hi, log = PRIORS[name]
            val = np.exp(np.log(lo) + u[j]*(np.log(hi)-np.log(lo))) if log else lo + u[j]*(hi-lo)
            row[name] = val
        rows.append(row)
    return pd.DataFrame(rows)


def extract_ts(sim, draw_idx):
    ann = sim.results.annualize()
    years = ann.n_alive.timevec.years.astype(int)
    out = {'year': years, 'draw_idx': draw_idx}
    for col in RESULT_COLS:
        if '.' in col:
            mod, name = col.split('.', 1)
            out[col] = ann[mod][name]
        else:
            out[col] = ann[col]
    return pd.DataFrame(out)


def worker(args):
    draw_idx, draw_row = args
    calib_row = {k: v for k, v in draw_row.items() if k != 'draw_idx'}
    try:
        sim = make_sim(seed=int(draw_idx)+1, n_agents=N_AGENTS,
                       start=1985, stop=2040, calib_pars=calib_row, verbose=0)
        sim.run()
        return extract_ts(sim, draw_idx)
    except Exception as e:
        print(f'[draw {draw_idx}] failed: {e}', flush=True)
        return None


def load_targets():
    """Assemble targets. ART input is now data/p_art.csv (coverage).
    UNAIDS n_art comes from n_art.csv for the Number-on-ART panel;
    UNAIDS ART coverage is now the input p_art series itself."""
    d = pd.read_csv(REPO / 'data' / 'zimbabwe_hiv_calib.csv')
    art_n = pd.read_csv(REPO / 'data' / 'n_art.csv').rename(columns={'year': 'time'})
    art_p = pd.read_csv(REPO / 'data' / 'p_art.csv').rename(columns={'year': 'time', 'p_art': 'unaids_art_coverage'})
    d = d.merge(art_n[['time', 'n_art']], on='time', how='left')
    d = d.merge(art_p, on='time', how='left')
    return d


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
        by_year = ens.groupby('year')[sim_col]
        p05 = by_year.quantile(0.05) * scale
        p95 = by_year.quantile(0.95) * scale
        med = by_year.median() * scale
        ax.fill_between(p05.index, p05, p95, alpha=0.22, color='#2b5f8a',
                        label='Prior ensemble 5-95%')
        ax.plot(med.index, med, color='#2b5f8a', lw=1.6, label='Prior median')
        # per-draw spaghetti
        for _, g in ens.groupby('draw_idx'):
            ax.plot(g.year, g[sim_col] * scale, color='#2b5f8a', lw=0.4, alpha=0.12)
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
    out = FIG_DIR / 'coverage_check.png'
    fig.savefig(out, dpi=130, bbox_inches='tight')
    print(f'wrote {out}')


def main():
    draws = lhs_draws(N_DRAWS)
    draws.to_csv(OUT_DIR / 'coverage_draws.csv', index=False)
    print(f'Drew {len(draws)} LHS samples; running with {N_WORKERS} workers...')

    args = [(row.draw_idx, row.to_dict()) for _, row in draws.iterrows()]
    with mp.Pool(N_WORKERS) as pool:
        results = pool.map(worker, args)

    results = [r for r in results if r is not None]
    ens = pd.concat(results, ignore_index=True)
    ens.to_parquet(OUT_DIR / 'coverage_check.parquet')
    print(f'wrote {OUT_DIR / "coverage_check.parquet"} ({len(ens)} rows, '
          f'{ens.draw_idx.nunique()} draws)')

    targets = load_targets()
    plot(ens, targets)


if __name__ == '__main__':
    main()
