"""
Calibration-fit figure: HIVsim ensemble vs Zimbabwe HIV surveillance.

Reads outputs/zimbabwe_validation.parquet (produced by
run_zimbabwe_validation.py) and produces a 2 x 3 grid showing HIVsim's
ensemble median + 5-95th percentile band against the empirical Zimbabwe
HIV data compiled from UNAIDS:

    prev 15-49 | incidence 15-49 | new infections/year
    PLHIV      | number on ART   | AIDS-related deaths

Intended as a supplementary calibration-fit diagnostic for the preprint.

Usage:
    python plot_calibration_fit.py
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from utils import set_font

set_font(size=13)

REPO = Path(__file__).resolve().parent
OUT = REPO / 'outputs' / 'zimbabwe_validation.parquet'
FIG_DIR = REPO / 'figures'
FIG_DIR.mkdir(exist_ok=True)


def ensemble_summary(df, col):
    """Aggregate to (year, median, p05, p95) across draw_idx x sub_idx."""
    g = df.groupby('year')[col]
    return pd.DataFrame({
        'median': g.median(),
        'p05':    g.quantile(0.05),
        'p95':    g.quantile(0.95),
    }).reset_index()


def load_calibration_target():
    """Zimbabwe HIV surveillance data (data/zimbabwe_hiv_calib.csv).

    Dot-notation columns matching sim results: hiv.prevalence, hiv.n_infected,
    hiv.new_infections, hiv.new_deaths, hiv.prevalence_15_49, plus whole-pop
    n_alive (implied denominator from UNAIDS).
    """
    p = REPO / 'data' / 'zimbabwe_hiv_calib.csv'
    if not p.exists():
        return None
    d = pd.read_csv(p)
    d['hiv_prevalence_pct'] = d['hiv.prevalence'] * 100
    d['hiv_prevalence_15_49_pct'] = d['hiv.prevalence_15_49'] * 100
    return d


def plot_panel(ax, df, col, title, ylabel, calib_target=None,
               calib_col=None, calib_label=None):
    ens = ensemble_summary(df, col)
    ax.fill_between(ens.year, ens.p05, ens.p95, alpha=0.25,
                    color='#2b5f8a', label='HIVsim 5-95th %ile (draws x seeds)')
    ax.plot(ens.year, ens['median'], color='#2b5f8a', lw=2.2,
            label='HIVsim median')

    if calib_target is not None and calib_col is not None:
        ax.scatter(calib_target.time, calib_target[calib_col],
                   marker='o', s=22, color='#c44e52',
                   label=calib_label or 'Empirical target', zorder=5)

    ax.set_title(title, fontsize=13)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.tick_params(labelsize=11)
    ax.set_xlim(1990, 2040)
    ax.grid(alpha=0.3)


def main():
    df = pd.read_parquet(OUT)
    calib = load_calibration_target()
    fig, axes = plt.subplots(2, 3, figsize=(10, 5), sharex=True)

    plot_panel(axes[0, 0], df, 'prev_15_49_pct',
               'HIV prevalence, 15-49', '%',
               calib_target=calib, calib_col='hiv_prevalence_15_49_pct',
               calib_label='UNAIDS 15-49 estimate')

    plot_panel(axes[0, 1], df, 'inc_15_49_per1000py',
               'HIV incidence, 15-49', 'per 1000 person-years')

    plot_panel(axes[0, 2], df, 'new_infections_per_year',
               'New HIV infections per year (all ages)', 'count',
               calib_target=calib, calib_col='hiv.new_infections',
               calib_label='UNAIDS estimate')

    plot_panel(axes[1, 0], df, 'plhiv',
               'People living with HIV (all ages)', 'count',
               calib_target=calib, calib_col='hiv.n_infected',
               calib_label='UNAIDS estimate')

    plot_panel(axes[1, 1], df, 'n_on_art',
               'Number on ART (all ages)', 'count')

    plot_panel(axes[1, 2], df, 'aids_deaths_per_year',
               'AIDS-related deaths per year (all ages)', 'count',
               calib_target=calib, calib_col='hiv.new_deaths',
               calib_label='UNAIDS estimate')

    for ax in axes[1, :]:
        ax.set_xlabel('Year', fontsize=11)

    handles, labels = [], []
    for ax in axes.flat:
        for h, l in zip(*ax.get_legend_handles_labels()):
            if l not in labels:
                handles.append(h); labels.append(l)
    fig.legend(handles, labels, loc='lower center', ncol=3, fontsize=11,
               bbox_to_anchor=(0.5, -0.06))

    fig.tight_layout(rect=[0, 0.04, 1, 1.0])
    out = FIG_DIR / 'hivsim_vs_unaids_calibration.png'
    fig.savefig(out, dpi=140, bbox_inches='tight')
    print(f'wrote {out}')


if __name__ == '__main__':
    main()
