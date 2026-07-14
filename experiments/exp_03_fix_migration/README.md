# Exp 03 — Pin `rel_migration` at a point value

**Question.** [exp_02](../exp_02_wider_migration_higher_beta/SUMMARY.md)
found that `migration.rel_migration` doesn't behave as a useful
calibration lever: sweeping [0.2, 1.2] under a 7-prior LHS produced
near-zero correlation with 2020 `n_alive`, because HIV-mortality
variance across the β prior swamps the migration effect. What
single value of `rel_migration` (all other model parameters held
fixed at reasonable point values) makes the sim's `n_alive`
trajectory track UNAIDS most closely — and does the answer suggest
we should be using the migration data as-is (rel_migration = 1.0),
scaling down (< 1.0, less emigration), or scaling up (> 1.0)?

**Plan.**
- Fix all 6 non-migration priors at their **prior medians** so
  migration is the only thing varying:

  | prior | value |
  |---|---:|
  | `hiv.beta_m2f` | 0.0225 (midpoint of [0.005, 0.04]) |
  | `hiv.rel_init_prev` | 0.9 (midpoint of [0.3, 1.5]) |
  | `hiv.dur_on_art` | 6 (midpoint of [2, 10]) |
  | `structuredsexual.prop_f0` | 0.725 (midpoint of [0.55, 0.90]) |
  | `structuredsexual.m2_conc` | 5.0 (midpoint of [2.0, 8.0]) |
  | `structuredsexual.dur_sw` | 8.5 (midpoint of [2, 15]) |

- Scan `rel_migration ∈ {0.5, 1.0, 1.5}` (three point values; the
  user asked for 0.5 and 1.5 to bracket; 1.0 = "use the data as-is"
  makes a clean reference).
- Run K = 5 seeds per value at 10 000 agents, 1985–2040 — averages
  out stochastic variance so we can read the migration signal cleanly.
- Extract annual `n_alive` from each sim; plot the three
  rel_migration curves side-by-side against UN WPP totals.

**Success criteria.** One of the three values (or an interpolation
between two) lands the sim's 2020 `n_alive` inside [15.0, 16.0] M
(target 15.67 M ± roughly 4%). If none of them do, expand the scan
or diagnose a structural issue in the migration application. If
`rel_migration = 1.0` (data as-is) is the winner, that's the
simplest and most defensible choice.

**Motivation.** Two runs of prior-predictive coverage confirmed that
sweeping rel_migration inside a joint prior is wasted degrees of
freedom. Better to lock it at a single value backed by an isolated
sensitivity scan and calibrate the 6 remaining HIV / network
parameters against it.
