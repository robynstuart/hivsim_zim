# Suggested additional figures for the preprint

Beyond the five figures already committed in `figures/`, several
additional figures could strengthen the methods section of the preprint.
Listed in priority order.

## Priority 1 (recommend including)

### F-M1: HIV natural history state diagram
A boxes-and-arrows schematic of the HIV disease states in stisim's HIV
module. States: susceptible → acute (CD4 800→500, ~2.9 months) → latent
(CD4 500→200, ~10 years) → falling (CD4 200→0, ~3 years) → death.
Overlay treatment arrows: acute/latent/falling → on_art (CD4 rebounds
per logistic function) → post_art (linear decline). Include the ART
efficacy ramp and death routes.

Purpose: makes the natural-history parameterisation legible at a glance,
which the current write-up carries in prose only.

Implementation: matplotlib patches + arrows, or draw.io / TikZ. ~1 day.

### F-M2: Sexual network schematic
Three-panel diagram showing:
1. Risk levels L0 / L1 / L2 with prop_f0, prop_f2 annotations.
2. Concurrency preferences per level (f1_conc, m1_conc, m2_conc).
3. FSW / client overlay: 5% of women × ~4-year duration.

Purpose: makes the network structure section (§2.2) legible.

Implementation: hand-drawn or draw.io. ~0.5 day.

### F-M3: Calibration diagnostic — draws vs targets
A single figure showing all 30 sustaining draws' HIV whole-pop
prevalence trajectory (thin lines) overlaid on the UNAIDS 15-49
data (dots). Colour-code draws by their `hiv.beta_m2f` quintile so
the reader can see how the parameter maps to trajectory shape.

Purpose: transparency on ensemble spread; helps reader judge whether
the 5-95th percentile band in Fig 1 is well-supported or dominated by
outliers.

Implementation: 30-line spaghetti plot, colour = beta_m2f quintile.
~0.5 day.

## Priority 2 (nice-to-have)

### F-M4: Sex-stratified HIV prevalence
Adult HIV prevalence 15-49 split by sex, 1990-2040. HIVsim ensemble
median + band for males and females separately. Overlay ZIMPHIA 2015-16
and 2020 point estimates (women 16.7%, men 10.4% in 2016; women 14.9%,
men 10.3% in 2020 per PHIA Zimbabwe).

Purpose: validates that HIVsim captures the well-known
women-higher-than-men gradient in Zimbabwe.

Implementation: aggregate `prevalence_f` and `prevalence_m` from the
per-band results already exported by stisim; ~2 hours.

### F-M5: Age-stratified prevalence snapshot
Bar chart of HIV prevalence in 5-year age bins (15-19, 20-24, ...,
50-64), by sex, at 2015 and 2020, HIVsim vs ZIMPHIA/PHIA. Shows
whether the age gradient of HIV in the model matches surveillance
data.

Purpose: another dimension of validation. ZIMPHIA reports age-specific
prevalence for both years.

Implementation: sum `n_infected_{f,m}_{band}` / `n_alive_{f,m}_{band}`
(need to add n_alive by band to analyzer — small change). ~half day.

### F-M6: HIV-STI co-infection prevalence
Companion to F-M4. Shows how much of the HIV+ population also has
syph / NG / CT / TV in the model, comparing to Zimbabwe co-infection
studies. Would use the joint model (not the HIV-only slim wrapper).

Purpose: motivates the multi-STI framing for readers who care about
the joint calibration lineage.

Implementation: requires running the full joint model rather than the
HIV-only slim; ~1-2 days incl. figure work.

## Priority 3 (supplementary appendix material only)

### F-S1: Parameter posterior distribution box plots
For each of the 5 HIV-relevant priors (`hiv.beta_m2f`,
`hiv.rel_init_prev`, `structuredsexual.prop_f0`, `structuredsexual.m2_conc`,
`structuredsexual.dur_sw`), show the prior range (grey box) with the
top-30 sustaining draws overplotted. Would show which parameters were
strongly constrained by calibration and which were not.

Implementation: from `calibration/artifacts/draws_sustaining_top30.csv`
+ `priors.py`; ~half day.

### F-S2: Cascade churn diagnostic
Time series of the fraction of PLHIV in each cascade state
(undiagnosed → diagnosed-not-on-ART → on-ART → post-ART) 1985-2040.
Complements Fig 3 (which shows transmission attribution) by showing
the stock-vs-flow picture.

Implementation: already have n_undiagnosed / n_diag_not_on_art / n_on_art_effective / n_post_art in the analyzer output; small plot. ~2 hours.

### F-S3: Model runtime + ensemble-size sensitivity
For internal reviewer confidence. Time-per-sim vs n_agents (5k, 10k,
20k), 5-95th percentile band width vs K (1, 3, 5, 10). Confirms that
K=3 seeds x 30 draws gives stable central estimates.

Implementation: a few extra runs; ~half day.
