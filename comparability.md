# Comparability matrix: HIVsim Zimbabwe vs published multi-model outputs

Draft. Rows filled in from the Day 1 (Paper A benchmarks) + Day 2 (Paper B
cascade + transmission) runs; the "HIVsim vs published" column will be
tightened once year-by-year traces from the Taramusi paper are digitised
into `reference/`. See `ANALYSIS_PLAN.md` §7 for the scoring convention.

## Paper A (Taramusi et al. 2025) — 5-model status-quo projections

| Indicator | Directly comparable? | HIVsim ensemble @ 2023 / 2040 | Published 5-model range | Notes on structural differences |
|---|---|---|---|---|
| HIV prevalence, 15-49 (%) | Yes | 2023 median 12.2 (5-95th: 2.6-19.4); 2040 median 3.6 (0.9-6.6) | 2023: 12.1-14.3; 2040: 3.9-6.0 | HIVsim ensemble brackets the published range; median in Paper A's 2023 range; 2040 median just below the lower bound. |
| HIV incidence, 15-49 (per 1000 py) | Yes | 2023 median 1.4 (5-95th: 0.2-3.3); 2040 median 0.7 (0.1-2.0) | 2023: 2.0-3.3; 2040: 1.0-3.0 | HIVsim's 2023 median below paper's lower bound; upper 5-95th reaches lower bound. Note: with the step-increasing p_art (70% at 2020 → 95% at 2025) the incidence trajectory is smoother than the pre-fix runs. |
| New infections per year, all ages | Yes | 2025 median 9,570 (5-95th: 1,653-20,880) | <7,800/yr by 2025 (all 5 models) | HIVsim central tendency still slightly above paper's <7,800 benchmark; lower 5-95th %ile well below. Trend consistent with paper models. |
| People living with HIV (PLHIV), all ages | Yes | 2023 median 1.67M | (paper reports; not extracted yet) | Empirical PLHIV 2020 ≈ 1.3M (UNAIDS). HIVsim median above but ensemble brackets it. |
| Number on ART, all ages | Yes | 2023 median 1.53M | (paper reports; not extracted yet) | 1990-2019 driven by empirical `data/n_art.csv`; 2020+ uses step-increasing `p_art` (0.70 → 0.95 by 2025 and beyond). |
| AIDS-related deaths per year | Yes | 2023 median 2,610 (5-95th: 0-7,830) | (paper reports; not extracted yet) | HIVsim tracks the empirical trajectory but may undershoot post-2020 (worth checking against Zim MoH deaths). |

## Paper B (Bansi-Matharu et al. 2025, MIHPSA) — treatment cascade + transmission attribution

| Indicator | Directly comparable? | HIVsim @ 2024 | Published 4-model range (Zimbabwe) | Notes on structural differences |
|---|---|---|---|---|
| 1st 95: Diagnosed among PLHIV (%) | Yes | 2023 median 99 (5-95th: 98-100) | ~95% (paper reports high & stable) | HIVsim slightly overshoots — near-universal testing scaled up in the sim. |
| 2nd 95: On ART among diagnosed (%) | Yes | 2023 median 91 (5-95th: 90-93) | ~90% (paper reports) | Well-matched with step-increasing p_art. |
| 3rd 95 proxy: On ART past efficacy ramp (%) | Approximate | 2023 median 81 (5-95th: 80-83) | ~95% viral suppression (paper reports) | Ceiling at 83% reflects the 6-month efficacy ramp — some on-ART agents are always within their first 6 months. HIVsim doesn't model viral load directly. |
| Transmission from undiagnosed (%) | Yes but structurally distinct | 2024 aggregate 12.0 | 29.8-64.6 (4-model range) | HIVsim LOW because the sim diagnoses ~99% of PLHIV. Paper B's models retain a larger undiagnosed pool despite similar diagnosis rates (possibly per-partnership acute-phase transmission asymmetries). |
| Transmission from diagnosed-not-on-ART (%) | Yes | 2024 aggregate 1.6 | <5.0 (all models) | Well within paper's range after fixing the upstream `post_art` bug in stisim (see §4.4 of preprint). |
| Transmission from on-ART (%) | Yes | 2024 aggregate 58.6 | 19.5-54.2 | Just above paper's upper bound (2024). At 2040 rises to ~74% (further above). Consequence of p_art rising to 95% pushing more PLHIV onto ART. |
| Transmission from post-ART / ART-interrupted (%) | Yes | 2024 aggregate 27.8; 2040 aggregate 14.6 | 4.7-21.5 | 2024 slightly above; 2040 median (14.6) inside paper's range. Trajectory: peaks at 54% in 2020 during ART-scale-up, drops as p_art rises. |

## Overall structural notes

- **ART allocation.** HIVsim uses `sti.ART` with historical n_art through 2021 and `p_art=0.92` (Zimbabwe UNAIDS 2023 coverage) from 2022 onward. Prior iteration used `p_art=0.706` (the sim's own low self-coverage) which artificially depressed on-ART transmission; switching to empirical 0.92 collapsed the "diagnosed-not-on-ART" transmission bucket from 62% to 29% (2024). Paper A's models explicitly implement CD4-based prioritisation or "test-and-treat" logic — this is the ART-prioritisation example the analysis plan flags (§4, §8) as an "appropriate structural difference".
- **Viral suppression / VL.** No explicit VL modelling in stisim's HIV module; ART efficacy is a scalar `art_efficacy = 0.96` on transmission rel_trans, ramping from 1.0 over `time_to_art_efficacy = 6 months`. Paper B's models measure VL suppression directly. Our "effectively suppressed" proxy — "on ART for ≥ 6 months" — plateaus at ~83% because ~17% of on-ART agents are always in the ramp window at steady state.
- **Post-ART / interruption.** Modelled via `dur_on_art` (lognormal, mean 3 yrs) — when scheduled ART duration elapses, agents enter `post_art` state and CD4 declines linearly toward `ti_zero` (death). Paper B's 4.7-21.5% post-ART transmission share is well within HIVsim's ensemble. Note: stisim had a latent bug where the `post_art` boolean was never set to True (only cleared to False); fixed in `stisim/fix/hiv-post-art-state` branched off `rc1.5.9`. Without that fix, ART-interrupted transmissions were mis-attributed to the "diagnosed but not on ART" bucket.
- **Undiagnosed transmission share.** HIVsim consistently assigns a smaller share (~10-15%) of transmission to undiagnosed sources than Paper B (30-65%). Two candidate explanations: (a) our sim reaches 99% diagnosis by 2020, leaving only ~1% of PLHIV undiagnosed at any given time; (b) even among that 1%, stisim's acute-phase transmission multiplier (`rel_trans_acute = 5.3`) may not fully offset the small denominator. Paper B's models likely have higher acute-phase transmission per undiagnosed person, per-partnership viral load dynamics, or lower diagnosis rates.
- **Age structure.** HIVsim uses starsim's `[X, Y)` age-band convention. Paper A's 15-49 aggregate is well-approximated by summing bands `15_20 + 20_25 + 25_30 + 30_35 + 35_50` (this covers ages 15-49 inclusive).
- **Calibration source.** HIVsim ensemble comes from a *joint* HIV + syphilis + NG/CT/TV/BV Bayesian LHS calibration in the `sti_notification` project; only the HIV-relevant priors were retained for this validation. See `calibration/artifacts/CALIBRATION_SUMMARY.md`.

## Open questions to resolve on the next iteration

- Digitise year-by-year traces from the Taramusi paper (once PDF available) and swap the point ranges for full curves in `paper_a_overlay.png`.
- Sub-select the ensemble to HIV-well-fit draws (hiv_dist < 0.01 vs empirical whole-pop target of 9.35%) and quote *both* the full-ensemble and HIV-fit-subset central tendencies — the paper's audience will want to see both.
- Consider whether the ART supply cap should be relaxed for the projection window (post-2021), and re-run with a scaling / logistic-cap policy that matches paper A's "status quo continuation" definition rather than a hard historical cap.
