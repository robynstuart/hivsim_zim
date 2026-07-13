"""
Replica of Bansi-Matharu et al. 2025 (Lancet GH) Figure 3B — Zimbabwe.

Paper Fig 3B shows proportion of source partners by treatment status
(undiagnosed / diagnosed-not-on-ART / receiving-ART / post-ART) for
each of the 4 models that contributed Zimbabwe outputs (PopART, Goals,
Optima HIV, Synthesis), as stacked bars by year.

This figure adds a 5th panel for HIVsim in the same style, so the user
can compare HIVsim's cascade attribution directly against the 4 paper
models. The 4 paper panels are shown for reference by embedding the
Fig 3B JPEG on the left; HIVsim occupies the right.

Usage:
    python plot_fig3_replica.py
"""

from pathlib import Path

import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from utils import set_font

set_font(size=11)

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
    """For each year in `years`, take the ensemble median of the shares."""
    d = df[df.year.isin(years)].copy()
    d['total'] = (d.trans_undiagnosed_per_year
                  + d.trans_diag_not_on_art_per_year
                  + d.trans_on_art_per_year
                  + d.trans_post_art_per_year)
    d['share_undiag']   = np.where(d.total > 0, d.trans_undiagnosed_per_year     / d.total * 100, np.nan)
    d['share_diag_no']  = np.where(d.total > 0, d.trans_diag_not_on_art_per_year / d.total * 100, np.nan)
    d['share_on_art']   = np.where(d.total > 0, d.trans_on_art_per_year          / d.total * 100, np.nan)
    d['share_post']     = np.where(d.total > 0, d.trans_post_art_per_year        / d.total * 100, np.nan)
    med = d.groupby('year').median(numeric_only=True)[
        ['share_undiag', 'share_diag_no', 'share_on_art', 'share_post']]
    return med.reindex(years)


def plot_hivsim_panel(ax, med, years):
    xs = np.arange(len(years))
    width = 0.85
    bottom = np.zeros(len(years))
    for key in ['undiag', 'diag_no', 'on_art', 'post_art']:
        col = f'share_{key}' if key != 'post_art' else 'share_post'
        vals = med[col].to_numpy()
        vals = np.nan_to_num(vals, nan=0.0)
        ax.bar(xs, vals, width, bottom=bottom, color=COLORS[key], label=LABELS[key],
               edgecolor='white', linewidth=0.4)
        bottom = bottom + vals
    # x-tick labels: show every third year to match the paper style
    show_idx = list(range(0, len(years), 3))
    ax.set_xticks([xs[i] for i in show_idx])
    ax.set_xticklabels([years[i] for i in show_idx], rotation=45, ha='right', fontsize=9)
    ax.set_ylim(0, 100)
    ax.set_ylabel('Proportion of source partners (%)')
    ax.set_title('HIVsim', fontsize=11, pad=6)
    ax.spines[['top', 'right']].set_visible(False)


def main():
    df = pd.read_parquet(OUT)
    years = list(range(2000, 2041))
    med = compute_hivsim_shares(df, years)

    # Left panel: paper Fig 3B (Zimbabwe subplot images embedded as reference)
    fig = plt.figure(figsize=(14, 6.5))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.05, 1.0], wspace=0.15)

    ax_ref = fig.add_subplot(gs[0, 0])
    ref_path = REPO / 'reference' / 'fig3_zim.jpg'
    if ref_path.exists():
        img = mpimg.imread(ref_path)
        # Crop to Zimbabwe (B) block. The paper's Fig 3 stacks 3 country
        # blocks vertically; Zimbabwe (B) sits ~38-64% of the way down.
        h = img.shape[0]
        zim_block = img[int(h * 0.38):int(h * 0.64)]
        ax_ref.imshow(zim_block)
        ax_ref.set_title('Bansi-Matharu et al. 2025, Fig 3B (Zimbabwe): 4 published models',
                         fontsize=11, pad=6)
    else:
        ax_ref.text(0.5, 0.5, 'reference/fig3_zim.jpg not found',
                    ha='center', va='center', transform=ax_ref.transAxes)
    ax_ref.axis('off')

    ax = fig.add_subplot(gs[0, 1])
    plot_hivsim_panel(ax, med, years)
    ax.legend(loc='lower left', bbox_to_anchor=(0.0, -0.55), fontsize=9,
              frameon=False, ncol=2, handlelength=1.4)

    fig.suptitle('Ongoing HIV transmission source by cascade stage — Zimbabwe',
                 fontsize=12, y=0.99)
    fig.tight_layout()
    out = FIG_DIR / 'fig3_replica_zim.png'
    fig.savefig(out, dpi=140, bbox_inches='tight')
    print(f'wrote {out}')


if __name__ == '__main__':
    main()
