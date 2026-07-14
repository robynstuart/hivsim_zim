"""
Exp 03 — Point-value scan of `migration.rel_migration`.

6 non-migration priors fixed at their prior midpoints; sweep
`rel_migration ∈ {0.5, 1.0, 1.5}` with K = 5 seeds per value.

Saves per-sim time series to `outputs/scan.parquet` and a 3-panel
figure comparing n_alive under each rel_migration setting against
UNAIDS.

Env vars:
    N_SEEDS   default 5
    N_WORKERS default 15  (3 rel_mig values * 5 seeds = 15 sims)
    N_AGENTS  default 10000
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

N_SEEDS = int(os.environ.get('N_SEEDS', 5))
N_WORKERS = int(os.environ.get('N_WORKERS', 15))
N_AGENTS = int(os.environ.get('N_AGENTS', 10_000))

OUT_DIR = HERE / 'outputs'
FIG_DIR = HERE / 'figures'
OUT_DIR.mkdir(exist_ok=True)
FIG_DIR.mkdir(exist_ok=True)

FIXED_PARS = {
    'hiv.beta_m2f':              0.0225,
    'hiv.rel_init_prev':         0.9,
    'hiv.dur_on_art':            6.0,
    'structuredsexual.prop_f0':  0.725,
    'structuredsexual.m2_conc':  5.0,
    'structuredsexual.dur_sw':   8.5,
}

REL_MIG_VALUES = [0.5, 1.0, 1.5]

RESULT_COLS = ['hiv.prevalence', 'hiv.n_infected', 'hiv.prevalence_15_49',
               'hiv.new_infections', 'hiv.new_deaths', 'n_alive']


def extract_ts(sim, rel_mig, seed):
    ann = sim.results.annualize()
    years = ann.n_alive.timevec.years.astype(int)
    out = {'year': years, 'rel_migration': rel_mig, 'seed': seed}
    for col in RESULT_COLS:
        if '.' in col:
            mod, name = col.split('.', 1)
            out[col] = ann[mod][name]
        else:
            out[col] = ann[col]
    return pd.DataFrame(out)


def worker(args):
    rel_mig, seed = args
    calib_pars = {**FIXED_PARS, 'migration.rel_migration': rel_mig}
    try:
        sim = make_sim(seed=seed, n_agents=N_AGENTS,
                       start=1985, stop=2040, calib_pars=calib_pars, verbose=0)
        sim.run()
        return extract_ts(sim, rel_mig, seed)
    except Exception as e:
        print(f'[rel_mig={rel_mig} seed={seed}] failed: {e}', flush=True)
        return None


def plot(ts, targets):
    metrics = [
        ('n_alive',             'Total population',       1e-6, 'millions'),
        ('hiv.n_infected',      'PLHIV',                  1e-6, 'millions'),
        ('hiv.prevalence_15_49', 'HIV prev 15-49',        1.0,  ''),
    ]
    fig, axes = plt.subplots(1, 3, figsize=(14, 4), sharex=True)
    palette = {0.5: '#2b8ea1', 1.0: '#8b6ba1', 1.5: '#e2b64e'}
    for ax, (col, title, scale, unit) in zip(axes, metrics):
        for rel_mig in REL_MIG_VALUES:
            g = ts[ts.rel_migration == rel_mig]
            by_year = g.groupby('year')[col]
            med = by_year.median() * scale
            p05 = by_year.quantile(0.05) * scale
            p95 = by_year.quantile(0.95) * scale
            ax.fill_between(p05.index, p05, p95, alpha=0.15, color=palette[rel_mig])
            ax.plot(med.index, med, color=palette[rel_mig], lw=1.8,
                    label=f'rel_migration = {rel_mig}')
        if col in targets.columns:
            t = targets.dropna(subset=[col])
            ax.scatter(t.time, t[col] * scale, s=25, color='#c44e52', zorder=5,
                       label='UNAIDS')
        ax.set_title(title, fontsize=12)
        if unit:
            ax.set_ylabel(unit, fontsize=11)
        ax.set_xlim(1990, 2040)
        ax.grid(alpha=0.3)
    axes[0].legend(loc='upper left', fontsize=9)
    fig.tight_layout()
    out = FIG_DIR / 'rel_migration_scan.png'
    fig.savefig(out, dpi=130, bbox_inches='tight')
    print(f'wrote {out}')


def main():
    args = [(rel_mig, seed) for rel_mig in REL_MIG_VALUES for seed in range(1, N_SEEDS + 1)]
    print(f'Launching {len(args)} sims across {N_WORKERS} workers…')
    with mp.Pool(N_WORKERS) as pool:
        results = pool.map(worker, args)
    results = [r for r in results if r is not None]
    ts = pd.concat(results, ignore_index=True)
    ts.to_parquet(OUT_DIR / 'scan.parquet')
    print(f'wrote {OUT_DIR / "scan.parquet"} ({len(ts)} rows, '
          f'{ts.rel_migration.nunique()} rel_mig values, {ts.seed.nunique()} seeds)')
    targets = pd.read_csv(REPO / 'data' / 'zimbabwe_hiv_calib.csv')
    plot(ts, targets)


if __name__ == '__main__':
    main()
