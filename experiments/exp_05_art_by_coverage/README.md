# Exp 05 — Switch ART intervention from absolute n_art to coverage p_art

**Question.** [Exp 04](../exp_04_coverage_after_migration_fix/SUMMARY.md)
showed the sim's HIV epidemic runs 2–4× hot through the ART scale-up
window: `n_on_art` matches the forced UNAIDS `n_art` schedule but
PLHIV keeps climbing because the sim's inflated PLHIV means fewer
people (proportionally) are on treatment than in reality. Switching
the ART intervention from **absolute enrollment** (`n_art`) to
**coverage-based** enrollment (`p_art` = fraction of PLHIV on ART)
gives the sim a self-correcting feedback loop: if PLHIV is inflated,
the same coverage target enrolls more people, blocking more
transmission and bending PLHIV back down. Does this switch bring the
median trajectory into UNAIDS's neighbourhood on prev + PLHIV +
new_infections?

**Plan.**
- Compute historical `p_art` from UNAIDS: `n_art / hiv.n_infected`
  where both are available (2003–2019). Continue with a smooth
  ramp 2020 = 0.85, 2021 = 0.87, 2022 = 0.90, 2023 = 0.92, 2024 = 0.94,
  2025+ = 0.95 (matches where the historical series ends; no jump).
- Write to `data/p_art.csv`; update `hiv_model.py::make_hiv_intvs`
  to pass this via `sti.ART(coverage=p_art)`. sti's `parse_coverage`
  detects the `p_art` column and switches to coverage-target mode.
- Rerun the exp_04 3×3 coverage diagnostic (same 50 LHS draws, 6
  priors, `rel_migration = 0.5` fixed, same 9 result columns).

**Success criteria.**
- **PLHIV trajectory bends over** — climbs to a peak ~2000, plateaus
  through 2005, and starts falling as ART coverage crosses ~50%. If
  it keeps climbing, coverage-based enrollment isn't enough on its
  own and β_m2f still needs to come down.
- **New infections show ART's transmission-blocking effect** —
  the 2010→2015 gradient should be much steeper than in exp_04
  (where new_infections stayed flat/rising through the scale-up
  window despite 10× more people on ART).
- **ART coverage panel tracks UNAIDS** — sim `hiv.p_on_art` should
  now be an input, not a diagnostic. Verifies the coverage-target
  mode is working.
- Coverage of the UNAIDS envelope on prev + PLHIV improves in the
  2010–2020 window relative to exp_04.

**Motivation.** The exp_04 diagnosis was that ART enrollment was
happening but not enough of PLHIV was being treated (because PLHIV
was inflated). Coverage-based enrollment is the mechanism-level fix
for that: the sim now targets a *fraction* rather than an *absolute*
count, so ART scales with PLHIV. Whether this alone closes the gap
or the sim still needs a tighter β prior is the empirical question.
