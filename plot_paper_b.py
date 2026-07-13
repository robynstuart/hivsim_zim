"""
Paper B (Bansi-Matharu et al. 2025, MIHPSA) overlay plots.

Reads outputs/zimbabwe_validation.parquet and produces two figures:

  1. 95-95-95 cascade over time for Zimbabwe (prop_diagnosed,
     prop_diag_on_art, prop_art_effective) with HIVsim ensemble band
     and Paper B benchmarks.

  2. Stacked-bar of ongoing sexual transmission by source cascade stage
     (undiagnosed / diagnosed-not-on-ART / on-ART / post-ART), 2024
     annual snapshot, with Paper B's 4-model Zimbabwe range shown as
     an inset table for comparison.

Usage:
    python plot_paper_b.py
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent
OUT = REPO / 'outputs' / 'zimbabwe_validation.parquet'
FIG_DIR = REPO / 'figures'
FIG_DIR.mkdir(exist_ok=True)


# Paper B 2024 Zimbabwe transmission-by-stage: range across the 4 models
# that contributed Zimbabwe outputs (PopART-IBM, Optima HIV, HIV Synthesis,
# Goals). Numbers from the paper's Figure 3B.
PAPER_B_2024 = {
    'undiagnosed':          (29.8, 64.6),
    'diag_not_on_art':      (0.0,   5.0),  # "<5% for all models"
    'on_art':               (19.5, 54.2),
    'post_art':             (4.7,  21.5),
}


def load():
    return pd.read_parquet(OUT)


def cascade_summary(df, col):
    g = df.groupby('year')[col]
    return pd.DataFrame({
        'median': g.median(),
        'p05':    g.quantile(0.05),
        'p95':    g.quantile(0.95),
    }).reset_index()


def transmission_shares_at_year(df, year):
    """For each (draw, seed) at `year`, compute the % share of transmissions
    coming from each cascade stage. Returns a DataFrame with columns
    [draw_idx, sub_idx, share_undiag, share_diag_no, share_on_art, share_post].
    """
    sub = df[df.year == year].copy()
    sub['total'] = (sub.trans_undiagnosed_per_year
                    + sub.trans_diag_not_on_art_per_year
                    + sub.trans_on_art_per_year
                    + sub.trans_post_art_per_year)
    for name, col in [('share_undiag',   'trans_undiagnosed_per_year'),
                      ('share_diag_no',  'trans_diag_not_on_art_per_year'),
                      ('share_on_art',   'trans_on_art_per_year'),
                      ('share_post',     'trans_post_art_per_year')]:
        sub[name] = np.where(sub['total'] > 0, sub[col] / sub['total'] * 100, np.nan)
    return sub[['draw_idx', 'sub_idx', 'share_undiag', 'share_diag_no',
                'share_on_art', 'share_post']]


def plot_cascade(df):
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5), sharey=True)
    cascades = [
        ('prop_diagnosed',     '1st 95: Diagnosed among PLHIV'),
        ('prop_diag_on_art',   '2nd 95: On ART among diagnosed'),
        ('prop_art_effective', '3rd 95 proxy: On ART past efficacy ramp'),
    ]
    for ax, (col, title) in zip(axes, cascades):
        c = cascade_summary(df, col)
        ax.fill_between(c.year, c.p05 * 100, c.p95 * 100, alpha=0.25, color='#2b5f8a',
                        label='HIVsim 5-95th %ile')
        ax.plot(c.year, c['median'] * 100, color='#2b5f8a', lw=2, label='HIVsim median')
        ax.axhline(95, color='#c44e52', ls='--', lw=1.2, label='95% target')
        ax.set_title(title, fontsize=11)
        ax.set_xlim(2000, 2040)
        ax.set_ylim(0, 105)
        ax.grid(alpha=0.3)
        ax.set_xlabel('Year')
    axes[0].set_ylabel('Percent')
    axes[0].legend(loc='lower right', fontsize=9)

    fig.suptitle('HIV treatment cascade for Zimbabwe (HIVsim vs 95-95-95 target)',
                 fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    out = FIG_DIR / 'paper_b_cascade.png'
    fig.savefig(out, dpi=140, bbox_inches='tight')
    print(f'wrote {out}')


def plot_transmission_by_stage(df, year=2024):
    shares = transmission_shares_at_year(df, year)
    # Ensemble spread across all (draw x seed) sims
    stage_labels = ['Undiagnosed', 'Diagnosed,\nnot on ART', 'On ART', 'Post-ART']
    cols  = ['share_undiag', 'share_diag_no', 'share_on_art', 'share_post']
    paper = ['undiagnosed', 'diag_not_on_art', 'on_art', 'post_art']

    fig, ax = plt.subplots(figsize=(9, 5.5))
    xs = np.arange(len(stage_labels))
    width = 0.35

    # HIVsim: 5-95th percentile
    med  = [shares[c].median() for c in cols]
    p05  = [shares[c].quantile(0.05) for c in cols]
    p95  = [shares[c].quantile(0.95) for c in cols]
    yerr = np.array([[m - lo for m, lo in zip(med, p05)],
                     [hi - m for m, hi in zip(med, p95)]])
    ax.bar(xs - width/2, med, width, yerr=yerr, capsize=4,
           color='#2b5f8a', alpha=0.85, label='HIVsim median (5-95th %ile)')

    # Paper B: 4-model range
    paper_med  = [(PAPER_B_2024[p][0] + PAPER_B_2024[p][1]) / 2 for p in paper]
    paper_yerr = np.array([[m - PAPER_B_2024[p][0] for p, m in zip(paper, paper_med)],
                           [PAPER_B_2024[p][1] - m for p, m in zip(paper, paper_med)]])
    ax.bar(xs + width/2, paper_med, width, yerr=paper_yerr, capsize=4,
           color='#8c564b', alpha=0.85, label='Paper B 4-model range')

    ax.set_xticks(xs)
    ax.set_xticklabels(stage_labels)
    ax.set_ylabel(f'% of new sexual transmissions ({year})')
    ax.set_title(f'HIVsim vs Paper B: transmission source by cascade stage, Zimbabwe {year}',
                 fontsize=12)
    ax.grid(alpha=0.3, axis='y')
    ax.legend()
    fig.tight_layout()
    out = FIG_DIR / 'paper_b_transmission_by_stage.png'
    fig.savefig(out, dpi=140, bbox_inches='tight')
    print(f'wrote {out}')


def main():
    df = load()
    plot_cascade(df)
    plot_transmission_by_stage(df, year=2024)


if __name__ == '__main__':
    main()
