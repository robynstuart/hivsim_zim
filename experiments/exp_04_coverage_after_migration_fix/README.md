# Exp 04 — ART scale-up dynamics after fixing migration

**Question.** In exp_03's PLHIV panel the sim's PLHIV keeps climbing
right through the mid-2000s, whereas UNAIDS shows PLHIV plateauing
around 2000 and starting to fall by 2005 — exactly when Zimbabwe's
ART program scaled up. So: with population now correct (rel_migration
locked at 0.5), does the sim actually reproduce the ART scale-up in
the mid-2000s, and does that scale-up bring new infections down as
it should? Or is HIV running open-loop in the 2005-2015 window?

**Plan.**
- 50 LHS draws × 1 seed × 10 000 agents × 1985-2040 on the 6 remaining
  HIV / network priors (all non-demographic):
  `hiv.beta_m2f ∈ [0.005, 0.04]`, `hiv.rel_init_prev ∈ [0.3, 1.5]`,
  `hiv.dur_on_art ∈ [2, 10]`, `structuredsexual.prop_f0 ∈ [0.55, 0.90]`,
  `structuredsexual.m2_conc ∈ [2.0, 8.0]`,
  `structuredsexual.dur_sw ∈ [2, 15]`.
- `rel_migration = 0.5` hardcoded in `model.py::make_sim`; not sampled.
- 3×3 envelope panel:

  | | col 1 | col 2 | col 3 |
  |---|---|---|---|
  | row 1 | HIV prev 15-49 | HIV prev female | HIV prev male |
  | row 2 | Total population | PLHIV | ART coverage (%) |
  | row 3 | New HIV infections/yr | AIDS-related deaths/yr | Number on ART |

  ART coverage panel: sim `hiv.p_on_art` vs UNAIDS `n_art / PLHIV`.
  Number on ART panel: sim `hiv.n_on_art` vs the forced `data/n_art.csv`
  targets. Comparing these two rules out a scale-up mechanism failure
  (if `n_on_art` matches the target file, low coverage is purely a
  PLHIV-denominator problem).

**Success criteria.**
- **ART scale-up mechanism is intact.** The sim's `n_on_art` (row 3
  col 3) should follow the forced targets in `data/n_art.csv` from
  ~2004 onward. If it lags, that's a mechanism failure that has to
  be fixed before calibration.
- **PLHIV trajectory response to ART.** With ART scaling up in 2005+,
  the sim's PLHIV should plateau by ~2005 and start dropping — mirroring
  UNAIDS. If PLHIV keeps rising through 2010, that says the epidemic
  is producing new infections faster than ART is preventing them or
  new_deaths are removing them.
- **New infections come down** in the 2005-2015 window as ART scale-up
  raises the treated fraction. A flat or rising `new_infections` after
  2005 signals prevention-of-transmission via ART isn't being felt.

**Motivation.** exp_03 fixed the population problem cleanly but left
a ~40% PLHIV overshoot at 2020. That overshoot could be:
(a) a single dial (β too high) inflating the whole trajectory, in which
    case a wide-β calibration will pull it into band without further
    surgery,
(b) an ART-response failure — infections should be dropping post-2005
    but aren't, leaving PLHIV to accumulate,
(c) a natural-history issue (people not dying / not clearing at the
    right rate).
The 3×3 plot is designed to tell these apart at a glance rather than
diagnosing after calibration fails.
