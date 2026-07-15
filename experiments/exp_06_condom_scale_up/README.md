# Exp 06 — Condom-use scale-up from 2005 onwards

**Question.** [exp_05](../exp_05_art_by_coverage/SUMMARY.md) showed
that switching ART to coverage-based enrollment (p_art) helps but the
sim's HIV epidemic still runs 1.7-2.7× hot on PLHIV / new_infections
at 2020. Cutting β directly is one option; a more mechanism-consistent
alternative is to push condom use UP from 2005 onwards, matching
Zimbabwe's real ABC / behaviour-change response. The current
`data/condom_use.csv` plateaus at 0.70 for most cross-risk partnerships
from 2005–2015 — exactly the period the sim's PLHIV runs away.
Does pushing condom use higher in that window close the transmission
overshoot without any β change?

**Plan.**
- Three scenarios, same 30-draw LHS (paired draws across scenarios):

  | scenario | condom use for cross-risk partnerships (0,1)(0,2)(1,0)(1,2)(2,0)(2,1) |
  |---|---|
  | **current** | 2005: 0.70, 2010: 0.70, 2015: 0.70, 2020: 0.80 (as-is) |
  | **modest** | 2005: 0.70, 2010: 0.80, 2015: 0.85, 2020: 0.90 |
  | **aggressive** | 2005: 0.70, 2010: 0.90, 2015: 0.95, 2020: 0.95 |

  Marital / homogamous partnerships (0,0), (1,1), (2,2) and FSW-client
  unchanged in all three (they're already at their calibrated
  positions). Pre-2005 unchanged across all three scenarios so the
  early epidemic remains identical.
- 30 LHS × 1 seed × 10 000 agents × 1985-2040 per scenario = 90 sims.
- Same 3×3 diagnostic panel as exp_04/exp_05, but with three coloured
  lines (one per scenario) plus UNAIDS red dots.

**Success criteria.**
- **new_infections 2010-2020** falls under the modest or aggressive
  scenario to approach UNAIDS (target 76 k at 2010, 42 k at 2015,
  18 k at 2020).
- **PLHIV trajectory bends over** in the modest/aggressive scenarios
  — starts falling by ~2005-2010 as reduced transmission catches up.
- No collateral damage on n_alive (should be identical across
  scenarios up to noise), prev_15_49, or the F/M prevalence panels
  outside the direction the intervention should push.
- Preferred scenario is the one that hits UNAIDS closest without
  overshooting the low side.

**Motivation.** Cutting β_m2f is unlabelled — it doesn't say what
changed in the world. Zimbabwe's condom promotion campaigns (National
AIDS Council, PSI, church-led marital programmes) grew substantially
post-2003 in response to the crisis. Elevating condom use in
cross-risk partnerships is the mechanism through which that
behaviour change would appear in a transmission model. If the effect
is enough to bring transmission into UNAIDS's neighbourhood, that
tells us the transmission overshoot was really a behaviour-response
mis-parameterisation and not a fundamental β issue.
