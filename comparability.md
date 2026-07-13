# Comparability matrix: HIVsim Zimbabwe vs published multi-model outputs

Draft. Rows filled in from the Day 1 (Paper A benchmarks) + Day 2 (Paper B
cascade + transmission) runs; the "HIVsim vs published" column will be
tightened once year-by-year traces from the Taramusi paper are digitised
into `reference/`. See `ANALYSIS_PLAN.md` §7 for the scoring convention.

## Paper A (Taramusi et al. 2025) — 5-model status-quo projections

| Indicator | Directly comparable? | HIVsim ensemble @ 2023 / 2040 | Published 5-model range | Notes on structural differences |
|---|---|---|---|---|
| HIV prevalence, 15-49 (%) | Yes | 2023 median 12.2 (5-95th: 2.5-19.7); 2040 median 4.2 (0.8-10.5) | 2023: 12.1-14.3; 2040: 3.9-6.0 | HIVsim ensemble brackets the published range for both benchmark years; median hits the lower bound in 2023 and inside the range in 2040. Wide 5-95th spread reflects keeping all 30 sustaining draws (not HIV-fit sub-selected). |
| HIV incidence, 15-49 (per 1000 py) | Yes | 2023 median 1.9 (5-95th: 0.1-6.3); 2040 median 1.1 (0.1-7.7) | 2023: 2.0-3.3; 2040: 1.0-3.0 | HIVsim 2023 median (1.9) just below the paper's lower bound (2.0); the ensemble spread easily brackets it. 2040 median in range. |
| New infections per year, all ages | Yes | 2025 median 20,010 (5-95th: 870-53,635) | <7,800/yr by 2025 (all 5 models) | HIVsim central tendency runs above the paper's benchmark. Real signal, not a bug: (a) the empirical ART supply curve caps ART enrolment at ~1.19M from 2020, so high-PLHIV draws leave excess PLHIV out of the ART numerator and generate higher onward transmission; (b) no PrEP scale-up modelled in status-quo beyond the historical curve. |
| People living with HIV (PLHIV), all ages | Yes | 2023 median 1.68M (5-95th: 0.54M-2.30M) | (paper reports; not extracted yet) | Empirical PLHIV 2020 ≈ 1.3M (UNAIDS). HIVsim median above but ensemble brackets it. |
| Number on ART, all ages | Partly | 2023 median 1.19M (saturated at empirical cap) | (paper reports; not extracted yet) | Bounded by `data/n_art.csv` (Zimbabwe MoH 1990-2021, held constant thereafter). Paper A's models likely project ART targets beyond 2021 rather than using an empirical cap — a genuine structural difference. |
| AIDS-related deaths per year | Yes | 2023 median 5,220 (5-95th: 0-16,138) | (paper reports; not extracted yet) | HIVsim tracks the empirical trajectory (peak ~120k mid-2000s, decline to ~10k by 2020) but slightly overshoots the historical peak in 2005-2010. |

## Paper B (Bansi-Matharu et al. 2025, MIHPSA) — treatment cascade + transmission attribution

| Indicator | Directly comparable? | HIVsim @ 2024 | Published 4-model range (Zimbabwe) | Notes on structural differences |
|---|---|---|---|---|
| 1st 95: Diagnosed among PLHIV (%) | Yes | 2023 median 98 (5-95th: 97-100) | ~95% (paper reports high & stable) | HIVsim slightly overshoots — a plausible reflection of the near-universal testing regime already scaled up in the sim. |
| 2nd 95: On ART among diagnosed (%) | Partly | 2023 median 72 (5-95th: 53-100) | ~90% (paper reports) | Structural difference: HIVsim's ART enrolment is capped by empirical `n_art.csv` (~1.19M from 2020). Draws overshooting PLHIV then get lower "on ART among diagnosed" because the ART numerator saturates while diagnoses keep rising. |
| 3rd 95 proxy: On ART past efficacy ramp (%) | Approximate | 2023 median 83 (5-95th: 81-85) | ~95% viral suppression (paper reports) | stisim doesn't model viral load explicitly; we use "on ART for ≥ 6 months" (`time_to_art_efficacy`) as the "effectively suppressed" proxy. Paper B measures VL suppression directly. |
| Transmission from undiagnosed (%) | Yes | 2024 median 7.5 (5-95th: 0.0-20.7) | 29.8-64.6 (4-model range) | HIVsim runs LOW because our sim diagnoses ~97% of PLHIV; Paper B's models retain a larger undiagnosed pool. |
| Transmission from diagnosed-not-on-ART (%) | Yes but structurally sensitive | 2024 median 57.9 (5-95th: 0.0-78.6) | <5.0 (all models) | HIVsim runs HIGH: the ART cap forces excess PLHIV into "diagnosed but not on ART". A definitional overlap that could be resolved with a cascade-aware ART allocation. |
| Transmission from on-ART (%) | Yes | 2024 median 31.1 (5-95th: 12.2-100) | 19.5-54.2 | In range. |
| Transmission from post-ART / ART-interrupted (%) | No | ~0 | 4.7-21.5 | Structural: stisim's HIV module does not model ART interruption endogenously. Clearest case where the models differ *by design*, not a fit failure. |

## Overall structural notes

- **ART allocation.** HIVsim uses `sti.ART` with time-varying coverage tied to Zimbabwe's empirical ART numbers. When PLHIV in the sim exceed the ART curve, agents are picked for ART enrolment on a policy that doesn't currently prioritise by CD4 or diagnosis-time. Paper A's models explicitly implement CD4-based prioritisation or "test-and-treat" logic. This is the ART-prioritisation example the analysis plan flags (§4, §8) as an "appropriate structural difference".
- **Viral suppression / VL.** No explicit VL modelling in stisim's HIV module; ART efficacy is a scalar `art_efficacy = 0.96` on transmission rel_trans, ramping from 1.0 over `time_to_art_efficacy = 6 months`. Paper B's models measure VL suppression directly.
- **Post-ART / interruption.** Not modelled endogenously in stisim; agents on ART stay on ART. Paper B relies on this stage for a substantial fraction of transmissions (4.7-21.5%). Any transmission that Paper B attributes to "interrupted" is redistributed across other stages in HIVsim.
- **Age structure.** HIVsim uses starsim's `[X, Y)` age-band convention. Paper A's 15-49 aggregate is well-approximated by summing bands `15_20 + 20_25 + 25_30 + 30_35 + 35_50` (this covers ages 15-49 inclusive).
- **Calibration source.** HIVsim ensemble comes from a *joint* HIV + syphilis + NG/CT/TV/BV Bayesian LHS calibration in the `sti_notification` project; only the HIV-relevant priors were retained for this validation. See `calibration/artifacts/CALIBRATION_SUMMARY.md`.

## Open questions to resolve on the next iteration

- Digitise year-by-year traces from the Taramusi paper (once PDF available) and swap the point ranges for full curves in `paper_a_overlay.png`.
- Sub-select the ensemble to HIV-well-fit draws (hiv_dist < 0.01 vs empirical whole-pop target of 9.35%) and quote *both* the full-ensemble and HIV-fit-subset central tendencies — the paper's audience will want to see both.
- Consider whether the ART supply cap should be relaxed for the projection window (post-2021), and re-run with a scaling / logistic-cap policy that matches paper A's "status quo continuation" definition rather than a hard historical cap.
