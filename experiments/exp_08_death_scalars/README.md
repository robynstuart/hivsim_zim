# Exp 08 — Coverage check with `rel_death` and `rel_death_on_art` open

**Question.** [exp_07](../exp_07_dur_on_art_scan/SUMMARY.md) showed
`dur_on_art = 20 yr` almost closes the transmission gap
(2020 new_infections 1.14× UNAIDS), but `new_deaths` remains stuck
at 0.16× UNAIDS. The stisim `feat/hiv-death-rate-pars` branch exposes
two new tunables — `hiv.rel_death` (scales HIV deaths for all
infected) and `hiv.rel_death_on_art` (additional scale for on-ART
agents). Does adding these to the calibration priors let the ensemble
cover the UNAIDS AIDS-death trajectory, while keeping the other
metrics we've already got in the neighbourhood?

**Plan.**
- 50 LHS draws × 1 seed × 10 000 agents × 1985-2040.
- 8 priors:

  | prior | range | notes |
  |---|---|---|
  | `hiv.beta_m2f` | [0.005, 0.04] | unchanged |
  | `hiv.rel_init_prev` | [0.3, 1.5] | unchanged |
  | `hiv.dur_on_art` | **[8, 25]** | widened per exp_07 (was [2, 10]) |
  | `hiv.rel_death` | **[0.5, 2.5]** | new |
  | `hiv.rel_death_on_art` | **[0.1, 2.0]** | new |
  | `structuredsexual.prop_f0` | [0.55, 0.90] | unchanged |
  | `structuredsexual.m2_conc` | [2.0, 8.0] | unchanged |
  | `structuredsexual.dur_sw` | [2, 15] | unchanged |

- Aggressive condom schedule (exp_06 default). Fixed: `rel_migration = 0.5`,
  ART driven by `data/p_art.csv`.
- Runs on stisim branch `feat/hiv-death-rate-pars` (not yet merged).
- Same 3×3 diagnostic panel as exp_04/05.

**Success criteria.**
- **`new_deaths` becomes coverable.** UNAIDS target should sit inside
  the ensemble 5–95 % envelope at 1990, 2000, 2010, 2015, 2020.
- **`prev` / `PLHIV` / `new_infections` retain coverage.** Widened
  death rates could over-kill PLHIV, so we need to check that HIV
  metrics remain in-band.
- **All targets covered** in the ensemble envelope. If so, next
  experiment is the actual calibration (Optuna via sti.Calibration).

**Motivation.** All prior calibrations of this ensemble hit a
structural ceiling on `new_deaths` (~0.16× UNAIDS at 2020) because
on-ART agents were excluded from the stochastic HIV-death channel.
The stisim change (`feat/hiv-death-rate-pars`) puts them back in with
a scalable rate. This experiment validates that adding both scalars
to the calibration prior gives enough freedom to hit UNAIDS.
