# hivsim_zim

HIVsim Zimbabwe: a calibrated HIV model on the Starsim / STIsim stack, used to
reproduce published Zimbabwe results from two multi-model comparison studies
and to draft a validation preprint. See `ANALYSIS_PLAN.md` for the sprint brief.

## What's in the repo

- `model.py` — HIV-only Zimbabwe sim (HIV disease + structured sexual network +
  Zimbabwe demographics), 1985–2040. Slim wrapper around stisim's `sti.HIV` and
  `sti.StructuredSexual`.
- `hiv_model.py` — HIV disease module + interventions (testing programs, ART,
  VMMC, PrEP) with time-varying coverage from `data/n_art.csv`,
  `data/n_vmmc.csv`.
- `priors.py` — HIV-relevant calibration priors (`hiv.beta_m2f`,
  `hiv.rel_init_prev`, network shape).
- `data/` — Zimbabwe HIV surveillance (`zimbabwe_hiv_calib.csv`), initial
  prevalence, ART / VMMC coverage, demographics (age structure, ASFR, deaths,
  migration, condom use).
- `calibration/artifacts/` — 500-draw LHS × K=5 sim-averaging calibration
  outputs from the `sti_notification` project (experiment 06, 2026-06-24).
  Includes the top-10 draws by GoF (`draws_top10.csv`), the full 500-draw
  prior sample (`priors_500.csv`), per-draw calibration metrics
  (`per_draw_means_wholepop.csv`), and the calibration write-up
  (`CALIBRATION_SUMMARY.md`).
- `reference/` — digitised / appendix data from the target papers (populated
  during the sprint).
- `outputs/` — simulated indicator time series (gitignored).
- `figures/` — comparison figures (gitignored).

## Provenance

The calibrated model is lifted from
[sti_notification](../sti_notification/) (private, IDM), where HIV was
calibrated jointly with syphilis + NG/CT/TV/BV against Zimbabwe MoH and
ZIMPHIA data. The joint HIV–syph coupling in that fit is
`hiv → syph` (HIV+ agents are more susceptible to syph), not the
reverse, so dropping the STIs here does not materially perturb the HIV
trajectory. The calibration itself ran on stisim `fix/ng-tx@731bc1d`.

## Quick start

```bash
pip install -r requirements.txt
python model.py                # smoke test: 1985-1990, 1k agents
```

To load a calibrated draw and run to 2040:

```python
import pandas as pd
from model import make_sim

draws = pd.read_csv('calibration/artifacts/draws_top10.csv')
row = draws.iloc[0]

# The draws CSV stores several parameters on a log10 scale (columns
# prefixed `log_`). Only the HIV + network columns matter for HIV-only.
calib_pars = {
    'hiv.beta_m2f':             row['hiv.beta_m2f'],
    'hiv.rel_init_prev':        row['hiv.rel_init_prev'],
    'structuredsexual.prop_f0': row['structuredsexual.prop_f0'],
    'structuredsexual.m2_conc': row['structuredsexual.m2_conc'],
    'structuredsexual.dur_sw':  row['structuredsexual.dur_sw'],
}

sim = make_sim(seed=1, start=1985, stop=2040, n_agents=10_000,
               calib_pars=calib_pars)
sim.run()
```

## Environment

Conda env `starsim`. `stisim>=1.5.5`, `starsim>=3.3.2`. Single-sim runtime at
10k agents, 1985–2040: ~60 s (HIV-only, no STI co-infection dynamics).
