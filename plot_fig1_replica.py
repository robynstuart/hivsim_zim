"""
Replica of Bansi-Matharu et al. 2025 (Lancet GH) Figure 1B — Zimbabwe.

Six panels for the 4 published models + HIVsim overlay:
    1) Population size (aged 15-64 years)
    2) HIV prevalence (%)
    3) Number of new HIV infections per year
    4) Proportion of PLHIV who are diagnosed (%)
    5) Proportion of PLHIV receiving ART (%)
    6) Proportion of on-ART who are virally suppressed (%)

The 4 published-model traces are eyeball-digitised from
`reference/fig1_zim.jpg` at ~5-year intervals into
`reference/paper_b_fig1_zimbabwe_digitised.csv`; precision +/- 3-5%.
HIVsim is shown as the ensemble median + 5-95th percentile band.

Usage:
    python plot_fig1_replica.py
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from utils import set_font

set_font(size=11)

REPO = Path(__file__).resolve().parent
OUT = REPO / 'outputs' / 'zimbabwe_validation.parquet'
FIG_DIR = REPO / 'figures'
DIGITISED_CSV = REPO / 'reference' / 'paper_b_fig1_zimbabwe_digitised.csv'
FIG_DIR.mkdir(exist_ok=True)

MODEL_COLORS = {
    'Optima':    '#2b8ea1',   # cyan
    'Synthesis': '#e2b64e',   # yellow
    'PopART':    '#3e8f57',   # green
    'Goals':     '#8b6ba1',   # purple/lavender
}
HIVSIM_COLOR = '#c44e52'      # red for contrast


def hivsim_summary(df, col):
    g = df.groupby('year')[col]
    return pd.DataFrame({
        'median': g.median(),
        'p05':    g.quantile(0.05),
        'p95':    g.quantile(0.95),
    }).reset_index()


def plot_paper_lines(ax, dig, metric, scale=1.0):
    sub = dig[dig.metric == metric]
    for model in ['Optima', 'Synthesis', 'PopART', 'Goals']:
        m = sub[sub.model == model].sort_values('year')
        if len(m):
            ax.plot(m.year, m.value * scale, color=MODEL_COLORS[model],
                    lw=1.6, marker='o', ms=3, label=model, alpha=0.9)


def plot_hivsim(ax, df, col, scale=1.0):
    s = hivsim_summary(df, col)
    ax.fill_between(s.year, s.p05 * scale, s.p95 * scale,
                    color=HIVSIM_COLOR, alpha=0.20)
    ax.plot(s.year, s['median'] * scale, color=HIVSIM_COLOR, lw=2.0,
            label='HIVsim')


def main():
    df = pd.read_parquet(OUT)
    dig = pd.read_csv(DIGITISED_CSV, comment='#')

    # Derive HIVsim columns
    df['prev_15_64_pct'] = df.n_infected_15_64 / df.n_alive_15_64 * 100

    fig, axes = plt.subplots(3, 2, figsize=(13, 12), sharex=True)

    # Panel 1: population size 15-64
    ax = axes[0, 0]
    plot_paper_lines(ax, dig, 'pop_15_64')
    plot_hivsim(ax, df, 'n_alive_15_64')
    ax.set_title('Population size (aged 15-64 years)')
    ax.set_ylabel('People')
    ax.ticklabel_format(axis='y', style='sci', scilimits=(0, 0))

    # Panel 2: HIV prev (15-64)
    ax = axes[0, 1]
    plot_paper_lines(ax, dig, 'prev')
    plot_hivsim(ax, df, 'prev_15_64_pct')
    ax.set_title('HIV prevalence (%), 15-64')
    ax.set_ylabel('%')
    ax.set_ylim(0, 22)

    # Panel 3: new infections/year (whole-pop from paper; 15-64 from HIVsim)
    ax = axes[1, 0]
    plot_paper_lines(ax, dig, 'new_inf')
    plot_hivsim(ax, df, 'new_infections_per_year')
    ax.set_title('Number of new HIV infections per year')
    ax.set_ylabel('People')
    ax.ticklabel_format(axis='y', style='sci', scilimits=(0, 0))

    # Panel 4: proportion diagnosed
    ax = axes[1, 1]
    plot_paper_lines(ax, dig, 'p_dx')
    plot_hivsim(ax, df, 'prop_diagnosed', scale=100)
    ax.set_title('Proportion of PLHIV diagnosed (%)')
    ax.set_ylabel('%')
    ax.set_ylim(0, 105)

    # Panel 5: proportion of PLHIV on ART. HIVsim doesn't expose this directly
    # so compute n_on_art / plhiv.
    df['p_on_art_of_plhiv'] = df.n_on_art / df.plhiv * 100
    ax = axes[2, 0]
    plot_paper_lines(ax, dig, 'p_on_art')
    plot_hivsim(ax, df, 'p_on_art_of_plhiv')
    ax.set_title('Proportion of PLHIV receiving ART (%)')
    ax.set_ylabel('%')
    ax.set_ylim(0, 105)

    # Panel 6: proportion of on-ART virally suppressed. HIVsim proxy:
    # prop_art_effective is "on ART past efficacy ramp" as fraction of on-ART.
    ax = axes[2, 1]
    plot_paper_lines(ax, dig, 'p_vls')
    plot_hivsim(ax, df, 'prop_art_effective', scale=100)
    ax.set_title('Proportion of on-ART virally suppressed (%)')
    ax.set_ylabel('%')
    ax.set_ylim(0, 105)

    for ax in axes.flat:
        ax.set_xlim(2000, 2040)
        ax.set_xlabel('Year')
        ax.grid(alpha=0.25)

    # Single figure-level legend
    handles, labels = [], []
    for ax in axes.flat:
        for h, l in zip(*ax.get_legend_handles_labels()):
            if l not in labels:
                handles.append(h); labels.append(l)
    fig.legend(handles, labels, loc='lower center', ncol=5, fontsize=10,
               bbox_to_anchor=(0.5, -0.01))

    fig.suptitle('HIVsim Zimbabwe vs Bansi-Matharu et al. 2025, Fig 1B '
                 '(4 published models eyeball-digitised)', fontsize=12)
    fig.tight_layout(rect=[0, 0.02, 1, 0.97])

    out = FIG_DIR / 'fig1_replica_zim.png'
    fig.savefig(out, dpi=140, bbox_inches='tight')
    print(f'wrote {out}')


if __name__ == '__main__':
    main()
