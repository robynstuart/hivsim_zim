"""
Replica of Bansi-Matharu et al. 2025 (Lancet GH) Figure 3B — Zimbabwe.

Layout: HIVsim stacked-bar panel on the left (full height). Right column
stacks the paper's Fig 3B Zimbabwe block (4 published models, natural
aspect) on top of the 2024 transmission-by-stage HIVsim-vs-paper bar
chart in the space below.

Usage:
    python plot_fig4_replica.py
"""

from pathlib import Path

import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from plot_paper_b import PAPER_B_2024, transmission_shares_at_year
from utils import set_font

set_font(size=13)

REPO = Path(__file__).resolve().parent
OUT = REPO / 'outputs' / 'zimbabwe_validation.parquet'
FIG_DIR = REPO / 'figures'
FIG_DIR.mkdir(exist_ok=True)

# Paper Fig 3 colour scheme (approximated from the JPEG legend)
COLORS = {
    'undiag':   '#8ecdd8',  # light cyan-blue
    'diag_no':  '#f3d34a',  # yellow
    'on_art':   '#a3c785',  # muted green
    'post_art': '#e07068',  # coral-red
}
LABELS = {
    'undiag':   'Undiagnosed',
    'diag_no':  'Diagnosed but treatment naive',
    'on_art':   'Receiving treatment',
    'post_art': 'Not receiving treatment\n(after having started treatment)',
}


def compute_hivsim_shares(df, years):
    """Ensemble transmission attribution as a % of total, summing to 100.

    Aggregating raw counts across the ensemble FIRST (sum over draws x seeds)
    then dividing keeps the four shares self-consistent — taking medians per
    share independently does not. Missing years get NaN so the bars are blank.
    """
    d = df[df.year.isin(years)].copy()
    cols_raw = ['trans_undiagnosed_per_year', 'trans_diag_not_on_art_per_year',
                'trans_on_art_per_year',      'trans_post_art_per_year']
    agg = d.groupby('year')[cols_raw].sum()
    totals = agg.sum(axis=1)
    shares = agg.divide(totals.where(totals > 0, np.nan), axis=0) * 100
    shares.columns = ['share_undiag', 'share_diag_no', 'share_on_art', 'share_post']
    return shares.reindex(years)


def plot_hivsim_panel(ax, shares, years):
    xs = np.arange(len(years))
    width = 0.85
    bottom = np.zeros(len(years))
    key_to_col = {'undiag': 'share_undiag', 'diag_no': 'share_diag_no',
                  'on_art': 'share_on_art', 'post_art': 'share_post'}
    for key in ['undiag', 'diag_no', 'on_art', 'post_art']:
        vals = np.nan_to_num(shares[key_to_col[key]].to_numpy(), nan=0.0)
        ax.bar(xs, vals, width, bottom=bottom, color=COLORS[key], label=LABELS[key],
               edgecolor='white', linewidth=0.4)
        bottom = bottom + vals
    show_idx = list(range(0, len(years), 5))
    ax.set_xticks([xs[i] for i in show_idx])
    ax.set_xticklabels([years[i] for i in show_idx], rotation=0, fontsize=10)
    ax.tick_params(axis='y', labelsize=10)
    ax.set_ylim(0, 100)
    ax.set_ylabel('Source partners (%)', fontsize=11)
    ax.set_title('HIVsim', fontsize=12, pad=4)
    ax.spines[['top', 'right']].set_visible(False)


def plot_transmission_by_stage_panel(ax, df, year=2024):
    shares = transmission_shares_at_year(df, year)
    stage_labels = ['Undiagnosed', 'Diagnosed,\nnot on ART', 'On ART', 'Post-ART']
    cols = ['share_undiag', 'share_diag_no', 'share_on_art', 'share_post']
    paper_keys = ['undiagnosed', 'diag_not_on_art', 'on_art', 'post_art']
    xs = np.arange(len(stage_labels))
    width = 0.35

    means = [shares[c].mean() for c in cols]
    lo    = [shares[c].min()  for c in cols]
    hi    = [shares[c].max()  for c in cols]
    yerr = np.array([[m - l for m, l in zip(means, lo)],
                     [h - m for m, h in zip(means, hi)]])
    ax.bar(xs - width/2, means, width, yerr=yerr, capsize=3,
           color='#2b5f8a', alpha=0.85, label='HIVsim (mean, min–max)')

    p_mid = [(PAPER_B_2024[k][0] + PAPER_B_2024[k][1]) / 2 for k in paper_keys]
    p_err = np.array([[m - PAPER_B_2024[k][0] for k, m in zip(paper_keys, p_mid)],
                      [PAPER_B_2024[k][1] - m for k, m in zip(paper_keys, p_mid)]])
    ax.bar(xs + width/2, p_mid, width, yerr=p_err, capsize=3,
           color='#8c564b', alpha=0.85, label='Bansi-Matharu 4-model range')

    ax.set_xticks(xs)
    ax.set_xticklabels(stage_labels, fontsize=8.5)
    ax.tick_params(axis='y', labelsize=9)
    ax.set_ylabel(f'% new transmissions ({year})', fontsize=10)
    ax.grid(alpha=0.3, axis='y')
    ax.legend(fontsize=7.5, loc='upper right', frameon=True, framealpha=0.9,
              edgecolor='none')
    ax.spines[['top', 'right']].set_visible(False)


def main():
    df = pd.read_parquet(OUT)
    years = list(range(2000, 2041))
    shares = compute_hivsim_shares(df, years)

    fig = plt.figure(figsize=(10, 5))
    gs_outer = fig.add_gridspec(1, 2, width_ratios=[1.0, 1.0], wspace=0.22,
                                left=0.07, right=0.98, top=0.94, bottom=0.20)

    ax_hivsim = fig.add_subplot(gs_outer[0, 0])
    plot_hivsim_panel(ax_hivsim, shares, years)
    handles, labels = ax_hivsim.get_legend_handles_labels()
    fig.legend(handles, labels, loc='lower center', bbox_to_anchor=(0.28, 0.01),
               fontsize=8.5, frameon=False, ncol=2, handlelength=1.2,
               columnspacing=1.2)

    gs_right = gs_outer[0, 1].subgridspec(2, 1, height_ratios=[1.4, 1.0],
                                          hspace=0.45)

    ax_ref = fig.add_subplot(gs_right[0, 0])
    ref_path = REPO / 'reference' / 'fig3_zim.jpg'
    if ref_path.exists():
        img = mpimg.imread(ref_path)
        h = img.shape[0]
        zim_block = img[int(h * 0.38):int(h * 0.64)]
        ax_ref.imshow(zim_block)
        ax_ref.set_title('Bansi-Matharu 2025, Fig 3B (4 published models)',
                         fontsize=10, pad=3)
    else:
        ax_ref.text(0.5, 0.5, 'reference/fig3_zim.jpg not found',
                    ha='center', va='center', transform=ax_ref.transAxes)
    ax_ref.axis('off')

    ax_bar = fig.add_subplot(gs_right[1, 0])
    plot_transmission_by_stage_panel(ax_bar, df, year=2024)

    out = FIG_DIR / 'fig4_replica_zim.png'
    fig.savefig(out, dpi=140)
    print(f'wrote {out}')


if __name__ == '__main__':
    main()
