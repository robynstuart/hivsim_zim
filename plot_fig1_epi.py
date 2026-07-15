"""
Figure 1 — HIV epidemiology in Zimbabwe.

Ensemble (top-50 draws from exp_09 LHS) overlaid on UNAIDS 1990-2024
and ZIMPHIA 2015-16 / 2020 anchors.

Layout (4 rows):
    Row 1 (3 panels): HIV prevalence 15-49, PLHIV, ART coverage
    Row 2 (3 panels): new infections/yr, AIDS deaths/yr, number on ART
    Row 3 (4 mini panels): HIV prevalence by age (F, M) at 2005/2016/2020/2025,
                            ZIMPHIA 2016 + 2020 CIs overlaid
    Row 4 (1 wide panel): new HIV infections by sex-work status stacked area
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.gridspec import GridSpec

from utils import set_font

REPO = Path(__file__).resolve().parent
FIG_DIR = REPO / 'figures'
EXP_09 = REPO / 'experiments' / 'exp_09_extended_lhs' / 'outputs'

ENSEMBLE_COLOR = '#2b5f8a'
UNAIDS_COLOR = '#c44e52'
ZIMPHIA_F = '#d46e9c'
ZIMPHIA_M = '#4a90d9'

# ZIMPHIA 2015-16 HIV prevalence by age and sex, with 95% CIs.
# Format: age_group: (f_point, m_point, f_lo, f_hi, m_lo, m_hi).
# Values reproduce syph_dx_zim/plot_fig1_epi.py.
ZIMPHIA_HIV_2016 = {
    '15-20': (0.040, 0.025, 0.028, 0.052, 0.015, 0.035),
    '20-25': (0.077, 0.034, 0.059, 0.095, 0.020, 0.048),
    '25-30': (0.137, 0.077, 0.113, 0.161, 0.055, 0.099),
    '30-35': (0.207, 0.148, 0.175, 0.239, 0.118, 0.178),
    '35-50': (0.233, 0.207, 0.198, 0.268, 0.173, 0.241),
    '50-65': (0.130, 0.142, 0.091, 0.169, 0.098, 0.186),
}
ZIMPHIA_HIV_2020 = {
    '15-20': (0.038, 0.021, 0.026, 0.050, 0.012, 0.030),
    '20-25': (0.064, 0.028, 0.048, 0.080, 0.016, 0.040),
    '25-30': (0.106, 0.040, 0.084, 0.128, 0.025, 0.055),
    '30-35': (0.184, 0.093, 0.154, 0.214, 0.070, 0.116),
    '35-50': (0.295, 0.208, 0.254, 0.336, 0.169, 0.247),
    '50-65': (0.250, 0.251, 0.209, 0.291, 0.200, 0.302),
}

AGE_BANDS = ['15-20', '20-25', '25-30', '30-35', '35-50', '50-65']
AGE_BAND_COLS = ['15_20', '20_25', '25_30', '30_35', '35_50', '50_65']


def load_ensemble():
    """Load exp_09 top-50 draws filtered ensemble."""
    ens = pd.read_parquet(EXP_09 / 'lhs_coverage.parquet')
    top = pd.read_csv(EXP_09 / 'draws_top50.csv')
    return ens[ens.draw_idx.isin(top.draw_idx)].copy()


def load_targets():
    d = pd.read_csv(REPO / 'data' / 'zimbabwe_hiv_calib.csv')
    art_n = pd.read_csv(REPO / 'data' / 'n_art.csv').rename(columns={'year': 'time'})
    art_p = pd.read_csv(REPO / 'data' / 'p_art.csv').rename(columns={'year': 'time', 'p_art': 'p_art'})
    return d.merge(art_n[['time', 'n_art']], on='time', how='left') \
            .merge(art_p, on='time', how='left')


def plot_ts_panel(ax, ens, targets, sim_col, targ_col, title, scale=1.0, unit=''):
    by_year = ens.groupby('year')[sim_col]
    p05 = by_year.quantile(0.05) * scale
    p95 = by_year.quantile(0.95) * scale
    med = by_year.median() * scale
    ax.fill_between(p05.index, p05, p95, alpha=0.22, color=ENSEMBLE_COLOR,
                    label='Top-50 ensemble 5–95%')
    ax.plot(med.index, med, color=ENSEMBLE_COLOR, lw=1.8, label='Ensemble median')
    if targ_col is not None and targ_col in targets.columns:
        t = targets.dropna(subset=[targ_col])
        ax.scatter(t.time, t[targ_col] * scale, s=28, color=UNAIDS_COLOR,
                   zorder=5, label='UNAIDS')
    ax.set_title(title, fontsize=10)
    if unit:
        ax.set_ylabel(unit, fontsize=9)
    ax.set_xlim(1990, 2040)
    ax.grid(alpha=0.3)
    ax.tick_params(labelsize=8)


def plot_age_snapshot(ax, ens, year, zimphia_lookup=None, show_ylabel=False):
    """Prev by age × sex at one year; optional ZIMPHIA CI overlay."""
    sub = ens[ens.year == year]
    x = np.arange(len(AGE_BANDS))
    width = 0.35
    for i, ab in enumerate(AGE_BAND_COLS):
        f_col = f'hiv.prevalence_f_{ab}'
        m_col = f'hiv.prevalence_m_{ab}'
        f_vals = sub[f_col].dropna() * 100
        m_vals = sub[m_col].dropna() * 100
        ax.bar(x[i] - width/2, f_vals.median(), width, color=ZIMPHIA_F, alpha=0.75,
               label='Female (model)' if i == 0 else None)
        ax.bar(x[i] + width/2, m_vals.median(), width, color=ZIMPHIA_M, alpha=0.75,
               label='Male (model)' if i == 0 else None)
        # 5-95 error bars
        ax.errorbar(x[i] - width/2, f_vals.median(),
                    yerr=[[f_vals.median() - f_vals.quantile(0.05)],
                          [f_vals.quantile(0.95) - f_vals.median()]],
                    color='black', capsize=2, lw=0.8)
        ax.errorbar(x[i] + width/2, m_vals.median(),
                    yerr=[[m_vals.median() - m_vals.quantile(0.05)],
                          [m_vals.quantile(0.95) - m_vals.median()]],
                    color='black', capsize=2, lw=0.8)
    if zimphia_lookup is not None:
        for i, ab in enumerate(AGE_BANDS):
            if ab in zimphia_lookup:
                f_pt, m_pt, f_lo, f_hi, m_lo, m_hi = zimphia_lookup[ab]
                ax.errorbar(x[i] - width/2, f_pt * 100,
                            yerr=[[(f_pt - f_lo) * 100], [(f_hi - f_pt) * 100]],
                            fmt='D', color=UNAIDS_COLOR, markersize=5,
                            capsize=3, lw=1.2,
                            label='ZIMPHIA F' if i == 0 else None)
                ax.errorbar(x[i] + width/2, m_pt * 100,
                            yerr=[[(m_pt - m_lo) * 100], [(m_hi - m_pt) * 100]],
                            fmt='s', color='#7b2d67', markersize=5,
                            capsize=3, lw=1.2,
                            label='ZIMPHIA M' if i == 0 else None)
    ax.set_xticks(x)
    ax.set_xticklabels(AGE_BANDS, rotation=45, fontsize=7)
    ax.set_title(f'{year}', fontsize=10)
    if show_ylabel:
        ax.set_ylabel('%', fontsize=9)
    ax.grid(alpha=0.3, axis='y')
    ax.set_ylim(0, 40)
    ax.tick_params(labelsize=8)


def plot_infections_by_sw(ax, ens):
    """Stacked area of new HIV infections by SW status."""
    by_year = ens.groupby('year')[['hiv.new_infections_sw',
                                    'hiv.new_infections_client',
                                    'hiv.new_infections']].median() / 1000
    fsw = by_year['hiv.new_infections_sw']
    client = by_year['hiv.new_infections_client']
    gen = (by_year['hiv.new_infections'] - fsw - client).clip(lower=0)
    ax.stackplot(fsw.index, fsw, client, gen,
                 colors=['#e41a1c', '#ff7f00', '#4daf4a'],
                 labels=['FSW', 'Clients', 'Gen pop'], alpha=0.85)
    ax.set_title('New infections by SW status', fontsize=10)
    ax.set_ylabel('thousands / yr', fontsize=9)
    ax.set_xlim(1990, 2040)
    ax.grid(alpha=0.3)
    ax.legend(loc='upper right', fontsize=7, frameon=False)
    ax.tick_params(labelsize=8)


def main():
    set_font(size=10)
    ens = load_ensemble()
    targets = load_targets()

    fig = plt.figure(figsize=(10, 5))
    gs = GridSpec(2, 3, figure=fig, hspace=0.55, wspace=0.35,
                  left=0.07, right=0.98, top=0.92, bottom=0.10)

    ax = fig.add_subplot(gs[0, 0])
    plot_ts_panel(ax, ens, targets, 'hiv.prevalence_15_49', 'hiv.prevalence_15_49',
                  'HIV prevalence, adults 15–49', scale=100, unit='%')
    ax.legend(loc='upper right', fontsize=7, frameon=False)

    ax = fig.add_subplot(gs[0, 1])
    plot_ts_panel(ax, ens, targets, 'hiv.n_infected', 'hiv.n_infected',
                  'People living with HIV', scale=1e-6, unit='millions')

    ax = fig.add_subplot(gs[0, 2])
    plot_ts_panel(ax, ens, targets, 'hiv.new_infections', 'hiv.new_infections',
                  'New HIV infections / yr', scale=1e-3, unit='thousands')

    ax = fig.add_subplot(gs[1, 0])
    plot_ts_panel(ax, ens, targets, 'hiv.new_deaths', 'hiv.new_deaths',
                  'AIDS-related deaths / yr', scale=1e-3, unit='thousands')

    ax = fig.add_subplot(gs[1, 1])
    plot_age_snapshot(ax, ens, 2020, zimphia_lookup=ZIMPHIA_HIV_2020,
                      show_ylabel=True)
    ax.set_title('HIV prevalence by age (2020)', fontsize=10)
    ax.legend(loc='upper left', fontsize=6, frameon=False, ncol=1)

    ax = fig.add_subplot(gs[1, 2])
    plot_infections_by_sw(ax, ens)

    labels = [(gs[0, 0], 'A'), (gs[0, 1], 'B'), (gs[0, 2], 'C'),
              (gs[1, 0], 'D'), (gs[1, 1], 'E'), (gs[1, 2], 'F')]
    for spec, lab in labels:
        ss = spec.get_position(fig)
        fig.text(ss.x0 - 0.010, ss.y1 + 0.005, lab,
                 fontsize=12, fontweight='bold', va='bottom', ha='right')

    out = FIG_DIR / 'fig1_hiv_epi.png'
    fig.savefig(out, dpi=180, bbox_inches='tight')
    print(f'wrote {out}')


if __name__ == '__main__':
    main()
