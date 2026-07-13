"""
Replica of Bansi-Matharu et al. 2025 (Lancet GH) Figure 2B — Zimbabwe.

Mean age at HIV acquisition (years), by sex, for the 4 published models +
HIVsim overlay. Published-model traces are eyeball-digitised from
`reference/fig2_zim.jpg` (+/- 1-2 years precision); HIVsim uses the
ensemble mean of age at acquisition per year, computed by the
HIVCascadeAnalyzer.

Usage:
    python plot_fig2_replica.py
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from utils import set_font

set_font(size=13)

REPO = Path(__file__).resolve().parent
OUT = REPO / 'outputs' / 'zimbabwe_validation.parquet'
FIG_DIR = REPO / 'figures'
DIGITISED_CSV = REPO / 'reference' / 'paper_b_fig2_zimbabwe_digitised.csv'
FIG_DIR.mkdir(exist_ok=True)

MODEL_COLORS = {
    'Optima':    '#2b8ea1',
    'Synthesis': '#e2b64e',
    'PopART':    '#3e8f57',
    'Goals':     '#8b6ba1',
}
HIVSIM_COLOR = '#c44e52'
LINESTYLE = {'male': '-', 'female': '--'}


def hivsim_age_summary(df):
    """Compute HIVsim mean age at acquisition per year, by sex.

    Groups across draws x seeds: sum ages numerator, sum counts denominator,
    take ratio -> per-draw-sim mean. Ensemble summarised as median + 5-95th.
    """
    d = df.copy()
    d['mean_age_f'] = np.where(d.n_new_inf_f_per_year > 0,
                               d.age_sum_new_inf_f_per_year / d.n_new_inf_f_per_year,
                               np.nan)
    d['mean_age_m'] = np.where(d.n_new_inf_m_per_year > 0,
                               d.age_sum_new_inf_m_per_year / d.n_new_inf_m_per_year,
                               np.nan)
    out = {}
    for sex, col in [('female', 'mean_age_f'), ('male', 'mean_age_m')]:
        g = d.groupby('year')[col]
        out[sex] = pd.DataFrame({
            'median': g.median(),
            'p05':    g.quantile(0.05),
            'p95':    g.quantile(0.95),
        }).reset_index()
    return out


def main():
    df = pd.read_parquet(OUT)
    dig = pd.read_csv(DIGITISED_CSV, comment='#')

    fig, ax = plt.subplots(figsize=(10, 5))

    for model in ['Optima', 'Synthesis', 'PopART', 'Goals']:
        for sex in ['male', 'female']:
            m = dig[(dig.model == model) & (dig.sex == sex)].sort_values('year')
            if len(m):
                ax.plot(m.year, m.value, color=MODEL_COLORS[model],
                        lw=1.6, ls=LINESTYLE[sex], marker='o', ms=4,
                        label=f'{model} ({sex})', alpha=0.85)

    hivsim = hivsim_age_summary(df)
    for sex, s in hivsim.items():
        s = s.dropna(subset=['median'])
        s = s[(s.year >= 2000) & (s.year <= 2040)]
        ax.fill_between(s.year, s.p05, s.p95, color=HIVSIM_COLOR, alpha=0.20)
        ax.plot(s.year, s['median'], color=HIVSIM_COLOR, lw=2.6,
                ls=LINESTYLE[sex], label=f'HIVsim ({sex})')

    ax.set_xlim(2000, 2040)
    ax.set_ylim(22, 47)
    ax.set_xlabel('Year', fontsize=12)
    ax.set_ylabel('Mean age at HIV acquisition (years)', fontsize=12)
    ax.tick_params(labelsize=11)
    ax.grid(alpha=0.25)
    ax.legend(loc='center left', bbox_to_anchor=(1.01, 0.5), fontsize=10,
              frameon=False)
    fig.tight_layout()

    out = FIG_DIR / 'fig2_replica_zim.png'
    fig.savefig(out, dpi=140, bbox_inches='tight')
    print(f'wrote {out}')


if __name__ == '__main__':
    main()
