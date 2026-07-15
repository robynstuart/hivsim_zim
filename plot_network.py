"""
Supplementary network figure. Panels:
    A: Lifetime partner distribution by sex (debuted agents only)
    B: Partner-age mixing heatmap (female age x male age density)
    C: Risk group composition by sex
    D: Cumulative distribution of age at sexual debut by sex
    E: Female partnership status by age (stable / casual)
    F: Condom use over time by partnership type
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as pl
import numpy as np
import pandas as pd
import sciris as sc
from matplotlib.gridspec import GridSpec

from utils import set_font

REPO = Path(__file__).resolve().parent
OUT_DIR = REPO / 'outputs'
FIG_DIR = REPO / 'figures'

F_COLOR = '#d46e9c'
M_COLOR = '#4a90d9'
RG_COLORS = ['#4daf4a', '#ff7f00', '#e41a1c']
RG_LABELS = ['Low risk', 'Medium risk', 'High risk']


def plot_lifetime_partners(data, ax):
    max_p = 20
    bins = np.arange(max_p + 2) - 0.5
    width = 0.35
    centers = np.arange(max_p + 1)
    f_vals = np.clip(data.lifetime_partners_f, 0, max_p)
    m_vals = np.clip(data.lifetime_partners_m, 0, max_p)
    f_prop = np.histogram(f_vals, bins=bins)[0] / max(1, len(f_vals))
    m_prop = np.histogram(m_vals, bins=bins)[0] / max(1, len(m_vals))
    ax.bar(centers - width/2, f_prop, width, color=F_COLOR, alpha=0.85, label='Female')
    ax.bar(centers + width/2, m_prop, width, color=M_COLOR, alpha=0.85, label='Male')
    ax.set_xlabel('Lifetime partners')
    ax.set_ylabel('Proportion')
    ax.set_title('Lifetime partner\ndistribution')
    ax.set_xlim(-1, max_p + 1)
    ax.set_xticks([0, 5, 10, 15, 20])
    ax.set_xticklabels(['0', '5', '10', '15', '20+'])
    ax.legend(frameon=False, fontsize=12)


def plot_age_heatmap(data, ax, fig):
    """F x M age-pairing density."""
    f_ages = np.asarray(data.f_ages)
    m_ages = np.asarray(data.m_ages)
    band = (f_ages >= 15) & (f_ages < 65) & (m_ages >= 15) & (m_ages < 65)
    f_ages, m_ages = f_ages[band], m_ages[band]
    bins = np.arange(15, 66, 2)
    h, xedges, yedges = np.histogram2d(f_ages, m_ages, bins=[bins, bins], density=True)
    im = ax.imshow(h.T, origin='lower', aspect='auto', cmap='magma_r',
                   extent=[xedges[0], xedges[-1], yedges[0], yedges[-1]])
    ax.plot([15, 65], [15, 65], color='w', lw=0.8, alpha=0.6, ls='--')
    ax.set_xlabel('Female age')
    ax.set_ylabel('Male age')
    ax.set_title('Partner age-pairing\ndensity (2020)')
    ax.set_xlim(15, 65)
    ax.set_ylim(15, 65)
    cbar = fig.colorbar(im, ax=ax, fraction=0.045, pad=0.03)
    cbar.set_label('Density', fontsize=11)


def plot_risk_groups(data, ax):
    rg = data.risk_group_data
    sexes = ['Female', 'Male']
    x = np.arange(len(sexes))
    width = 0.5
    bottom = np.zeros(len(sexes))
    for rg_idx in [0, 1, 2]:
        vals = np.array([rg[(s, rg_idx)] / rg[(s, 'total')] * 100 for s in sexes])
        ax.bar(x, vals, width, bottom=bottom, color=RG_COLORS[rg_idx],
               label=RG_LABELS[rg_idx], alpha=0.85)
        for xi, v in zip(x, vals):
            if v > 5:
                ax.text(xi, bottom[xi] + v/2, f'{v:.0f}%',
                        ha='center', va='center', fontsize=12)
        bottom += vals
    ax.set_xticks(x)
    ax.set_xticklabels(sexes)
    ax.set_ylabel('Proportion (%)')
    ax.set_title('Risk group\ncomposition')
    ax.set_ylim(0, 118)
    ax.legend(frameon=False, fontsize=11, loc='upper right')


def plot_debut_age(data, ax):
    for sex_label, color in [('Female', F_COLOR), ('Male', M_COLOR)]:
        ages = np.sort(data.debut_data[sex_label])
        cdf = np.arange(1, len(ages) + 1) / len(ages)
        ax.plot(ages, cdf, color=color, linewidth=2, label=sex_label)
        for q in [0.25, 0.50, 0.75]:
            val = np.percentile(ages, q * 100)
            ax.plot(val, q, 'o', color=color, markersize=6, zorder=5)
    ax.set_xlabel('Age (years)')
    ax.set_ylabel('Cumulative proportion')
    ax.set_title('Age at sexual debut')
    ax.set_xlim(12, 35)
    ax.set_ylim(0, 1.05)
    ax.axhline(0.5, color='grey', linestyle='--', alpha=0.3, linewidth=0.8)
    ax.legend(frameon=False, fontsize=12)


def plot_partnership_by_age(data, ax):
    pba = data.partnership_by_age
    ages = pba['age_bins']
    ax.plot(ages, pba['prop_stable'] * 100, color='#2171b5', linewidth=2, label='Stable partner')
    ax.plot(ages, pba['prop_casual'] * 100, color='#ff7f00', linewidth=2, label='1+ casual partner')
    ax.set_xlabel('Age (years)')
    ax.set_ylabel('Proportion of females (%)')
    ax.set_title('Female partnership\nstatus by age')
    ax.set_xlim(15, 50)
    ax.set_ylim(0, 100)
    ax.legend(frameon=False, fontsize=11)


def plot_condom_use(ax):
    df = pd.read_csv(REPO / 'data' / 'condom_use.csv')
    year_cols = [c for c in df.columns if c != 'partnership']
    years = [int(c) for c in year_cols]
    groups = {
        'Stable (low risk)': ['(0,0)'],
        'Cross-risk': ['(0,1)', '(0,2)', '(1,0)', '(1,2)', '(2,0)', '(2,1)'],
        'High risk': ['(1,1)', '(2,2)'],
        'FSW–client': ['(fsw,client)'],
    }
    colors = ['#4daf4a', '#ff7f00', '#e41a1c', '#984ea3']
    for (label, pairings), color in zip(groups.items(), colors):
        subset = df[df.partnership.isin(pairings)]
        vals = subset[year_cols].mean(axis=0).values
        ax.plot(years, vals, color=color, linewidth=2, label=label, marker='o', markersize=4)
    ax.set_xlabel('Year')
    ax.set_ylabel('Condom use probability')
    ax.set_title('Condom use over time')
    ax.set_ylim(0, 1.05)
    ax.legend(frameon=False, fontsize=10, loc='upper left')


if __name__ == '__main__':
    data = sc.loadobj(OUT_DIR / 'network_data.obj')
    set_font(size=9)
    fig = pl.figure(figsize=(10, 5))
    gs = GridSpec(2, 3, left=0.07, right=0.98, bottom=0.10, top=0.92,
                  wspace=0.40, hspace=0.55)
    panels = []
    panels.append(fig.add_subplot(gs[0, 0])); plot_lifetime_partners(data, panels[-1])
    panels.append(fig.add_subplot(gs[0, 1])); plot_age_heatmap(data, panels[-1], fig)
    panels.append(fig.add_subplot(gs[0, 2])); plot_risk_groups(data, panels[-1])
    panels.append(fig.add_subplot(gs[1, 0])); plot_debut_age(data, panels[-1])
    panels.append(fig.add_subplot(gs[1, 1])); plot_partnership_by_age(data, panels[-1])
    panels.append(fig.add_subplot(gs[1, 2])); plot_condom_use(panels[-1])
    for i, ax in enumerate(panels):
        ax.text(-0.14, 1.10, chr(65 + i), transform=ax.transAxes,
                fontsize=12, fontweight='bold', va='top')
    out = FIG_DIR / 'figs2_network.png'
    pl.savefig(out, dpi=200, bbox_inches='tight')
    print(f'wrote {out}')
