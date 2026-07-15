# Exp 09 — Extended LHS + GoF ranking (top-10% ensemble)

**Goal.** Extend the exp_08 coverage check to N=500 LHS draws, rank
draws by weighted goodness-of-fit against UNAIDS multi-year targets,
and select the top ~10% (50 draws) as the ensemble used for
`run_zimbabwe_validation.py` and the paper's Figures 1-4.

**Setup.**
- 500 LHS × 1 seed × 10 000 agents × 1985-2040 on stisim
  `feat/hiv-death-rate-pars`.
- 8 priors (same as exp_08).
- `rel_migration = 0.5`, aggressive condoms locked; ART driven by
  `data/p_art.csv`.
- Result columns extended to include: HIV cascade analyzer outputs
  (`prop_diagnosed`, `prop_art_effective`, `n_alive_15_64`,
  age-of-infection sums, transmission-by-cascade-stage), SW-stratified
  new infections, and age-band prevalence (both sexes + sex-stratified).

**GoF metric.** Weighted RMSE of median vs UNAIDS at 1990, 1995,
2000, 2005, 2010, 2015, 2020 across:
- `hiv.prevalence_15_49`, `hiv.prevalence_f`, `hiv.prevalence_m`
- `hiv.n_infected`, `hiv.new_infections`, `hiv.new_deaths`

Residuals are normalized per-metric by target value (relative error)
so each metric contributes equally.

**Outputs.**
- `outputs/lhs_coverage.parquet` — full 500-draw ensemble time series.
- `outputs/lhs_gof.csv` — per-draw GoF scores.
- `outputs/draws_top50.csv` — top-50 draws (input to
  `run_zimbabwe_validation.py`).
- `figures/coverage_check.png` — 3×3 diagnostic panel (all 500 draws).
- `figures/coverage_top50.png` — same diagnostic panel restricted to
  the top-50.
