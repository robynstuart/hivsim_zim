# Exp 02 — Wider migration bound + slightly higher beta upper

**Question.** Following [exp_01_initial](../exp_01_initial/SUMMARY.md),
does widening `migration.rel_migration` below 0.5 and lifting the upper
`hiv.beta_m2f` bound close the two marginal coverage misses:

- 2020 `n_alive` (target 15.67 M, exp_01 ensemble p95 14.80 M — 6% low)
- 1990 `hiv.new_infections` (target 283 k, exp_01 p95 238 k — small)
- 2000 `hiv.prevalence_m` (target 23%, exp_01 p95 20% — marginal)

**Plan.**
- Same 50 LHS × 1 seed × 10 000 agents × 1985–2040 protocol as exp_01.
- Same 7 priors, but with two bounds changed:

  | prior | exp_01 | exp_02 |
  |---|---|---|
  | `migration.rel_migration` | [0.5, 1.2] | **[0.2, 1.2]** |
  | `hiv.beta_m2f` | [0.005, 0.03] | **[0.005, 0.04]** |

  All five other priors unchanged (`hiv.rel_init_prev`, `hiv.dur_on_art`,
  `structuredsexual.prop_f0`, `m2_conc`, `dur_sw`).
- Same 2025 UNAIDS target CSV, same 8 result columns.
- Same runner (`run.py` mirrors exp_01, updated to point at
  `exp_02/outputs/` and `figures/`).

**Success criteria.**
- 2020 `n_alive` target sits inside the ensemble p05-p95 band.
- 1990 `hiv.new_infections` and 2000 `hiv.prevalence_m` targets inside
  band (or at worst, closer to p95 than in exp_01).
- No regression on the metrics that already covered cleanly in exp_01
  (PLHIV, `prev_15_49`, `prev_f`).
- `hiv.new_deaths` remains uncovered — that's a structural note carried
  forward, not something this experiment tries to fix.

**Motivation.** exp_01's coverage check was clean on HIV concentration
but couldn't reach the endpoint total-population target from below.
This is exactly the kind of "prior is too narrow at one edge" failure
mode the coverage-check skill flags: widen the bound with justification
(here, that Zimbabwe's UN-WPP-derived migration table under-counts the
peak-emigration years, so `rel_migration < 0.5` is defensible). The
beta upper is lifted for the same reason: two marginal upper-edge
target misses call for a slightly hotter transmission ceiling.

After this experiment closes, if coverage passes, the next move is
the calibration itself — deciding between `sti.Calibration` + Optuna
and an LHS + K-seed ensemble (deferred at exp_01 close, will revisit
here).
