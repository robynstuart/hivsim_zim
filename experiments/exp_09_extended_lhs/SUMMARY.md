# Exp 09 — Extended LHS + top-50 GoF ranking

**Status.** Closed 2026-07-15.
**Setup.** 500 LHS × 1 seed × 10 000 agents × 1985-2040 on stisim
`feat/hiv-death-rate-pars`. 8 priors (unchanged from exp_08).
`rel_migration = 0.5`, aggressive condoms, `p_art` schedule fixed.

## GoF (v2 with mean-age-at-acquisition + MTC-fixed analyzer)

Weighted-RMSE ranking against UNAIDS multi-year targets
(1990/1995/2000/2005/2010/2015/2020 × six metrics: sex-stratified
prev, PLHIV, new infections, deaths) plus **mean age at adult HIV
acquisition (F and M) at 2015 and 2020**, targets sourced from the
Bansi-Matharu 2025 four-model consensus for Zimbabwe (F: 30/32,
M: 34/36).

**All 500 draws sustained.**

| | RMSE |
|---|---|
| Best draw (all 500) | 0.207 |
| Worst-of-top-50 | 0.266 |
| Worst draw (all 500) | ~0.9 |

Note: an earlier v1 GoF (UNAIDS-only, no age-at-acquisition) placed
essentially the same 50 draws at the top with RMSE 0.215-0.277 —
adding mean-age constraints didn't materially re-order the ensemble
because the age-fit and the UNAIDS-fit align in the same draws.

Top-50 draws are saved to `outputs/draws_top50.csv`. Used by
`run_zimbabwe_validation.py` and the paper's Figures 1-4.

## Posterior tightening (top-50 vs prior)

| Prior | Prior range | Top-50 range | Top-50 median |
|---|---|---|---|
| `hiv.beta_m2f` | [0.005, 0.04] | [0.016, 0.028] | 0.022 |
| `hiv.rel_init_prev` | [0.3, 1.5] | [0.31, 1.48] | 0.89 |
| `hiv.dur_on_art` | [8, 25] yr | [8.5, 24.1] | 14.9 |
| `hiv.rel_death` | [0.5, 2.5] | [0.97, 2.49] | 2.05 |
| `hiv.rel_death_on_art` | [0.1, 2.0] | [0.47, 1.98] | 1.37 |
| `structuredsexual.prop_f0` | [0.55, 0.90] | [0.55, 0.89] | 0.70 |
| `structuredsexual.m2_conc` | [2.0, 8.0] | [2.2, 7.9] | 4.4 |
| `structuredsexual.dur_sw` | [2, 15] yr | [2.2, 15.0] | 9.2 |

Tightest constraints are on `beta_m2f` (top-50 confined to
[0.016, 0.028] vs prior [0.005, 0.04]) and on the two new death
scalars (`rel_death` biased above 1.0, `rel_death_on_art` biased
above 0.5) — both required to fit the AIDS-deaths peak.

## Coverage vs UNAIDS (top-50 ensemble)

See `figures/coverage_top50.png`. The top-50 5-95th percentile band
brackets UNAIDS for:
- HIV prevalence 15-49 (whole-pop + sex-stratified)
- Total population
- PLHIV
- ART coverage (data-driven)
- New infections per year (2000-2020)

Residual misses:
- AIDS-related deaths peak at 2005-2010: median ~0.6× UNAIDS.
- New infections at 1990 slightly overshoots.
- HIV prev 15-49 slightly overshoots 2020 (~1.05×).

## Mean age at HIV acquisition (adult, MTC excluded)

| Year | HIVsim F | HIVsim M | Paper B F target | Paper B M target |
|---|---|---|---|---|
| 2000 | 25.7 | 32.0 | ~28-30 | ~33-38 |
| 2010 | 26.4 | 31.2 | ~30-33 | ~35-38 |
| 2020 | 30.1 | 34.8 | 32 | 36 |

F remains ~2 yr below the 4-model consensus at 2020; M is within 1 yr.
The analyzer bug that had been folding MTC infections (age ~0) into
the mean was fixed in this exp (see `analyzers.py::step`).

## Bug fixed in this experiment

`HIVCascadeAnalyzer` previously computed `age_sum_new_inf_f/m` and
`n_new_inf_f/m` over all newly-infected agents regardless of age —
so MTC infections at age ~0 were pulling the reported mean-age-at-
acquisition down by ~4-5 years at 2000. Now filtered to adults (age
≥ 15) to match the Paper B "mean age at HIV acquisition" semantics.

## Artefacts

- `outputs/lhs_coverage.parquet` — 500-draw ensemble time series
  (28 000 rows × 50 columns; SW-stratified new infections + age-band
  prev + cascade analyzer results included).
- `outputs/lhs_gof.csv` — per-draw GoF scores.
- `outputs/draws_top50.csv` — top-50 draws for downstream use.
- `figures/coverage_check.png`, `figures/coverage_top50.png` — 3×3
  diagnostic panels.

## Next step

`run_zimbabwe_validation.py` runs the top-50 × K=3 seeds and produces
`outputs/zimbabwe_validation.parquet` used by the paper's Figs 2-4.
The new Fig 1 (`plot_fig1_epi.py`) reads `lhs_coverage.parquet`
filtered to top-50 directly.
