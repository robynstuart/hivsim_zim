# Exp 07 — Point-value scan of `hiv.dur_on_art`

**Question.** [exp_06](../exp_06_condom_scale_up/SUMMARY.md)'s
post-experiment diagnostic showed **21-29% of PLHIV in 2010-2015 are
in the `post_art` state** because stisim's default `dur_on_art =
LogN(mean=3 yr)` produces high treatment churn — people cycle off ART
and transmit at 100% until they either die or get re-enrolled by the
coverage target. Real Zimbabwe ART retention is much higher (85% at
3 yr, 70% at 5 yr, 55% at 10 yr). How much of the residual PLHIV +
new_infections overshoot does treatment churn account for?

**Plan.**
- Point-value scan at `hiv.dur_on_art ∈ {3, 10, 20}` years (mean of
  LogN distribution). 3 = stisim default; 10 = current prior upper;
  20 ≈ lifetime retention.
- Other priors fixed at midpoints (same as [exp_03](../exp_03_fix_migration/README.md)):
  - `hiv.beta_m2f = 0.0225` (midpoint of [0.005, 0.04])
  - `hiv.rel_init_prev = 0.9`
  - `structuredsexual.prop_f0 = 0.725`
  - `structuredsexual.m2_conc = 5.0`
  - `structuredsexual.dur_sw = 8.5`
- Condom schedule: **aggressive** (locked-in default from
  [exp_06](../exp_06_condom_scale_up/SUMMARY.md)). Actually — this
  hasn't been made the default in `data/condom_use.csv` yet. Runner
  will construct the aggressive schedule inline (using the same
  logic as exp_06) so the scan is independent of any future
  data-file change.
- K = 5 seeds per value × 3 values = 15 sims.

**Success criteria.**
- **Post-ART fraction of PLHIV collapses** as `dur_on_art` climbs.
  At 3 yr we saw ~29% post-ART in 2010-2015; at 20 yr the number
  should drop to single digits.
- **New infections come down** as more PLHIV stay in the transmitting-
  at-4% on-ART state instead of transmitting-at-100% post-ART.
- **PLHIV trajectory** — depends on how the churn-vs-death balance
  shifts. Longer ART = fewer post-ART deaths = potentially higher
  PLHIV; but longer ART also means less onward transmission, so
  fewer new infections. The net effect is empirical.
- **new_deaths** should DROP further with longer ART (fewer post-ART
  agents dying). That's the correct direction for reality (ART
  extends life) but pushes new_deaths further from the UNAIDS target.
  A signal that the missing-deaths problem is deeper than dur_on_art
  alone.

Adds an extra plot panel: per-scenario post-ART fraction of PLHIV
over time, so we can see the churn effect directly.

**Motivation.** Same pattern as [exp_03](../exp_03_fix_migration/SUMMARY.md)
— rather than sweep dur_on_art inside a joint LHS, isolate its effect
by holding everything else constant. Deciding whether to bake in a
point value (like `rel_migration = 0.5`) or open it up as a prior
depends on how strong / monotonic the effect is.
