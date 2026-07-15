"""
Exp 09 extended LHS + GoF ranking.

500 LHS draws x 1 seed x 10k agents on the exp_08 8-prior setup +
stisim feat/hiv-death-rate-pars. Extends RESULT_COLS to capture the
cascade analyzer outputs, SW-stratified new infections, and age-band
prevalence needed by the paper's Fig 1 and validation replicas.
Ranks draws by weighted GoF and writes draws_top50.csv.
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

N_DRAWS = int(os.environ.get('N_DRAWS', 500))
N_WORKERS = int(os.environ.get('N_WORKERS', 30))
N_AGENTS = int(os.environ.get('N_AGENTS', 10_000))
LHS_SEED = 46
TOP_N = 50

OUT_DIR = HERE / 'outputs'
FIG_DIR = HERE / 'figures'
OUT_DIR.mkdir(exist_ok=True)
FIG_DIR.mkdir(exist_ok=True)

RESULT_COLS_SIM = ['n_alive']

RESULT_COLS_HIV = [
    'prevalence_15_49', 'prevalence_f', 'prevalence_m',
    'n_infected', 'p_on_art', 'n_on_art', 'n_diagnosed',
    'new_infections', 'new_deaths',
    'new_infections_sw', 'new_infections_client',
    'new_infections_not_sw', 'new_infections_not_client',
    # Age-band prevalence (both sexes)
    'prevalence_15_20', 'prevalence_20_25', 'prevalence_25_30',
    'prevalence_30_35', 'prevalence_35_50', 'prevalence_50_65',
    # Age-band prevalence by sex
    'prevalence_f_15_20', 'prevalence_f_20_25', 'prevalence_f_25_30',
    'prevalence_f_30_35', 'prevalence_f_35_50', 'prevalence_f_50_65',
    'prevalence_m_15_20', 'prevalence_m_20_25', 'prevalence_m_25_30',
    'prevalence_m_30_35', 'prevalence_m_35_50', 'prevalence_m_50_65',
]

RESULT_COLS_CASCADE = [
    'prop_diagnosed', 'prop_diag_on_art', 'prop_art_effective',
    'n_alive_15_64', 'n_infected_15_64', 'new_infections_15_64',
    'age_sum_new_inf_f', 'age_sum_new_inf_m',
    'n_new_inf_f', 'n_new_inf_m',
    'new_trans_undiagnosed', 'new_trans_diag_not_on_art',
    'new_trans_on_art', 'new_trans_post_art',
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
    for col in RESULT_COLS_SIM:
        out[col] = ann[col]
    for col in RESULT_COLS_HIV:
        out[f'hiv.{col}'] = ann.hiv[col]
    for col in RESULT_COLS_CASCADE:
        out[f'casc.{col}'] = ann.hivcascadeanalyzer[col]
    return pd.DataFrame(out)


CROSS_RISK = ['(0,1)', '(0,2)', '(1,0)', '(1,2)', '(2,0)', '(2,1)']


def aggressive_condom_df():
    """Locked condom schedule from exp_06 (aggressive scenario)."""
    d = pd.read_csv(REPO / 'data' / 'condom_use.csv')
    bumps = {'2010': 0.90, '2015': 0.95, '2020': 0.95}
    for pship in CROSS_RISK:
        row_idx = d.index[d.partnership == pship]
        for col, val in bumps.items():
            d.loc[row_idx, col] = val
    return d


def worker(args):
    draw_idx, draw_row = args
    calib_row = {k: v for k, v in draw_row.items() if k != 'draw_idx'}
    try:
        sim = make_sim(seed=int(draw_idx)+1, n_agents=N_AGENTS,
                       start=1985, stop=2040, calib_pars=calib_row, verbose=0,
                       condom_data=aggressive_condom_df())
        sim.run()
        return extract_ts(sim, draw_idx)
    except Exception as e:
        print(f'[draw {draw_idx}] failed: {e}', flush=True)
        return None


def load_targets():
    d = pd.read_csv(REPO / 'data' / 'zimbabwe_hiv_calib.csv')
    art_n = pd.read_csv(REPO / 'data' / 'n_art.csv').rename(columns={'year': 'time'})
    art_p = pd.read_csv(REPO / 'data' / 'p_art.csv').rename(columns={'year': 'time', 'p_art': 'unaids_art_coverage'})
    return d.merge(art_n[['time', 'n_art']], on='time', how='left').merge(art_p, on='time', how='left')


GOF_METRICS = [
    'hiv.prevalence_15_49', 'hiv.prevalence_f', 'hiv.prevalence_m',
    'hiv.n_infected', 'hiv.new_infections', 'hiv.new_deaths',
]
GOF_YEARS = [1990, 1995, 2000, 2005, 2010, 2015, 2020]

# Mean age at ADULT HIV acquisition (>= 15) targets, from Paper B four-model
# consensus for Zimbabwe (Bansi-Matharu 2025 Fig 2B).
AGE_ACQ_TARGETS = {
    (2015, 'f'): 30.0,
    (2020, 'f'): 32.0,
    (2015, 'm'): 34.0,
    (2020, 'm'): 36.0,
}


def compute_gof(ens, targets):
    """Per-draw weighted RMSE of relative error vs UNAIDS + mean-age-at-
    acquisition anchors.

    Each term contributes a squared relative-error (sim - targ) / targ.
    Terms are averaged across (metric, year) pairs so total counts are
    comparable across draws.
    """
    rows = []
    for draw_idx, grp in ens.groupby('draw_idx'):
        by_year = grp.set_index('year')
        sq = []
        for m in GOF_METRICS:
            for y in GOF_YEARS:
                if y not in by_year.index:
                    continue
                t = targets[targets.time == y]
                if t.empty:
                    continue
                targ_val = t[m].values[0] if m in t.columns else np.nan
                if pd.isna(targ_val) or targ_val <= 0:
                    continue
                sim_val = by_year.loc[y, m]
                sq.append(((sim_val - targ_val) / targ_val) ** 2)
        # Adult mean age at acquisition (F + M) at 2015 and 2020.
        for (yr, sex), tgt in AGE_ACQ_TARGETS.items():
            if yr not in by_year.index:
                continue
            age_sum = by_year.loc[yr, f'casc.age_sum_new_inf_{sex}']
            n_new = by_year.loc[yr, f'casc.n_new_inf_{sex}']
            if n_new <= 0:
                continue
            sim_val = age_sum / n_new
            sq.append(((sim_val - tgt) / tgt) ** 2)
        rmse = float(np.sqrt(np.mean(sq))) if sq else np.nan
        rows.append({'draw_idx': int(draw_idx), 'gof_rmse': rmse, 'n_terms': len(sq)})
    return pd.DataFrame(rows).sort_values('gof_rmse')


def plot_coverage(ens, targets, out_path, title_suffix=''):
    panels = [
        ('hiv.prevalence_15_49', 'HIV prevalence, 15-49', 1.0,   '',           'hiv.prevalence_15_49'),
        ('hiv.prevalence_f',     'HIV prevalence, female', 1.0,  '',           'hiv.prevalence_f'),
        ('hiv.prevalence_m',     'HIV prevalence, male', 1.0,    '',           'hiv.prevalence_m'),
        ('n_alive',              'Total population', 1e-6,       'millions',   'n_alive'),
        ('hiv.n_infected',       'PLHIV', 1e-6,                  'millions',   'hiv.n_infected'),
        ('hiv.p_on_art',         'ART coverage (of PLHIV)', 1.0, '',           'unaids_art_coverage'),
        ('hiv.new_infections',   'New HIV infections/yr', 1e-3,  'thousands',  'hiv.new_infections'),
        ('hiv.new_deaths',       'AIDS-related deaths/yr', 1e-3, 'thousands',  'hiv.new_deaths'),
        ('hiv.n_on_art',         'Number on ART', 1e-6,          'millions',   'n_art'),
    ]
    fig, axes = plt.subplots(3, 3, figsize=(14, 9), sharex=True)
    for ax, (sim_col, title, scale, unit, targ_col) in zip(axes.flat, panels):
        by_year = ens.groupby('year')[sim_col]
        p05 = by_year.quantile(0.05) * scale
        p95 = by_year.quantile(0.95) * scale
        med = by_year.median() * scale
        ax.fill_between(p05.index, p05, p95, alpha=0.22, color='#2b5f8a',
                        label='Ensemble 5-95%')
        ax.plot(med.index, med, color='#2b5f8a', lw=1.6, label='Median')
        for _, g in ens.groupby('draw_idx'):
            ax.plot(g.year, g[sim_col] * scale, color='#2b5f8a', lw=0.4, alpha=0.10)
        if targ_col in targets.columns:
            t = targets.dropna(subset=[targ_col])
            ax.scatter(t.time, t[targ_col] * scale, s=22, color='#c44e52',
                       zorder=5, label='UNAIDS')
        ax.set_title(title + title_suffix, fontsize=12)
        if unit:
            ax.set_ylabel(unit, fontsize=10)
        ax.set_xlim(1990, 2040)
        ax.grid(alpha=0.3)
    axes[0, 0].legend(loc='upper left', fontsize=8)
    fig.tight_layout()
    fig.savefig(out_path, dpi=130, bbox_inches='tight')
    print(f'wrote {out_path}')


def main():
    draws = lhs_draws(N_DRAWS)
    draws.to_csv(OUT_DIR / 'lhs_draws.csv', index=False)
    print(f'Drew {len(draws)} LHS samples; running with {N_WORKERS} workers...')

    args = [(row.draw_idx, row.to_dict()) for _, row in draws.iterrows()]
    with mp.Pool(N_WORKERS) as pool:
        results = pool.map(worker, args)

    results = [r for r in results if r is not None]
    ens = pd.concat(results, ignore_index=True)
    ens.to_parquet(OUT_DIR / 'lhs_coverage.parquet')
    print(f'wrote {OUT_DIR / "lhs_coverage.parquet"} '
          f'({len(ens)} rows, {ens.draw_idx.nunique()} draws)')

    targets = load_targets()
    gof = compute_gof(ens, targets)
    gof.to_csv(OUT_DIR / 'lhs_gof.csv', index=False)
    top = gof.head(TOP_N).merge(draws, on='draw_idx')
    top.to_csv(OUT_DIR / f'draws_top{TOP_N}.csv', index=False)
    print(f'wrote {OUT_DIR / f"draws_top{TOP_N}.csv"} '
          f'(best draw RMSE {gof.gof_rmse.min():.3f}, '
          f'worst-of-top RMSE {top.gof_rmse.max():.3f})')

    plot_coverage(ens, targets, FIG_DIR / 'coverage_check.png',
                  title_suffix=f' — all {ens.draw_idx.nunique()} draws')
    ens_top = ens[ens.draw_idx.isin(top.draw_idx)]
    plot_coverage(ens_top, targets, FIG_DIR / 'coverage_top50.png',
                  title_suffix=f' — top {TOP_N} draws')


if __name__ == '__main__':
    main()
