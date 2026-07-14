# Exp 01 — Prior-predictive coverage check on the fresh hivsim_zim setup

**Question.** After moving hivsim_zim onto starsim main + stisim 1.5.10
(both freshly rebuilt in a new `hivsim` conda env), and adding two new
priors (`hiv.dur_on_art`, `migration.rel_migration`), does the prior
predictive envelope bracket the UNAIDS 2025 Zimbabwe surveillance series
— including whole-population `n_alive` as a new target? This is a
coverage check, not a calibration; it tests whether the *model + prior
+ observation model* can reach the data before spending compute on the
full recalibration.

**Plan.**
- 50 Latin-Hypercube draws from `hivsim_zim/priors.py` (7 parameters:
  `hiv.beta_m2f`, `hiv.rel_init_prev`, `hiv.dur_on_art`,
  `migration.rel_migration`, `structuredsexual.prop_f0`, `m2_conc`,
  `dur_sw`).
- One seed per draw at 10 000 agents, 1985–2040.
- Compare against the reshaped `data/zimbabwe_hiv_calib.csv`
  (UNAIDS 2025 vintage, dot-notation columns, `n_alive` derived from
  PLHIV / prev, plus sex-stratified prevalence).
- Repeat the check with `use_migration=False` as a sanity baseline.

**Success criteria.**
- Every UNAIDS target point should sit inside the prior 5-95% envelope.
- If any target sits outside, diagnose whether it's a prior width
  problem, a model structure problem, or an observation model problem
  (per the coverage-check skill's three-way split).

**Motivation.** No previous experiment; this is the entry point for the
recalibration prompted by the observation that HIVsim's pre-migration
runs overshoot Zimbabwe's population by ~20% by 2020, which throws off
PLHIV and ART-coverage denominators. The 2025 UNAIDS CSV is a fresh
vintage that supersedes the previous mixed-vintage target CSV; adding
`migration.rel_migration` gives the recalibration a lever to move the
population trajectory.
