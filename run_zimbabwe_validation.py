"""
Zimbabwe validation runner.

Loads the calibrated draws (`calibration/artifacts/draws_top10.csv`),
runs each draw across K stochastic seeds under the status-quo scenario
1985-2040, and writes a long-format annual time-series parquet to
`outputs/zimbabwe_validation.parquet`.

Indicators extracted (Paper A: Taramusi et al. 2025, five-model
Zimbabwe projections):
  - HIV prevalence, 15-49 (percent)
  - HIV incidence, 15-49 (per 1000 person-years)
  - New infections per year (whole-pop count)
  - PLHIV (whole-pop count)
  - Number on ART (whole-pop)
  - AIDS-related deaths per year (whole-pop count)

Run:
    python run_zimbabwe_validation.py                        # default: 10 draws x 3 seeds
    N_DRAWS=5 K_SEEDS=2 python run_zimbabwe_validation.py    # override
    python run_zimbabwe_validation.py --serial               # disable multiprocessing
"""

import argparse
import os
import time as pytime
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

from model import make_sim


REPO = Path(__file__).resolve().parent
DRAWS_CSV = Path(os.environ.get(
    'DRAWS_CSV',
    REPO / 'calibration' / 'artifacts' / 'draws_sustaining_top30.csv'))
OUT_DIR = REPO / 'outputs'
OUT_PATH = OUT_DIR / 'zimbabwe_validation.parquet'

N_AGENTS = int(os.environ.get('N_AGENTS', 10_000))
START = 1985
STOP = 2041  # inclusive of 2040 output


# Age bands that approximate 15-49 (35-50 covers 35..49 inclusive under
# starsim's [X, Y) convention).
AGE_BANDS_15_49 = ['15_20', '20_25', '25_30', '30_35', '35_50']


def load_calib_pars(draws_row):
    """Extract the HIV-relevant parameter values from one draws row.

    The draws CSV came from a joint HIV + STI calibration. For the HIV-only
    model here, only the HIV + network columns are meaningful. Log-scale
    columns are prefixed `log_`.
    """
    return {
        'hiv.beta_m2f':             float(draws_row['hiv.beta_m2f']),
        'hiv.rel_init_prev':        float(draws_row['hiv.rel_init_prev']),
        'structuredsexual.prop_f0': float(draws_row['structuredsexual.prop_f0']),
        'structuredsexual.m2_conc': float(draws_row['structuredsexual.m2_conc']),
        'structuredsexual.dur_sw':  float(draws_row['structuredsexual.dur_sw']),
    }


def run_one(task):
    """Run one (draw, seed) sim and return an annual dataframe.

    `task` is a tuple (draw_idx, sub_idx, calib_pars). The seed convention
    matches the sti_notification scenarios runner: `seed = draw_idx*1000 + sub_idx`.
    """
    draw_idx, sub_idx, calib_pars = task
    seed = int(draw_idx) * 1000 + int(sub_idx)

    sim = make_sim(seed=seed, start=START, stop=STOP,
                   n_agents=N_AGENTS, calib_pars=calib_pars, verbose=0)
    sim.run()

    res = sim.results
    hiv = res.hiv
    tvec = np.asarray(hiv.timevec).astype(float)
    year = np.floor(tvec).astype(int)

    # 15-49 prevalence: direct
    prev_15_49 = np.asarray(hiv.prevalence_15_49) * 100.0  # percent

    # 15-49 new infections: sum across age bands
    new_inf_15_49 = np.zeros_like(tvec)
    n_inf_15_49 = np.zeros_like(tvec)
    for band in AGE_BANDS_15_49:
        new_inf_15_49 += np.asarray(hiv[f'new_infections_{band}'])
        n_inf_15_49 += np.asarray(hiv[f'n_infected_{band}'])

    # Derive n_alive_15_49 from prev_15_49 = n_infected_15_49 / n_alive_15_49.
    # Then susceptible = alive - infected; incidence per 1000 py.
    # Guard: when prev is 0 at very early years, alive is undefined; use nan.
    with np.errstate(divide='ignore', invalid='ignore'):
        n_alive_15_49 = np.where(prev_15_49 > 0,
                                 n_inf_15_49 / (prev_15_49 / 100.0),
                                 np.nan)
        n_susc_15_49 = n_alive_15_49 - n_inf_15_49
        # sim runs monthly; new_inf per step is per-month. Sum to annual below.
        # Instantaneous incidence rate (per 1000 py) at monthly res =
        # 12 * new_inf / susceptible * 1000.
        inc_15_49_permo = np.where(n_susc_15_49 > 0,
                                   12.0 * new_inf_15_49 / n_susc_15_49 * 1000.0,
                                   np.nan)

    # Whole-pop indicators
    new_inf_all = np.asarray(hiv.new_infections)
    plhiv = np.asarray(hiv.n_infected)
    n_on_art = np.asarray(hiv.n_on_art)
    new_deaths = np.asarray(hiv.new_deaths)  # AIDS-related deaths
    n_diagnosed = np.asarray(hiv.n_diagnosed)

    # Paper B: cascade + transmission-by-stage from HIVCascadeAnalyzer
    casc = res.hivcascadeanalyzer

    df = pd.DataFrame({
        'year': year,
        'draw_idx': int(draw_idx),
        'sub_idx': int(sub_idx),
        'seed': seed,
        # Paper A indicators
        'prev_15_49_pct': prev_15_49,
        'inc_15_49_per1000py': inc_15_49_permo,
        'new_infections_per_month': new_inf_all,
        'plhiv': plhiv,
        'n_on_art': n_on_art,
        'aids_deaths_per_month': new_deaths,
        # Ancillary (used for Paper B cascade denominators + validation)
        'n_diagnosed': n_diagnosed,
        'n_infected_15_49': n_inf_15_49,
        'n_alive_15_49': n_alive_15_49,
        # Paper B: cascade proportions
        'prop_diagnosed':     np.asarray(casc.prop_diagnosed),
        'prop_diag_on_art':   np.asarray(casc.prop_diag_on_art),
        'prop_art_effective': np.asarray(casc.prop_art_effective),
        # Paper B: transmission-by-stage (per timestep counts)
        'trans_undiagnosed_per_month':     np.asarray(casc.new_trans_undiagnosed),
        'trans_diag_not_on_art_per_month': np.asarray(casc.new_trans_diag_not_on_art),
        'trans_on_art_per_month':          np.asarray(casc.new_trans_on_art),
        'trans_post_art_per_month':        np.asarray(casc.new_trans_post_art),
        # Paper B Fig 1B: 15-64 population + prevalence (matches paper age band)
        'n_alive_15_64':      np.asarray(casc.n_alive_15_64),
        'n_infected_15_64':   np.asarray(casc.n_infected_15_64),
        'new_infections_15_64_per_month': np.asarray(casc.new_infections_15_64),
        # Paper B Fig 2B: sum-of-ages + count of new infections, by sex
        'age_sum_new_inf_f_per_month': np.asarray(casc.age_sum_new_inf_f),
        'age_sum_new_inf_m_per_month': np.asarray(casc.age_sum_new_inf_m),
        'n_new_inf_f_per_month':       np.asarray(casc.n_new_inf_f),
        'n_new_inf_m_per_month':       np.asarray(casc.n_new_inf_m),
    })

    # Aggregate monthly -> annual. For rates (prev, inc) take the mean over
    # the 12 months of each calendar year; for counts (new_infections, new_deaths)
    # sum the 12 months. PLHIV / n_on_art / n_diagnosed are stock variables so
    # take end-of-year value.
    agg = {
        'prev_15_49_pct':          'mean',
        'inc_15_49_per1000py':     'mean',
        'new_infections_per_month': 'sum',
        'aids_deaths_per_month':    'sum',
        'plhiv':                    'last',
        'n_on_art':                 'last',
        'n_diagnosed':              'last',
        'n_infected_15_49':         'last',
        'n_alive_15_49':            'last',
        # Cascade proportions: end-of-year snapshot
        'prop_diagnosed':          'last',
        'prop_diag_on_art':        'last',
        'prop_art_effective':      'last',
        # Transmission-by-stage: sum monthly counts to annual
        'trans_undiagnosed_per_month':     'sum',
        'trans_diag_not_on_art_per_month': 'sum',
        'trans_on_art_per_month':          'sum',
        'trans_post_art_per_month':        'sum',
        # 15-64 aggregates: pop + infected = end-of-year snapshot; new infs sum
        'n_alive_15_64':                   'last',
        'n_infected_15_64':                'last',
        'new_infections_15_64_per_month':  'sum',
        # Mean age at acquisition: sum ages + counts, divide post-agg
        'age_sum_new_inf_f_per_month':     'sum',
        'age_sum_new_inf_m_per_month':     'sum',
        'n_new_inf_f_per_month':           'sum',
        'n_new_inf_m_per_month':           'sum',
    }
    annual = df.groupby(['year', 'draw_idx', 'sub_idx', 'seed'], as_index=False).agg(agg)
    annual = annual.rename(columns={
        'new_infections_per_month': 'new_infections_per_year',
        'aids_deaths_per_month':    'aids_deaths_per_year',
        'trans_undiagnosed_per_month':     'trans_undiagnosed_per_year',
        'trans_diag_not_on_art_per_month': 'trans_diag_not_on_art_per_year',
        'trans_on_art_per_month':          'trans_on_art_per_year',
        'trans_post_art_per_month':        'trans_post_art_per_year',
        'new_infections_15_64_per_month':  'new_infections_15_64_per_year',
        'age_sum_new_inf_f_per_month':     'age_sum_new_inf_f_per_year',
        'age_sum_new_inf_m_per_month':     'age_sum_new_inf_m_per_year',
        'n_new_inf_f_per_month':           'n_new_inf_f_per_year',
        'n_new_inf_m_per_month':           'n_new_inf_m_per_year',
    })
    return annual


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--serial', action='store_true', help='Disable multiprocessing')
    ap.add_argument('--n-workers', type=int, default=int(os.environ.get('N_WORKERS', 60)))
    args = ap.parse_args()

    n_draws = int(os.environ.get('N_DRAWS', 10))
    k_seeds = int(os.environ.get('K_SEEDS', 3))

    draws = pd.read_csv(DRAWS_CSV).head(n_draws)
    tasks = []
    for _, row in draws.iterrows():
        cp = load_calib_pars(row)
        for sub_idx in range(k_seeds):
            tasks.append((int(row['draw_idx']), sub_idx, cp))

    OUT_DIR.mkdir(exist_ok=True)
    print(f'[run] {len(tasks)} sims '
          f'({n_draws} draws x {k_seeds} seeds) | n_agents={N_AGENTS} | '
          f'{START}-{STOP} | draws={DRAWS_CSV.name}')

    t0 = pytime.time()
    if args.serial or len(tasks) == 1:
        dfs = [run_one(t) for t in tasks]
    else:
        with Pool(processes=min(args.n_workers, len(tasks))) as pool:
            dfs = list(pool.imap(run_one, tasks))
    out = pd.concat(dfs, ignore_index=True)

    out.to_parquet(OUT_PATH, index=False)
    print(f'[done] wrote {OUT_PATH} ({len(out)} rows) in {pytime.time()-t0:.0f}s')


if __name__ == '__main__':
    main()
