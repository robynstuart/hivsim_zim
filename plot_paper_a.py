"""
Paper A (Taramusi et al. 2025) overlay plots.

Reads outputs/zimbabwe_validation.parquet (produced by
run_zimbabwe_validation.py) and produces a 2 x 3 grid comparing HIVsim
against the 5-model Zimbabwe published ranges:

    prev 15-49 | incidence 15-49 | new infections/year
    PLHIV      | number on ART   | AIDS-related deaths

Each panel shows the HIVsim ensemble (median + 5-95th percentile band
across draws x seeds), the empirical calibration target where available,
and Paper A's published 5-model range at benchmark years (2023, 2040).

Usage:
    python plot_paper_a.py
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent
OUT = REPO / 'outputs' / 'zimbabwe_validation.parquet'
FIG_DIR = REPO / 'figures'
FIG_DIR.mkdir(exist_ok=True)

# Paper A published Zimbabwe ranges (across 5 models: EMOD-HIV, Goals,
# HIV Synthesis, Optima, PopART-IBM). Numbers from Taramusi et al. 2025
# abstract summary; year-by-year traces still to be digitised from the
# paper's figures once the PDF is available.
PAPER_A_RANGES = {
    'prev_15_49_pct':       {2023: (12.1, 14.3), 2040: (3.9, 6.0)},   # percent
    'inc_15_49_per1000py':  {2023: (2.0, 3.3),   2040: (1.0, 3.0)},   # per 1000 py
    'new_infections_per_year': {2025: (0, 7800)},                     # below 7800 by 2025
}


def load():
    return pd.read_parquet(OUT)


def ensemble_summary(df, col):
    """Aggregate to (year, median, p05, p95) across draw_idx x sub_idx."""
    g = df.groupby('year')[col]
    return pd.DataFrame({
        'median': g.median(),
        'p05':    g.quantile(0.05),
        'p95':    g.quantile(0.95),
    }).reset_index()


def load_calibration_target():
    """The whole-pop calibration target (data/zimbabwe_hiv_calib.csv)."""
    p = REPO / 'data' / 'zimbabwe_hiv_calib.csv'
    if not p.exists():
        return None
    d = pd.read_csv(p)
    d['hiv_prevalence_pct'] = d['hiv_prevalence'] * 100
    return d


def plot_panel(ax, df, col, title, ylabel, published_ranges=None,
               calib_target=None, calib_col=None, calib_label=None):
    ens = ensemble_summary(df, col)
    ax.fill_between(ens.year, ens.p05, ens.p95, alpha=0.25,
                    color='#2b5f8a', label='HIVsim 5-95th %ile (draws x seeds)')
    ax.plot(ens.year, ens['median'], color='#2b5f8a', lw=2,
            label='HIVsim median')

    if calib_target is not None and calib_col is not None:
        ax.scatter(calib_target.time, calib_target[calib_col],
                   marker='o', s=18, color='#c44e52',
                   label=calib_label or 'Empirical target', zorder=5)

    if published_ranges:
        for year, (lo, hi) in published_ranges.items():
            ax.plot([year, year], [lo, hi], color='#8c564b', lw=6,
                    solid_capstyle='butt', alpha=0.85,
                    label='Paper A 5-model range' if year == min(published_ranges) else None)

    ax.set_title(title, fontsize=11)
    ax.set_ylabel(ylabel)
    ax.set_xlim(1990, 2040)
    ax.grid(alpha=0.3)


def main():
    df = load()
    calib = load_calibration_target()
    fig, axes = plt.subplots(2, 3, figsize=(15, 9), sharex=True)

    plot_panel(axes[0, 0], df, 'prev_15_49_pct',
               'HIV prevalence, 15-49', '%',
               published_ranges=PAPER_A_RANGES['prev_15_49_pct'],
               calib_target=calib, calib_col='hiv_prevalence_pct',
               calib_label='Whole-pop calibration target (UNAIDS)')

    plot_panel(axes[0, 1], df, 'inc_15_49_per1000py',
               'HIV incidence, 15-49', 'per 1000 person-years',
               published_ranges=PAPER_A_RANGES['inc_15_49_per1000py'])

    plot_panel(axes[0, 2], df, 'new_infections_per_year',
               'New HIV infections per year (all ages)', 'count',
               published_ranges=PAPER_A_RANGES['new_infections_per_year'],
               calib_target=calib, calib_col='hiv_new_infections',
               calib_label='Calibration target')

    plot_panel(axes[1, 0], df, 'plhiv',
               'People living with HIV (all ages)', 'count',
               calib_target=calib, calib_col='hiv_n_infected',
               calib_label='Calibration target')

    plot_panel(axes[1, 1], df, 'n_on_art',
               'Number on ART (all ages)', 'count')

    plot_panel(axes[1, 2], df, 'aids_deaths_per_year',
               'AIDS-related deaths per year (all ages)', 'count',
               calib_target=calib, calib_col='hiv_new_deaths',
               calib_label='Calibration target')

    for ax in axes.flat:
        ax.set_xlabel('Year')

    # One legend at figure level (dedupe)
    handles, labels = [], []
    for ax in axes.flat:
        for h, l in zip(*ax.get_legend_handles_labels()):
            if l not in labels:
                handles.append(h); labels.append(l)
    fig.legend(handles, labels, loc='lower center', ncol=4, fontsize=10,
               bbox_to_anchor=(0.5, -0.02))

    fig.suptitle('HIVsim Zimbabwe vs Taramusi et al. 2025 5-model comparison '
                 '(status quo, 1990-2040)', fontsize=13)
    fig.tight_layout(rect=[0, 0.03, 1, 0.97])
    out = FIG_DIR / 'paper_a_overlay.png'
    fig.savefig(out, dpi=140, bbox_inches='tight')
    print(f'wrote {out}')


if __name__ == '__main__':
    main()
