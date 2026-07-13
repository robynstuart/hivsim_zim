# Comparability matrix: HIVsim Zimbabwe vs published multi-model outputs

Draft. Rows filled in from the Day 1 (Paper A benchmarks) + Day 2 (Paper B
cascade + transmission) runs; the "HIVsim vs published" column will be
tightened once year-by-year traces from the Taramusi paper are digitised
into `reference/`. See `ANALYSIS_PLAN.md` §7 for the scoring convention.

## Paper A (Taramusi et al. 2025) — 5-model status-quo projections

| Indicator | Directly comparable? | HIVsim ensemble @ 2023 / 2040 | Published 5-model range | Notes on structural differences |
|---|---|---|---|---|
| HIV prevalence, 15-49 (%) | Yes | 2023 median 12.2 (5-95th: 2.6-19.4); 2040 median 3.6 (0.9-6.6) | 2023: 12.1-14.3; 2040: 3.9-6.0 | HIVsim ensemble brackets the published range; median in Paper A's 2023 range; 2040 median just below the lower bound. Wide 5-95th spread reflects keeping all 30 sustaining draws (not HIV-fit sub-selected). |
| HIV incidence, 15-49 (per 1000 py) | Yes | 2023 median 1.04 (5-95th: 0.1-2.5); 2040 median 0.73 (0.1-2.0) | 2023: 2.0-3.3; 2040: 1.0-3.0 | With `p_art=0.92` fallback from 2022, HIVsim's incidence declines faster and undershoots Paper A's 2023 range median by ~50%. Ensemble upper %ile still reaches the lower bound. This is the direct consequence of pushing ART coverage to 92% (Zim empirical); the paper models likely have similar ART trajectories but different transmission-per-partnership models. |
| New infections per year, all ages | Yes | 2025 median 10,440 (5-95th: 1,262-24,839) | <7,800/yr by 2025 (all 5 models) | Big shift from the pre-p_art=0.92 run (was 20,010). HIVsim's lower 5-95th %ile (1,262) is now well below 7,800; median (10,440) still above. Consistent with the sim slightly overshooting PLHIV. |
| People living with HIV (PLHIV), all ages | Yes | 2023 median 1.67M (5-95th: 0.55M-2.27M) | (paper reports; not extracted yet) | Empirical PLHIV 2020 ≈ 1.3M (UNAIDS). HIVsim median above but ensemble brackets it. |
| Number on ART, all ages | Yes | 2023 median 1.53M (5-95th: 0.50M-2.09M) | (paper reports; not extracted yet) | 1990-2021 driven by empirical `data/n_art.csv`; 2022+ uses `p_art=0.92` fallback (Zimbabwe's actual 2023 UNAIDS coverage). Previously used the model's own 0.706 self-coverage, which artificially depressed on-ART. |
| AIDS-related deaths per year | Yes | 2023 median 2,610 (5-95th: 0-7,830) | (paper reports; not extracted yet) | With p_art=0.92, AIDS deaths drop further (from 5,220 median pre-fix). HIVsim now potentially undershoots empirical deaths — worth checking against Zimbabwe MoH numbers post-2020. |

## Paper B (Bansi-Matharu et al. 2025, MIHPSA) — treatment cascade + transmission attribution

| Indicator | Directly comparable? | HIVsim @ 2024 | Published 4-model range (Zimbabwe) | Notes on structural differences |
|---|---|---|---|---|
| 1st 95: Diagnosed among PLHIV (%) | Yes | 2023 median 99 (5-95th: 98-100) | ~95% (paper reports high & stable) | HIVsim slightly overshoots — near-universal testing scaled up in the sim. |
| 2nd 95: On ART among diagnosed (%) | Yes | 2023 median 93 (5-95th: 92-94) | ~90% (paper reports) | Now well-matched with `p_art=0.92` fallback. Pre-fix (0.706 self-coverage) had median 72; the shift comes entirely from the ART supply model. |
| 3rd 95 proxy: On ART past efficacy ramp (%) | Approximate | 2023 median 83 (5-95th: 82-85) | ~95% viral suppression (paper reports) | stisim doesn't model viral load explicitly; we use "on ART for ≥ 6 months" (`time_to_art_efficacy`) as the "effectively suppressed" proxy. Paper B measures VL suppression directly. Cap at 83% reflects the efficacy ramp — some on-ART agents are always within their first 6 months. |
| Transmission from undiagnosed (%) | Yes but structurally distinct | 2024 aggregate 12.0 | 29.8-64.6 (4-model range) | HIVsim LOW because the sim diagnoses ~99% of PLHIV — leaves only ~1% of PLHIV undiagnosed at any time; Paper B's models retain a larger undiagnosed pool despite similar diagnosis rates (possibly because they model per-partnership transmission asymmetries — acute-phase transmission peaks in the days-to-months after infection when nobody has been tested yet). |
| Transmission from diagnosed-not-on-ART (%) | Yes | 2024 aggregate 29.1 | <5.0 (all models) | Dropped from 62 pre-p_art-fix to 29 post-fix. Still above the paper's <5%. Remaining gap likely reflects stisim's ART lag: newly-diagnosed agents take up to `time_to_art_efficacy = 6 months` to reach effective suppression, and some fraction of PLHIV are always in that ramp window. |
| Transmission from on-ART (%) | Yes | 2024 aggregate 58.8 | 19.5-54.2 | HIVsim just above the paper's 4-model upper bound. Direct consequence of p_art=0.92 pushing more PLHIV onto ART; because the ART bucket is large, even a small per-partnership transmission rate (art_efficacy 0.96) accumulates. |
| Transmission from post-ART / ART-interrupted (%) | No | ~0 | 4.7-21.5 | Structural: stisim's HIV module does not model ART interruption endogenously. Clearest case where the models differ *by design*, not a fit failure. Adding ART interruption would be upstream stisim work. |

## Overall structural notes

- **ART allocation.** HIVsim uses `sti.ART` with historical n_art through 2021 and `p_art=0.92` (Zimbabwe UNAIDS 2023 coverage) from 2022 onward. Prior iteration used `p_art=0.706` (the sim's own low self-coverage) which artificially depressed on-ART transmission; switching to empirical 0.92 collapsed the "diagnosed-not-on-ART" transmission bucket from 62% to 29% (2024). Paper A's models explicitly implement CD4-based prioritisation or "test-and-treat" logic — this is the ART-prioritisation example the analysis plan flags (§4, §8) as an "appropriate structural difference".
- **Viral suppression / VL.** No explicit VL modelling in stisim's HIV module; ART efficacy is a scalar `art_efficacy = 0.96` on transmission rel_trans, ramping from 1.0 over `time_to_art_efficacy = 6 months`. Paper B's models measure VL suppression directly. Our "effectively suppressed" proxy — "on ART for ≥ 6 months" — plateaus at ~83% because ~17% of on-ART agents are always in the ramp window at steady state.
- **Post-ART / interruption.** Not modelled endogenously in stisim; agents on ART stay on ART. Paper B relies on this stage for a substantial fraction of transmissions (4.7-21.5%). Any transmission that Paper B attributes to "interrupted" is redistributed across other stages in HIVsim.
- **Undiagnosed transmission share.** HIVsim consistently assigns a smaller share (~10-15%) of transmission to undiagnosed sources than Paper B (30-65%). Two candidate explanations: (a) our sim reaches 99% diagnosis by 2020, leaving only ~1% of PLHIV undiagnosed at any given time; (b) even among that 1%, stisim's acute-phase transmission multiplier (`rel_trans_acute = 5.3`) may not fully offset the small denominator. Paper B's models likely have higher acute-phase transmission per undiagnosed person, per-partnership viral load dynamics, or lower diagnosis rates.
- **Age structure.** HIVsim uses starsim's `[X, Y)` age-band convention. Paper A's 15-49 aggregate is well-approximated by summing bands `15_20 + 20_25 + 25_30 + 30_35 + 35_50` (this covers ages 15-49 inclusive).
- **Calibration source.** HIVsim ensemble comes from a *joint* HIV + syphilis + NG/CT/TV/BV Bayesian LHS calibration in the `sti_notification` project; only the HIV-relevant priors were retained for this validation. See `calibration/artifacts/CALIBRATION_SUMMARY.md`.

## Open questions to resolve on the next iteration

- Digitise year-by-year traces from the Taramusi paper (once PDF available) and swap the point ranges for full curves in `paper_a_overlay.png`.
- Sub-select the ensemble to HIV-well-fit draws (hiv_dist < 0.01 vs empirical whole-pop target of 9.35%) and quote *both* the full-ensemble and HIV-fit-subset central tendencies — the paper's audience will want to see both.
- Consider whether the ART supply cap should be relaxed for the projection window (post-2021), and re-run with a scaling / logistic-cap policy that matches paper A's "status quo continuation" definition rather than a hard historical cap.
