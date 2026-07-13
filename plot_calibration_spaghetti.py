"""
Calibration draw spaghetti: HIVsim's 30 sustaining draws vs UNAIDS.

Each draw is plotted as a thin line (mean across its K seeds), coloured
by its `hiv.beta_m2f` quintile so the reader can see how the calibrated
transmission rate maps to trajectory shape. UNAIDS surveillance is
overlaid as red dots.

Panels: HIV prevalence 15-49, PLHIV, new infections/yr, AIDS deaths/yr.

Intended as a supplementary calibration-transparency figure showing the
ensemble spread underneath the median + 5-95th percentile band in
Supplementary Figure S1.

Usage:
    python plot_calibration_spaghetti.py
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from utils import set_font

set_font(size=13)

REPO = Path(__file__).resolve().parent
OUT = REPO / 'outputs' / 'zimbabwe_validation.parquet'
DRAWS_CSV = REPO / 'calibration' / 'artifacts' / 'draws_sustaining_top30.csv'
FIG_DIR = REPO / 'figures'
FIG_DIR.mkdir(exist_ok=True)


def load_calibration_target():
    p = REPO / 'data' / 'zimbabwe_hiv_calib.csv'
    d = pd.read_csv(p)
    d['hiv_prevalence_pct'] = d['hiv_prevalence'] * 100
    d['hiv_prevalence_15_49_pct'] = d['hiv_prevalence_15_49'] * 100
    return d


def draw_beta_quintiles():
    draws = pd.read_csv(DRAWS_CSV)
    q = pd.qcut(draws['hiv.beta_m2f'], 5, labels=[1, 2, 3, 4, 5]).astype(int)
    return dict(zip(draws.draw_idx.astype(int), q))


def plot_panel(ax, ts, col, title, ylabel, calib_target=None, calib_col=None,
               cmap='viridis'):
    """Plot one line per draw (mean across seeds), coloured by beta quintile."""
    quintiles = draw_beta_quintiles()
    cmap_obj = plt.get_cmap(cmap)
    # Mean across seeds per (draw, year)
    per_draw = ts.groupby(['draw_idx', 'year'])[col].mean().reset_index()
    for draw_idx, g in per_draw.groupby('draw_idx'):
        q = quintiles.get(int(draw_idx), 3)
        colour = cmap_obj((q - 1) / 4.0)
        ax.plot(g.year, g[col], color=colour, lw=0.9, alpha=0.75)
    if calib_target is not None and calib_col is not None:
        ax.scatter(calib_target.time, calib_target[calib_col],
                   marker='o', s=22, color='#c44e52',
                   label='UNAIDS', zorder=5)
    ax.set_title(title, fontsize=13)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.tick_params(labelsize=11)
    ax.set_xlim(1990, 2040)
    ax.grid(alpha=0.3)


def main():
    df = pd.read_parquet(OUT)
    calib = load_calibration_target()

    fig, axes = plt.subplots(1, 4, figsize=(10, 5), sharex=True)

    plot_panel(axes[0], df, 'prev_15_49_pct',
               'HIV prevalence 15-49 (%)', '%',
               calib, 'hiv_prevalence_15_49_pct')

    plot_panel(axes[1], df, 'plhiv',
               'PLHIV (all ages)', 'count',
               calib, 'hiv_n_infected')
    axes[1].ticklabel_format(axis='y', style='sci', scilimits=(0, 0))

    plot_panel(axes[2], df, 'new_infections_per_year',
               'New infections / year', 'count',
               calib, 'hiv_new_infections')
    axes[2].ticklabel_format(axis='y', style='sci', scilimits=(0, 0))

    plot_panel(axes[3], df, 'aids_deaths_per_year',
               'AIDS-related deaths / year', 'count',
               calib, 'hiv_new_deaths')
    axes[3].ticklabel_format(axis='y', style='sci', scilimits=(0, 0))

    for ax in axes:
        ax.set_xlabel('Year', fontsize=11)

    # Colourbar-style legend for beta quintiles
    cmap_obj = plt.get_cmap('viridis')
    legend_handles = [
        plt.Line2D([0], [0], color=cmap_obj(i / 4.0), lw=2.5,
                   label=f'β Q{i+1}') for i in range(5)
    ]
    legend_handles.append(plt.Line2D([0], [0], marker='o', color='w',
                                     markerfacecolor='#c44e52', markersize=8,
                                     label='UNAIDS'))
    fig.legend(handles=legend_handles, loc='lower center', ncol=6,
               fontsize=11, bbox_to_anchor=(0.5, -0.05), frameon=False)

    fig.tight_layout(rect=[0, 0.04, 1, 1.0])
    out = FIG_DIR / 'calibration_spaghetti.png'
    fig.savefig(out, dpi=140, bbox_inches='tight')
    print(f'wrote {out}')


if __name__ == '__main__':
    main()
