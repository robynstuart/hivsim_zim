# Exp 08 — Coverage check with `rel_death` and `rel_death_on_art` open

**Status.** Closed 2026-07-15.
**Setup.** 50 LHS × 1 seed × 10 000 agents × 1985-2040 on stisim
`feat/hiv-death-rate-pars@4517819`. 8 priors including two new
scalars (`hiv.rel_death` ∈ [0.5, 2.5], `hiv.rel_death_on_art` ∈ [0.1, 2.0]).
Aggressive condom schedule and `rel_migration = 0.5` fixed. ART driven
by `data/p_art.csv`. All 50/50 draws sustained.

## Answer to the question

**Partial pass.** Adding the two new death scalars to the ensemble
lifts `new_deaths` coverage from an exp_07 ceiling of ~0.16× UNAIDS
back into range at the 2000 peak (**5-95 % envelope now brackets
UNAIDS**), but the ensemble still cannot reach the post-2005 tail
(2010–2020 targets sit above the 95th percentile at ~2.0–2.3× the
ensemble median).

## Coverage table (median / target ratio; **bold** = target inside 5-95 % envelope)

| Metric | 1990 | 2000 | 2010 | 2015 | 2020 |
|---|---|---|---|---|---|
| HIV prev 15–49 | **0.95** | **0.89** | **1.15** | **1.25** | **1.31** |
| HIV prev F | **1.09** | **1.00** | **1.26** | **1.33** | **1.37** |
| HIV prev M | **0.79** | 0.77 | **1.03** | **1.17** | **1.23** |
| n_alive | 1.03 | **1.00** | **0.97** | **0.97** | **0.97** |
| PLHIV | **0.92** | **0.97** | **1.13** | **1.19** | **1.18** |
| new infections | 0.72 | **1.09** | **1.10** | **0.82** | **1.02** |
| **new deaths** | **0.17** | **0.88** | **0.43** | **0.44** | **0.43** |
| n_art | — | — | **1.30** | **1.25** | — |

(ART coverage panel is data-driven and reproduces `p_art.csv` almost
exactly by construction — small `p_on_art` "misses" are numerical only.)

## What changed vs exp_07

- **new_deaths at 2000**: 0.16× → **0.88×** (in-band).
- **new_deaths post-2005**: still ≤ 0.5× UNAIDS at 2010, 2015, 2020 —
  ensemble envelope caps around 45–55 % of the UNAIDS trajectory.
- HIV prevalence and PLHIV coverage retained (as required by the
  success criterion) despite the widened death priors.
- new_infections 1990 slipped slightly out of band (0.72×) — envelope
  tops at 0.83× UNAIDS.

## Why the post-2005 death tail still misses

Correlations of individual-draw `new_deaths` at 2015 with priors:

| prior | r |
|---|---|
| `hiv.beta_m2f` | +0.68 |
| `hiv.rel_death` | +0.36 |
| `hiv.rel_death_on_art` | +0.30 |
| `hiv.rel_init_prev` | +0.19 |
| `structuredsexual.prop_f0` | +0.20 |
| `hiv.dur_on_art` | −0.11 |

Post-2005 deaths correlate more strongly with **transmission** than
with the death scalars themselves. Draws that hit 2015 UNAIDS
(32 600) tend to combine **high β** (~0.03–0.037), **high
`rel_death`** (1.7–2.5), and **moderate `rel_death_on_art`** (0.8–2.0).
The ceiling looks like a joint envelope constraint (β vs prevalence)
rather than a death-mechanism ceiling — a full calibration should
close much of the remaining gap.

## Success-criteria scorecard

- ✅ **new_deaths coverable** at the 2000 peak (was the hard blocker).
- ⚠️ **new_deaths coverable** at 2010/2015/2020 — ensemble tail misses
  by ~2× median.
- ✅ **HIV prevalence / PLHIV / new_infections retain coverage** —
  none of the widened priors broke coverage on the metrics exp_07
  already had.
- ⚠️ **All targets covered** — 4/9 metric-year slots miss (mostly
  new_deaths post-2005).

## Next step

Move to the actual **Optuna calibration** via `sti.Calibration` with
these 8 priors. The joint calibration should be able to find the
β / `rel_death` / `rel_death_on_art` combinations the diffuse LHS
missed, and should close the remaining post-2005 `new_deaths` gap
without breaking the coverage exp_08 already retains.

## Artefacts

- `outputs/coverage_check.parquet` — per-(draw, year) ensemble.
- `outputs/coverage_draws.csv` — LHS draw table.
- `figures/coverage_check.png` — 3×3 diagnostic panel.
