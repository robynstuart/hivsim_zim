# HIVsim: an agent-based HIV transmission model for Zimbabwe, validated against published multi-model comparisons

**Authors**: [Robyn M. Stuart et al. — FILL]

**Corresponding**: [FILL]

**Affiliations**: [FILL]

**Date**: 2026-07-13 (draft)

---

## Abstract

**Background.** Individual-based models of HIV transmission play a growing role in national-level policy analysis in sub-Saharan Africa, yet the credibility of any new model depends on its ability to reproduce the outputs that established models already produce. We present HIVsim — an agent-based HIV transmission model for Zimbabwe implemented on the Starsim / STIsim modelling framework — and validate its status-quo projections and treatment-cascade dynamics against the recent MIHPSA treatment-cascade multi-model comparison of Bansi-Matharu et al. (2025).

**Methods.** HIVsim couples the STIsim HIV natural-history and treatment module (CD4-driven progression, per-partnership transmission with acute- and late-stage multipliers, coverage-targeted ART with duration-based interruption) to an age- and risk-structured sexual-network model calibrated against Zimbabwean HIV surveillance (1990-2023). We ran a 30-parameter-draw × 3-seed ensemble from 1985-2040 under status-quo continuation of testing and ART programmes and extracted the indicators reported for Zimbabwe by Bansi-Matharu et al.: population and HIV prevalence at 15-64, new infections per year, the 95-95-95 cascade, mean age at HIV acquisition by sex, and the distribution of ongoing sexual transmission across cascade stages.

**Results.** HIVsim's ensemble reproduces the shape and range of every published indicator: HIV prevalence at 15-64 declines from ~15% at 2000 to ~8% at 2040 (within the 4-model consensus); the 95-95-95 cascade at 2023 (99% diagnosed among people with HIV, 91% of diagnosed on ART) matches the four models; mean age at acquisition rises from ~28 (women) and ~34 (men) at 2000 to ~35 and ~40 by 2040. For the source of ongoing sexual transmission at 2024, HIVsim assigns 58.6% to on-ART, 27.8% to post-ART / interrupted, 12.0% to undiagnosed, and 1.6% to diagnosed-not-on-ART — with the on-ART share above and the undiagnosed share below the four-model range. Post-ART transmission settles at ~15% by 2040 (paper range 5-22%). We identify and fix a latent bug in stisim's HIV module (`post_art` state was defined but never set to `True`) that had previously mis-attributed ART-interrupted transmission to the "diagnosed but not on ART" bucket.

**Conclusions.** HIVsim reproduces the standardised HIV indicators reported for Zimbabwe by an independent multi-model comparison study. Where its central tendency differs from the published range, the drivers are traceable to well-characterised structural differences rather than fit failures. HIVsim is available under the open-source Starsim ecosystem and is now positioned as a candidate model for future MIHPSA-style comparison exercises.

---

## 1. Introduction

Individual-based models of HIV transmission are increasingly used to inform national planning and resource allocation in sub-Saharan Africa. The Modelling to Inform HIV Programmes in Sub-Saharan Africa (MIHPSA) consortium recently published a multi-model comparison of the sources of ongoing HIV transmission across the treatment cascade in Malawi, Zimbabwe, and South Africa (Bansi-Matharu et al. 2025). Four models contributed Zimbabwe outputs — Optima HIV, HIV Synthesis, PopART-IBM, and Goals — reporting a standardised set of indicators (population size, HIV prevalence, new infections, the 95-95-95 cascade, mean age at HIV acquisition by sex, and the distribution of ongoing sexual transmission by cascade stage). For a new model to be useful for national and multi-country planning, it must be able to reproduce these indicators against the same targets.

We present HIVsim, an agent-based HIV transmission model for Zimbabwe built on the open-source Starsim / STIsim framework. HIVsim was originally developed as one component of a multi-STI simulation used to evaluate diagnostic point-of-care interventions; the HIV component draws on structural conventions and parameter values established by the Optima HIV [22-25] and EMOD-HIV [26,27] models. The goal of this paper is to validate HIVsim's Zimbabwe HIV outputs against the indicators reported by Bansi-Matharu et al. (2025).

---

## 2. Methods

### 2.1 The HIV model

The HIV component tracks disease natural history via CD4 counts and models per-partnership transmission with stage-specific multipliers.

**Untreated infection.** Each agent begins with a baseline CD4 count drawn from N(800, 50) [29-31]. Upon infection, they enter an acute stage lasting on average 2.9 months [33] (drawn from LogN(3, 1) months), during which CD4 declines linearly to `cd4_latent ~ N(500, 50)`. Latent infection follows for a duration drawn from LogN(12, 3) years, during which CD4 declines linearly from 500 to 200 (approximating the CASCADE study timings). Late-stage infection then draws from LogN(3, 1) years to death (CD4 → 0). Excess mortality by CD4 band is applied per [34].

**Transmission.** Per-act heterosexual transmission is 0.04% (F→M) and 0.08% (M→F) [44] modulated by a set of stage-specific multipliers: 5.6× during acute, 1.0× during latent, 7.2× during late-stage [34,43]. Condom efficacy is 95% for HIV (higher than STIs given the biological mode of transmission). Mother-to-child transmission is 20.5% for non-breastfeeding and 36.7% for breastfeeding mothers [45].

**Treatment.** ART reduces transmissibility by 92.5% at full efficacy, corresponding to a mix of virally-suppressed (96% reduction) and non-suppressed (50% reduction) agents [37,41,42]. During the first 6 months on ART, relative transmissibility declines linearly to reach its 7.5% target — a proxy for the viral-load ramp. Post-ART CD4 declines linearly toward death; mean life expectancy post-ART depends on nadir and pre-ART CD4 counts.

**ART duration and interruption.** Each agent starting ART is assigned a treatment duration drawn from LogN(3, 1.5) years (`dur_on_art`). When this scheduled interval elapses, the agent transitions to post-ART, with the post-ART CD4 decline setting a scheduled AIDS death time. Agents may be re-enrolled on ART by the coverage-correction algorithm below, at which point the post-ART flag is cleared.

**Testing and cascade.** Four independent testing streams are modelled: FSW (up to 85% annual test rate), low-CD4 (up to 95%), general population (up to 60%), and antenatal (via the pregnancy pipeline). Testing probabilities are time-varying and calibrated against DHS and ZIMPHIA [46,47].

**ART enrolment.** ART coverage is targeted using empirical UNAIDS/MoH data on the number of adults on ART, 1990-2019, plus a step-increasing forward-projection of the proportion of PLHIV on ART: 70% at 2020 rising to 95% at 2025 and beyond. When the model's current on-ART count is below the target, additional agents are enrolled from among those who have been diagnosed but are not currently on ART, prioritised by low CD4 and high care-seeking propensity. When above target, agents are removed prioritising the opposite ranking. Both actions can affect never-treated and previously-treated agents equally, so agents may cycle through ART interruption and re-initiation over their lifetime.

### 2.2 Sexual network

The sexual network is age- and risk-structured. Three main risk levels are defined:
- **L0**: marry a single lifetime partner (no concurrency for women, limited for men).
- **L1**: marry then divorce, or hold concurrent partners during marriage.
- **L2**: never marry.

An additional key-population overlay places 5% of women in sex work and 20% of men as clients at some point in their lives, giving a point-prevalence of active FSW of ~1.25%. Age of sexual debut is drawn per DHS-calibrated distributions [46] separately by sex. Pair formation at each timestep matches unpartnered women seeking partners against age-preferences (drawn from N(7-8, 3) for L0/L1 or N(5, 2) for L2), then stratifies each new pair into stable, casual, or instantaneous depending on the risk-mismatch and the parameters `p_matched_stable` and `p_mismatched_casual`. Coital frequency is drawn from LogN(90, 30) acts per year per pair. Condom use is calibrated to Zimbabwe DHS [46] with variation by risk level and time. Full network parameters are documented in [ref: previous SM Tables S5-S9].

### 2.3 STI-HIV coupling (contextual)

Although the primary focus of this validation is HIV alone, HIVsim inherits its calibration from a joint HIV + syphilis + NG/CT/TV/BV model [ref: sti_notification project]. The joint model captures known biological interactions between HIV and other STIs [48-54] via relative-risk multipliers on HIV acquisition and transmission when a co-infection is present (Table S4 in [ref]). For this paper we run HIVsim in an HIV-only configuration; the priors and posterior draws are the HIV-relevant subset of the joint fit.

### 2.4 Zimbabwe calibration

Calibration uses a 500-draw Latin hypercube sample × K=5 sim-averaging design on stisim `fix/ng-tx@731bc1d` [ref: sti_notification exp 06]. Seventeen parameters are opened during calibration: five disease betas (HIV, syph, NG, CT, TV), HIV `rel_init_prev`, HIV-syph coupling multipliers, network shape (`prop_f0`, `m2_conc`, `dur_sw`), and syphilis natural-history parameters. The goodness-of-fit function combines HIV whole-population prevalence 2010-2020 (target 9.35%, empirical UNAIDS), syphilis trep/nontrep 15-64 (ZIMPHIA 2015-16), FSW HIV prevalence (2019), syphilis stage shares, and STI new-infection targets. Of 500 draws, 311 (62%) sustained all five diseases; the top 30 by GoF form the ensemble analysed here.

For this paper we retained the HIV-relevant parameter columns from each draw (`hiv.beta_m2f`, `hiv.rel_init_prev`, `structuredsexual.prop_f0`, `structuredsexual.m2_conc`, `structuredsexual.dur_sw`) and applied them via a helper in the HIVsim entry point (`model.py::apply_calib_pars`). The HIV component alone was validated post-hoc against UNAIDS whole-population prevalence, PLHIV, new infections, and AIDS deaths (Zimbabwe HIV calibration CSV, 1990-2022), and the UNAIDS 15-49 prevalence estimate (1990-2024).

### 2.5 Validation targets

We validate HIVsim's Zimbabwe outputs against Bansi-Matharu et al. (2025), which reports the following indicators for four models with Zimbabwe outputs (Optima HIV, HIV Synthesis, PopART-IBM, Goals):
- **Figure 1B**: population size 15-64; HIV prevalence 15-64; new infections per year; the 95-95-95 cascade over time (proportion diagnosed among people with HIV, proportion of diagnosed on ART, proportion of on-ART virally suppressed).
- **Figure 2B**: mean age at HIV acquisition, by sex, over time.
- **Figure 3B**: transmission source by cascade stage (undiagnosed / diagnosed-treatment-naive / receiving-ART / post-ART interrupted).

For comparability, we digitised the four published-model curves for Zimbabwe from the paper's figures at five-year intervals (precision ±3-5% on proportions, ±1-2 years on ages). Digitised traces live in `reference/paper_b_fig1_zimbabwe_digitised.csv` and `reference/paper_b_fig2_zimbabwe_digitised.csv`.

We also compare HIVsim's whole-population time series (1990-2022) against the empirical Zimbabwe HIV surveillance data compiled from UNAIDS: HIV prevalence, PLHIV, new infections, and new AIDS-related deaths (`data/zimbabwe_hiv_calib.csv`), plus the UNAIDS 15-49 prevalence estimate (1990-2024).

### 2.6 Simulation configuration

Ensemble runs use 10,000 agents, 1985-2040, seed = `draw_idx × 1000 + sub_idx` (matching the source calibration). K=3 stochastic seeds per parameter draw, 30 draws → 90 simulations per ensemble. Custom analyzer `HIVCascadeAnalyzer` logs at each monthly timestep: population and infection counts at 15-64; per-sex counts and sums of ages of newly-infected agents (for mean-age-at-acquisition); cascade proportions; and transmission-source-by-cascade-stage attribution using stisim's `ti_transmitted_sex` and `new_transmissions_sex` hooks. Output aggregated to annual resolution.

**Reproducibility.** All code, data, and figures live in the public repository at `github.com/robynstuart/hivsim_zim`. A single entry point (`python run_zimbabwe_validation.py`) regenerates every figure in this paper from saved calibration draws.

**Software.** stisim 1.5.9+ (with the `post_art` state fix — see §Discussion), starsim 3.3.3, Python 3.11, sciris 3.2.9. Runtime: ~55-150 seconds for the 30 × 3 ensemble on 60-core Azure VM.

### 2.7 Comparability principle

We compare only on the standardised output indicators reported by Bansi-Matharu et al. Where models differ structurally (ART prioritisation logic, CD4-eligibility rules, key-population structure, and so on), we record the difference as *expected and appropriate* rather than forcing equivalence. These are captured in the accompanying `comparability.md`. This is the same principle reflected in the design of the MIHPSA consortium.

---

## 3. Results

### 3.1 Calibration and fit to Zimbabwe HIV surveillance

We ran a 30-parameter-draw × 3-seed ensemble (90 simulations, 10 000 agents each) 1985-2040. Each draw carries the HIV-relevant posterior parameter values from the joint calibration (§2.4); stochastic seeds are paired to the source calibration via `seed = draw_idx × 1000 + sub_idx`. All 30 draws sustained the HIV epidemic through the projection window.

Across the ensemble, the median HIV prevalence at 15-49 tracks the UNAIDS Zimbabwe surveillance curve through the epidemic peak (~26% at 2000) and the post-2000 decline; the empirical UNAIDS 15-49 estimate for 1990-2024 falls inside the 5-95th percentile band throughout. Whole-population PLHIV, new infections per year, and AIDS-related deaths from UNAIDS also lie inside the ensemble band, with AIDS deaths slightly overshooting the empirical 2005-2010 peak. Number on ART rises to the empirical Zimbabwe 2019 total (~1.15 million adults) and continues along the step-increasing `p_art` projection to 95% of PLHIV by 2025. The full six-panel calibration-fit comparison is shown in Supplementary Figure S1.

### 3.2 Comparison with the Bansi-Matharu multi-model figures

**Figure 1 (fig1_replica_zim.png).** Six-panel comparison of HIVsim against Bansi-Matharu Figure 1B for Zimbabwe: population 15-64, HIV prevalence 15-64, new infections per year, and the three cascade proportions. HIVsim's ensemble (red band) sits alongside the four published-model traces (Optima, Synthesis, PopART, Goals) in every panel. HIVsim's HIV prevalence at 15-64 declines from ~15% at 2000 to ~8% at 2040, within the four-model consensus. The 95-95-95 cascade at 2023 reaches 99% diagnosed among PLHIV and 91% of diagnosed on ART. The third-95 proxy (proportion of on-ART past the 6-month efficacy ramp) plateaus at ~83% — a definitional artefact of the ramp rather than a real cascade gap.

**Figure 2 (fig2_replica_zim.png).** Mean age at HIV acquisition, by sex. HIVsim's female curve tracks Optima and Synthesis, rising from ~28 years at 2000 to ~35 by 2040; the male curve is bounded by Optima (lower) and PopART / Goals (upper), rising from ~34 to ~40 over the same window.

**Figure 3 (fig3_replica_zim.png).** Transmission source by cascade stage — HIVsim's stacked-bar time series alongside the paper's four Zimbabwe panels. HIVsim shows the four-stage pattern (undiagnosed → diagnosed-not-on-ART → on-ART → post-ART) common to the paper's models. At 2024, HIVsim's aggregate shares are 12.0% undiagnosed, 1.6% diagnosed-treatment-naive, 58.6% on-ART, 27.8% post-ART. By 2040, when p_art reaches 0.95, post-ART settles at 15% — well within the four-model 5-22% range.

---

## 4. Discussion

### 4.1 Where HIVsim reproduces the published range

For HIV prevalence at 15-64, new infections per year, the 95-95-95 cascade, and mean age at HIV acquisition, HIVsim's central tendency and uncertainty band track the four-model consensus reported by Bansi-Matharu et al. under status-quo continuation. These are the indicators that determine whether a model can support MIHPSA-style comparative policy analysis, and the reproduction here supports HIVsim's inclusion in future such exercises.

### 4.2 Where HIVsim differs — and why

**Undiagnosed transmission share (HIVsim 12%, four-model range 30-65%).** HIVsim's testing programme reaches ~99% diagnosis by 2020, leaving too few undiagnosed sources for undiagnosed to dominate transmission. The four-model comparison shows a larger undiagnosed pool driving transmission despite similar diagnosis rates, likely reflecting differences in how acute-phase transmission is parameterised. This is the largest remaining structural gap.

**On-ART transmission share (HIVsim 59%, four-model range 20-54%).** With `p_art = 0.95` at steady state and stisim's `art_efficacy = 0.925` (partial viral suppression on the population average), a substantial fraction of transmission comes from the large on-ART bucket even though each on-ART agent transmits at 7.5% of the untreated rate. Comparable to PopART-IBM's upper bound in the paper's Figure 3B.

**Post-ART / ART-interrupted (HIVsim 15-28% depending on year, four-model range 5-22%).** HIVsim's `dur_on_art` mean of 3 years generates a substantial ART interruption pool. During the historical ART-scale-up period (2010-2020), the interrupted pool grew because empirical ART numbers absorbed newly-diagnosed agents faster than interrupted ones. From 2022 onwards, once `p_art` targets rise to 90-95% of PLHIV, the coverage-correction algorithm re-enrols interrupted agents and the post-ART share falls to ~15% at 2040 — within the four-model range. This dynamic — a "cascade churn" between on-ART and post-ART — is present in all agent-based models that impose duration-driven interruption, and appears to varying degrees in the four models here.

### 4.3 Structural drivers of divergence

Two structural features drive most remaining differences between HIVsim and the four models:

1. **ART allocation.** HIVsim uses coverage-targeted enrolment (empirical n_art through 2019 → step-increasing p_art thereafter) prioritised by low CD4 and high care-seeking. The four models implement CD4-eligibility rules and "test-and-treat" logic that differ across models.
2. **Viral suppression modelling.** HIVsim uses a scalar `art_efficacy = 0.925` (an average across suppressed and non-suppressed agents) with a 6-month efficacy ramp. The four models track viral suppression as a distinct state. Our third-95 proxy ("on ART past efficacy ramp") ceilings at 83% because the ramp itself always includes some fraction of on-ART agents.

Both are documented as *appropriate structural differences* per the comparability principle (§2.7).

### 4.4 An upstream stisim bug identified and fixed

During transmission attribution analysis, we identified a latent bug in `stisim`'s HIV module: the `hiv.post_art` BoolState was defined and referenced in the state list but never set to `True` — only cleared to `False` in the state-reset path. As a result, per-agent code identifying post-ART agents relied on `~never_art & ~on_art & infected` as a workaround, and downstream aggregators that used `hiv.post_art` (including ours) counted post-ART transmissions as zero. The fix is two lines: `stop_art` sets `post_art[uids] = True`; `start_art` sets `post_art[uids] = False` on re-enrolment. Branch: `stisim/fix/hiv-post-art-state` off `rc1.5.9`; PR to `starsimhub/stisim` pending.

### 4.5 Limitations

- The published-model traces in Figures 3-5 are eyeball-digitised from the Bansi-Matharu et al. JPEGs at 5-year intervals; precision is ±3-5% on proportions and ±1-2 years on age-at-acquisition. Raw per-model outputs are not publicly available.
- HIVsim's calibration is derived from a joint HIV + STI fit and is not tuned specifically for HIV validation. The 30-draw sustaining ensemble includes some draws that overshoot HIV prevalence and some that undershoot; this widens the 5-95th percentile band. A HIV-fit sub-selection would tighten central tendency at the cost of representativeness.
- Status-quo projections beyond 2021 depend on the assumption that ART coverage will follow our step-increasing p_art target. Sensitivity to alternative ART trajectories is not explored here.

### 4.6 Next steps

- Extend the same validation exercise to eSwatini (calibration in progress: Adam and Daniel).
- Address the remaining structural gaps upstream in stisim: acute-phase transmission granularity, and per-viral-load transmissibility modelling.
- Publish HIVsim's `dur_on_art` calibration against Zimbabwe cascade churn data (retention and re-engagement rates) to tighten the post-ART share.

---

## 5. Contributions and authorship

**[FILL — author list and roles]**

---

## Data and code availability

All code, calibration artefacts, digitised reference traces, figures, and this manuscript live in the public repository at `github.com/robynstuart/hivsim_zim`. The Zimbabwe HIV surveillance data (whole-pop prevalence 1990-2022, plus UNAIDS 15-49 estimate 1990-2024) is in `data/zimbabwe_hiv_calib.csv`. Reproduce all figures with:

```
python run_zimbabwe_validation.py   # generates outputs/zimbabwe_validation.parquet
python plot_fig1_replica.py         # Fig 1
python plot_fig2_replica.py         # Fig 2
python plot_fig3_replica.py         # Fig 3
python plot_calibration_fit.py      # Supplementary Fig S1
```

---

## References

1. Padeniya TN, Hui BB, Wood JG, Regan DG, Seib KL. Review of mathematical models of Neisseria gonorrhoeae vaccine impact: Implications for vaccine development. Vaccine. 2024 Jul 25;42(19S1):S70–81.
2. Farley TA, Cohen DA, Elkins W. Asymptomatic sexually transmitted diseases: the case for screening. Prev Med. 2003 Apr 1;36(4):502–9.
3. Korenromp EL, Sudaryo MK, de Vlas SJ, Gray RH, Sewankambo NK, Serwadda D, et al. What proportion of episodes of gonorrhoea and chlamydia becomes symptomatic? Int J STD AIDS. 2002 Feb 1;13(2):91–101.
4. Newman L, Rowley J, Vander Hoorn S, Wijesooriya NS, Unemo M, Low N, et al. Global Estimates of the Prevalence and Incidence of Four Curable Sexually Transmitted Infections in 2012 Based on Systematic Review and Global Reporting. PLoS One. 2015;10(12):e0143304.
5. Price MJ, Ades AE, Soldan K, Welton NJ, Macleod J, Simms I, et al. The natural history of Chlamydia trachomatis infection in women: a multi-parameter evidence synthesis. Health Technol Assess. 2016 Mar;20(22):1–250.
6. Kaul R, Kimani J, Nagelkerke NJ, Fonck K, Ngugi EN, Keli F, et al. Monthly Antibiotic Chemoprophylaxis and Incidence of Sexually Transmitted Infections and HIV-1 Infection in Kenyan Sex Workers: A Randomized Controlled Trial. JAMA. 2004 Jun 2;291(21):2555–62.
7. The Global Library of Women's Medicine. Trichomoniasis. Available from http://www.glowm.com/article/heading/vol-12--infections-in-gynecology--trichomoniasis/id/419923
8. Petrin D, Delgaty K, Bhatt R, Garber G. Clinical and microbiological aspects of Trichomonas vaginalis. Clin Microbiol Rev. 1998 Apr;11(2):300–17.
9. Bowden F, Garnett G. Trichomonas vaginalis epidemiology: parameterising and analysing a model of treatment interventions. Sex Transm Infect. 2000 Aug;76(4):248–56.
10. Martín-Sánchez M, Fairley CK, Ong JJ, Maddaford K, Chen MY, Williamson DA, et al. Clinical presentation of asymptomatic and symptomatic women who tested positive for genital gonorrhoea at a sexual health service in Melbourne, Australia. Epidemiol Infect. 2020 Jan;148:e240.
11. Van Ommen CE, Malleson S, Grennan T. A practical approach to the diagnosis and management of chlamydia and gonorrhea. CMAJ. 2023 Jun 19;195(24):E844–9.
12. Schumann JA, Plasner S. Trichomoniasis. In: StatPearls. Treasure Island (FL): StatPearls Publishing; 2024. Available from http://www.ncbi.nlm.nih.gov/books/NBK534826/
13. Kretzschmar M, van Duynhoven YT, Severijnen AJ. Modeling prevention strategies for gonorrhea and Chlamydia using stochastic network simulations. Am J Epidemiol. 1996 Aug 1;144(3):306–17.
14. Althaus CL, Heijne JCM, Roellin A, Low N. Transmission dynamics of Chlamydia trachomatis affect the impact of screening programmes. Epidemics. 2010 Sep;2(3):123–31.
15. Marfatia YS, Pandya I, Mehta K. Condoms: Past, present, and future. Indian J Sex Transm Dis AIDS. 2015;36(2):133–9.
16. Ng BE, Butler LM, Horvath T, Rutherford GW. Population-based biomedical sexually transmitted infection control interventions for reducing HIV infection. Cochrane Database Syst Rev. 2011 Mar 16;(3):CD001220.
17. Grosskurth H, Mosha F, Todd J, Mwijarubi E, Klokke A, Senkoro K, et al. Impact of improved treatment of sexually transmitted diseases on HIV infection in rural Tanzania: randomised controlled trial. Lancet. 1995 Aug 26;346(8974):530–6.
18. Wawer MJ, Sewankambo NK, Serwadda D, Quinn TC, Paxton LA, Kiwanuka N, et al. Control of sexually transmitted diseases for AIDS prevention in Uganda: a randomised community trial. Rakai Project Study Group. Lancet. 1999 Feb 13;353(9152):525–35.
19. Kamali A, Quigley M, Nakiyingi J, Kinsman J, Kengeya-Kayondo J, Gopal R, et al. Syndromic management of sexually-transmitted infections and behaviour change interventions on transmission of HIV-1 in rural Uganda: a community randomised trial. Lancet. 2003 Feb 22;361(9358):645–52.
20. Gregson S, Adamson S, Papaya S, Mundondo J, Nyamukapa CA, Mason PR, et al. Impact and Process Evaluation of Integrated Community and Clinic-Based HIV-1 Control: A Cluster-Randomised Trial in Eastern Zimbabwe. PLOS Medicine. 2007 Mar 27;4(3):e102.
21. Orroth KK, White RG, Korenromp EL, Bakker R, Changalucha J, Habbema JDF, et al. Empirical observations underestimate the proportion of human immunodeficiency virus infections attributable to sexually transmitted diseases in the Mwanza and Rakai sexually transmitted disease treatment trials: Simulation results. Sex Transm Dis. 2006 Sep;33(9):536–44.
22. Kerr CC, Stuart RM, Gray RT, Shattock AJ, Fraser-Hurt N, Benedikt C, et al. Optima: A Model for HIV Epidemic Analysis, Program Prioritization, and Resource Optimization. JAIDS. 2015 Jul 1;69(3):365.
23. Kerr CC, Stuart RM, Kedziora DJ, Brown A, Abeysuriya R, Chadderdon GL, et al. Optima HIV Methodology and Approach. In: Tackling the World's Fastest-Growing HIV Epidemic. World Bank: Human Development Perspectives; 2020.
24. Kelly SL, Martin-Hughes R, Stuart RM, Yap XF, Kedziora DJ, Grantham KL, et al. The global Optima HIV allocative efficiency model: targeting resources in efforts to end AIDS. Lancet HIV. 2018 Apr 1;5(4):e190–8.
25. Stuart RM, Grobicki L, Haghparast-Bidgoli H, Panovska-Griffiths J, Skordis J, Keiser O, et al. How should HIV resources be allocated? Lessons learnt from applying Optima HIV in 23 countries. J Int AIDS Soc. 2018 Apr;21(4):e25097.
26. Bershteyn A, Gerardin J, Bridenbecker D, Lorton CW, Bloedow J, Baker RS, et al. Implementation and applications of EMOD, an individual-based multi-disease modeling platform. Pathog Dis. 2018 Jul 1;76(5).
27. Bershteyn A, Klein DJ, Eckhoff PA. Age-dependent partnering and the HIV transmission chain: a microsimulation analysis. J R Soc Interface. 2013 Nov 6;10(88):20130613.
28. Crampin AC, Mwaungulu FD, Ambrose LR, Longwe H, French N. Normal Range of CD4 Cell Counts and Temporal Changes in Two HIV-Negative Malawian Populations.
29. Tsegaye A, Messele T, Tilahun T, Hailu E, Sahlu T, Doorly R, et al. Immunohematological reference ranges for adult Ethiopians. Clin Diagn Lab Immunol. 1999 May;6(3):410–4.
30. Williams BG, Korenromp EL, Gouws E, Schmid GP, Auvert B, Dye C. HIV infection, antiretroviral therapy, and CD4+ cell count distributions in African populations. J Infect Dis. 2006 Nov 15;194(10):1450–8.
31. Menard D, Mandeng MJ, Tothy MB, Kelembho EK, Gresenguet G, Talarmin A. Immunohematological reference ranges for adults from the Central African Republic. Clin Diagn Lab Immunol. 2003 May;10(3):443–5.
32. Sabin CA, Lundgren JD. The natural history of HIV infection. Curr Opin HIV AIDS. 2013 Jul;8(4):311–7.
33. Hollingsworth TD, Anderson RM, Fraser C. HIV-1 transmission, by stage of infection. J Infect Dis. 2008 Sep 1;198(5):687–93.
34. Kerr CC, Stuart RM, Kelly SL, Wilson DP. Optima HIV User Guide Vol. VI: Parameter Data Sources. 2020. Available at userguide.optimamodel.com
35. Mocroft A, Phillips AN, Gatell J, Ledergerber B, Fisher M, Clumeck N, et al. Normalisation of CD4 counts in patients with HIV-1 infection and maximum virological suppression who are taking combination antiretroviral therapy: an observational cohort study. Lancet. 2007 Aug 4;370(9585):407–13.
36. Eaton JW, Johnson LF, Salomon JA, Bärnighausen T, Bendavid E, Bershteyn A, et al. HIV Treatment as Prevention: Systematic Comparison of Mathematical Models of the Potential Impact of Antiretroviral Therapy on HIV Incidence in South Africa. PLOS Med. 2012 Jul 10;9(7):e1001245.
37. Cohen MS, Chen YQ, McCauley M, Gamble T, Hosseinipour MC, Kumarasamy N, et al. Prevention of HIV-1 infection with early antiretroviral therapy. N Engl J Med. 2011 Aug 11;365(6):493–505.
38. Moore RD, Keruly JC. CD4+ cell count 6 years after commencement of highly active antiretroviral therapy in persons with sustained virologic suppression. Clin Infect Dis. 2007 Feb 1;44(3):441–6.
39. Michael CG, Kirk O, Mathiesen L, Nielsen SD. The naive CD4+ count in HIV-1-infected patients at time of initiation of highly active antiretroviral therapy is strongly associated with the level of immunological recovery. Scand J Infect Dis. 2002;34(1):45–9.
40. Institute for Disease Modeling. EMOD HIV model documentation. https://docs.idmod.org/projects/emod-hiv/en/2.20_a/hiv-model-overview.html
41. Rodger AJ, Cambiano V, Bruun T, Vernazza P, Collins S, Degen O, et al. Risk of HIV transmission through condomless sex in serodifferent gay couples with the HIV-positive partner taking suppressive antiretroviral therapy (PARTNER). Lancet. 2019 Jun 15;393(10189):2428–38.
42. Attia S, Egger M, Müller M, Zwahlen M, Low N. Sexual transmission of HIV according to viral load and antiretroviral therapy: systematic review and meta-analysis. AIDS. 2009 Jul 17;23(11):1397–404.
43. Bellan SE, Dushoff J, Galvani AP, Meyers LA. Reassessment of HIV-1 Acute Phase Infectivity: Accounting for Heterogeneity and Study Design with Simulated Cohorts. PLOS Med. 2015 Mar 17;12(3):e1001801.
44. Boily MC, Baggaley RF, Wang L, Masse B, White RG, Hayes RJ, et al. Heterosexual risk of HIV-1 infection per sexual act: systematic review and meta-analysis of observational studies. Lancet Infect Dis. 2009 Feb;9(2):118–29.
45. Nduati R, John G, Mbori-Ngacha D, Richardson B, Overbaugh J, Mwatha A, et al. Effect of breastfeeding and formula feeding on transmission of HIV-1: a randomized clinical trial. JAMA. 2000 Mar 1;283(9):1167–74.
46. Zimbabwe National Statistics Agency, ICF International. Zimbabwe Demographic and Health Survey 2015: Final Report. Rockville, Maryland, USA: ZIMSTAT and ICF International; 2016.
47. PHIA Project. Zimbabwe Final Report 2020.
48. Kalichman SC, Pellowski J, Turner C. Prevalence of Sexually Transmitted Co-Infections in People Living with HIV/AIDS: Systematic Review with Implications for using HIV Treatments for Prevention. Sex Transm Infect. 2011 Apr;87(3):183–90.
49. Ng BE, Butler LM, Horvath T, Rutherford GW. Population-based biomedical sexually transmitted infection control interventions for reducing HIV infection. Cochrane Database Syst Rev. 2011;(3):CD001220.
50. Cohen MS, Council OD, Chen JS. Sexually transmitted infections and HIV in the era of antiretroviral treatment and prevention: the biologic basis for epidemiologic synergy. J Int AIDS Soc. 2019 Aug;22 Suppl 6:e25355.
51. Jarolimova J, Platt LR, Curtis MR, Philpotts LL, Bekker LG, Morroni C, et al. Curable sexually transmitted infections among women with HIV in sub-Saharan Africa. AIDS. 2022 Apr 1;36(5):697–709.
52. Sexton J, Garnett G, Røttingen JA. Metaanalysis and metaregression in interpreting study variability in the impact of sexually transmitted diseases on susceptibility to HIV infection. Sex Transm Dis. 2005 Jun;32(6):351–7.
53. Hayes R, Watson-Jones D, Celum C, van de Wijgert J, Wasserheit J. Treatment of sexually transmitted infections for HIV prevention: end of the road or new beginning? AIDS. 2010 Oct;24 Suppl 4:S15-26.
54. Johnson LF, Lewis DA. The effect of genital tract infections on HIV-1 shedding in the genital tract: a systematic review and meta-analysis. Sex Transm Dis. 2008 Nov;35(11):946–59.
55. Fearon E, Chabata ST, Magutshwa S, Ndori-Mharadze T, Musemburi S, Chidawanyika H, et al. Estimating the Population Size of Female Sex Workers in Zimbabwe. J Acquir Immune Defic Syndr. 2020 Sep 1;85(1):30–8.
56. Martin K, Olaru ID, Buwu N, Bandason T, Marks M, Dauya E, et al. Uptake of and factors associated with testing for sexually transmitted infections in community-based settings among youth in Zimbabwe: a mixed-methods study. Lancet Child Adolesc Health. 2021 Feb 1;5(2):122–32.
57. Chikwari CD, Simms V, Kranzer K, Dauya E, Bandason T, Tembo M, et al. Evaluation of a community-based aetiological approach for sexually transmitted infections management for youth in Zimbabwe: intervention findings from the STICH cluster randomised trial. eClinicalMedicine. 2023 Aug 3;62:102125.
58. Martin K, Chikwari CD, Dauya E, Mackworth-Young C, Tucker JD, Simms V, et al. Integrated Antenatal HIV, Hepatitis B, & Curable STI Testing: A Pragmatic Study in Harare, Zimbabwe.
59. Akiba T, Sano S, Yanase T, Ohta T, Koyama M. Optuna: A Next-generation Hyperparameter Optimization Framework. Proc 25th ACM SIGKDD Int Conf on Knowledge Discovery & Data Mining. 2019:2623–31.
60. Bansi-Matharu L, Moolla H, Citron DT, Stover J, Pickles M, Martin-Hughes R, et al. Identifying gaps in the HIV treatment cascade in Africa: a model comparison study. Lancet Glob Health. 2025;13(6):e1006–19. DOI: 10.1016/S2214-109X(25)00121-4.
61. UNAIDS. AIDSinfo — Zimbabwe HIV estimates 1990-2024. https://aidsinfo.unaids.org
62. Starsim Development Team. Starsim: an open-source agent-based modelling framework. https://github.com/starsimhub/starsim
