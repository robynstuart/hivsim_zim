# HIVsim validation and model-comparison sprint: Zimbabwe

**A brief for the coding agent.** The goal is a 3-day sprint that turns our already-calibrated HIVsim Zimbabwe model into evidence that HIVsim is a scientifically credible, validated model, by reproducing the published results of two multi-model studies and drafting a preprint. Read this whole brief before starting, then work through the sprint plan in Section 6. Placeholders marked **[FILL]** need input from Robyn and are collected in Section 10.

---

## 1. Why we are doing this

For NYU to adopt HIVsim for policy-relevant decision-making and to build grant applications on it, HIVsim has to be demonstrably credible: it must reproduce results that the HIV modelling community already trusts.

The original plan was a bespoke, pairwise comparison between EMOD-HIV and HIVsim. That plan has a problem. The two models were written at different points of the epidemic, were designed to answer different questions, and structurally differ in ways that make a like-for-like metric list genuinely unclear. For example, they do not model ART prioritisation the same way, and nor should they. Forcing false equivalence on such metrics would be misleading.

**The pivot:** rather than invent comparability metrics ourselves, we reproduce the outputs of two published studies that the community has already standardised on. Crucially, EMOD-HIV is one of the models in Paper A, so reproducing Paper A places HIVsim directly alongside EMOD-HIV and four other established models on agreed indicators. This is a stronger and faster route to credibility than a pairwise comparison, and both target papers already have NYU co-authors.

---

## 2. Objective

Within 3 days:

1. Reproduce the key published Zimbabwe results from the two papers below using the calibrated HIVsim Zimbabwe model.
2. Produce comparison figures overlaying HIVsim on the published multi-model results, plus a short comparability assessment.
3. Draft a preprint describing the model, the comparison, and the status-quo projection.

---

## 3. Target papers and what to reproduce

### Paper A: five-model Zimbabwe projections
- Taramusi et al. (2025), *HIV incidence and prevalence projections for Zimbabwe: findings from five mathematical models*, African Journal of AIDS Research. DOI `10.2989/16085906.2025.2518936`.
- Open-access manuscript via UCL Discovery: `https://discovery.ucl.ac.uk/id/eprint/10213175/`.
- Design: five independent models (EMOD-HIV, Goals, HIV Synthesis, Optima, PopART-IBM) calibrated to Ministry of Health datapoints, run under a **status-quo scenario** (interventions continue at current levels), producing indicators for **1990 to 2040**.
- **Reproduce for Zimbabwe, status quo, 1990 to 2040:**
  - HIV prevalence (adults 15 to 49)
  - HIV incidence (adults 15 to 49)
  - New infections per year (count). Benchmark: all five models projected a continuous decline and reaching fewer than 7,800 new infections per year by 2025.
  - People living with HIV (total)
  - ART coverage and/or number on ART
  - AIDS-related deaths
  - Disaggregate by sex and age band where the paper does.
- Deliverable: HIVsim added as an additional trajectory on the same axes as the five-model ensemble, so we can see whether HIVsim falls within the published range.

### Paper B: treatment-cascade gaps (MIHPSA)
- Bansi-Matharu et al. (2025), *Identifying gaps in the HIV treatment cascade in Africa: a model comparison study*, Lancet Global Health 13(6):e1006 to e1019. DOI `10.1016/S2214-109X(25)00121-4`.
- Open-access on PMC (CC BY 4.0): `https://pmc.ncbi.nlm.nih.gov/articles/PMC12500161/`. Pull the appendix for the underlying numbers where available.
- Design: model comparison across Malawi, Zimbabwe and South Africa (the MIHPSA project) asking **where along the treatment cascade ongoing HIV transmissions originate.**
- **Reproduce for Zimbabwe:**
  - The 95-95-95 treatment cascade over time (proportion diagnosed, proportion of diagnosed on ART, proportion on ART virally suppressed).
  - The distribution of ongoing transmission by the source's cascade position (for example: undiagnosed, diagnosed but not on ART, on ART but not virally suppressed).
  - Any risk-group or age or sex disaggregation the paper uses for Zimbabwe.

---

## 4. Scope and non-goals

**In scope:** Zimbabwe only (this is where we have a calibrated model); the status-quo scenario; the specific indicators listed in Section 3.

**Out of scope for this 3-day sprint:**
- eSwatini. Adam and Daniel are calibrating eSwatini separately; this is the longer-term extension, not part of the sprint.
- Re-deriving structural equivalence between models (for example, matching ART prioritisation logic). We do not do this.
- A full probabilistic sensitivity analysis or recalibration. Use the existing calibration.

**Comparability principle (important):** compare only on the standardised output indicators the published studies use. Where the models differ structurally (ART prioritisation, key-population structure, and so on), record the difference as expected and appropriate rather than forcing equivalence. Capture this in the comparability matrix (Section 7).

---

## 5. Technical setup

- Stack: HIVsim on the Starsim framework, Python. Use internal calibration tooling (Optuna or Starsim calibration) only if a re-run is needed; the default is to load the existing calibrated Zimbabwe configuration.
- Repo and calibrated model location: **[FILL: repo URL and path to the calibrated Zimbabwe model and calibration artifacts]**.
- Reproducibility: fix random seeds, run enough stochastic realisations to give stable central estimates and an uncertainty band, log the exact config, and commit a single `run_zimbabwe_validation.py` entry point plus a notebook that regenerates every figure from saved outputs.
- Output structure (suggested):
  ```
  zimbabwe_validation/
    config/            # scenario + calibration config, seeds
    run/               # run scripts, entry point
    outputs/           # raw simulated indicator time series (csv)
    reference/         # digitised / appendix data from Papers A and B
    figures/           # comparison figures
    preprint/          # draft manuscript + figure captions
    comparability.md   # the comparability matrix
  ```
- Reference data: where the papers do not ship machine-readable data, digitise the published curves (for example with WebPlotDigitizer) into `reference/` and note provenance. Paper B's appendix on PMC is the first place to look for Zimbabwe cascade numbers.
- Indicator harmonisation: match the papers' age ranges (commonly 15 to 49 for prevalence and incidence), denominators, units (prevalence as percent, incidence per person-year or per 1000, new infections as annual counts), and calendar-year alignment. Get these exactly right before plotting; most apparent disagreements are unit or denominator mismatches.

---

## 6. Sprint plan

### Day 0 (immediately, a few hours)
- Clone the repo, install, and confirm the calibrated Zimbabwe model loads and runs end to end.
- Confirm the calibration targets match the Ministry of Health datapoints used in Paper A (or note differences).
- Retrieve reference data from both papers into `reference/`.

### Day 1: reproduce Paper A projections
- Configure the status-quo scenario, 1990 to 2040.
- Run and extract the Section 3 Paper A indicators as annual time series to `outputs/`.
- Build overlay figures: HIVsim trajectory on the same axes as the five-model ensemble, for prevalence, incidence, new infections, PLHIV, ART coverage, and AIDS deaths.
- Sanity checks: continuous decline in incidence and prevalence; new infections trending below 7,800 per year around 2025. Flag and explain any indicator where HIVsim sits outside the published range.

### Day 2: reproduce Paper B cascade and transmission sources
- Produce the 95-95-95 cascade over time for Zimbabwe.
- Produce the distribution of ongoing transmission by source cascade stage, matching the paper's stage definitions.
- Build the comparison figures against Paper B's Zimbabwe results.
- Fill in the comparability matrix (Section 7).
- If Adam's EMOD-HIV comparison artifacts are available, fold them in as an additional comparator or supplementary check. **[FILL: Adam's EMOD progress and artifacts]**.

### Day 3: draft the preprint
- Assemble the manuscript per the outline in Section 8, dropping in the Day 1 and Day 2 figures with captions.
- Write the methods and the comparability discussion (including the ART-prioritisation example as the illustration of appropriate structural difference).
- Produce a clean, reproducible figure notebook and a short README for reviewers.
- Hand back for internal review by Robyn, Adam and Daniel.

---

## 7. Comparability matrix

Produce `comparability.md` as a table with one row per indicator:

| Indicator | Source paper | Directly comparable? | HIVsim vs published (2025 / 2030 / 2040) | Notes on structural differences |
|---|---|---|---|---|

Use it to state plainly which indicators are like-for-like, which are only broadly comparable, and which differ by design (and why that is appropriate). This matrix is a core scientific output, not an afterthought.

---

## 8. Preprint outline

1. **Title and abstract.** Framing: validating HIVsim against published multi-model Zimbabwe results.
2. **Introduction.** The need for a validated, credible HIVsim for policy use and grants; why reproducing agreed indicators from existing multi-model studies is preferable to a bespoke pairwise comparison.
3. **Methods.** HIVsim and Starsim; the Zimbabwe calibration and its targets; the status-quo scenario; the two reproduction exercises; indicator harmonisation; and an explicit statement of the comparability principle (compare on standardised outputs, not on structure).
4. **Results.** (a) Status-quo projections 1990 to 2040 versus the five-model ensemble; (b) treatment cascade and transmission-by-stage versus the MIHPSA comparison; (c) the comparability matrix.
5. **Discussion.** What HIVsim reproduces well; where and why it differs; the ART-prioritisation example as an instance of appropriate divergence; limitations; implications for NYU adoption and next steps (eSwatini).
6. **Contributions and authorship.** **[FILL: author list and order]**.

---

## 9. Definition of done

- Every Section 3 indicator reproduced for Zimbabwe and plotted against the published results.
- `comparability.md` complete.
- A reproducible entry point plus notebook that regenerates all figures from saved outputs.
- A preprint draft with methods, results, figures and discussion, ready for internal review.

---

## 10. Inputs needed from Robyn

- **[FILL]** Repo URL and path to the calibrated Zimbabwe model and calibration artifacts.
- **[FILL]** Adam's EMOD-HIV comparison progress and any artifacts to fold in.
- **[FILL]** The exact figures or panels from each paper to target first (if we want to prioritise a subset given the 3-day window).
- **[FILL]** Author list and target preprint server (for example medRxiv).
- **[FILL]** Confirmation that the current calibration targets align with the Ministry of Health datapoints used in Paper A.

---

## 11. Longer term (not this sprint)

- eSwatini calibration and the same validation exercise there (Adam and Daniel).
- Extending the comparison set and, if useful, a fuller structured comparison once the indicator-level validation is established.
