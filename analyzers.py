"""
Analyzers for HIVsim Zimbabwe validation.

`HIVCascadeAnalyzer` produces the two Paper B (Bansi-Matharu et al. 2025)
outputs for Zimbabwe:

  1. 95-95-95 cascade over time:
       - prop_diagnosed  = n_diagnosed / n_infected
       - prop_on_art     = n_on_art / n_diagnosed
       - prop_effective  = n_on_art_effective / n_on_art
     where "effective" means agents on ART past the efficacy ramp
     (`time_to_art_efficacy`, default 6 months). This is the closest
     stisim proxy for "virally suppressed".

  2. New sexual transmissions per year attributed to the source's
     cascade stage:
       - undiagnosed             (infected & ~diagnosed)
       - diagnosed_not_on_art    (diagnosed & never_art)
       - on_art                  (currently on ART)
       - post_art                (interrupted ART)
     Matches Paper B Figure 3B exactly (Zimbabwe subset).
"""

import numpy as np
import starsim as ss


class HIVCascadeAnalyzer(ss.Analyzer):
    def __init__(self, disease_name='hiv', **kwargs):
        super().__init__(**kwargs)
        self.disease_name = disease_name

    def init_pre(self, sim):
        super().init_pre(sim)
        self.define_results(
            # Cascade proportions (percent of the preceding stage)
            ss.Result('prop_diagnosed',       dtype=float, scale=False),
            ss.Result('prop_diag_on_art',     dtype=float, scale=False),
            ss.Result('prop_art_effective',   dtype=float, scale=False),
            # Cascade counts
            ss.Result('n_undiagnosed',        dtype=float),
            ss.Result('n_diag_not_on_art',    dtype=float),
            ss.Result('n_on_art_effective',   dtype=float),
            ss.Result('n_post_art',           dtype=float),
            # Transmission attribution (annual counts by source stage at
            # transmission time — cumulated across steps in a year).
            ss.Result('new_trans_undiagnosed',        dtype=float),
            ss.Result('new_trans_diag_not_on_art',    dtype=float),
            ss.Result('new_trans_on_art',             dtype=float),
            ss.Result('new_trans_post_art',           dtype=float),
            # Paper B Fig 1B: population + prev + new-infections at 15-64
            ss.Result('n_alive_15_64',       dtype=float),
            ss.Result('n_infected_15_64',    dtype=float),
            ss.Result('new_infections_15_64', dtype=float),
            # Paper B Fig 2B: mean age at HIV acquisition, by sex.
            # Accumulate sum(age) + count per timestep; divide at plot time.
            ss.Result('age_sum_new_inf_f',  dtype=float),
            ss.Result('age_sum_new_inf_m',  dtype=float),
            ss.Result('n_new_inf_f',        dtype=float),
            ss.Result('n_new_inf_m',        dtype=float),
        )

    def _time_to_art_efficacy_steps(self, sim):
        """Convert HIV `time_to_art_efficacy` duration into whole timesteps.

        stisim ships it as ss.months(6); the sim runs monthly by default,
        so this is ~6 steps. Falls back to 6 if introspection fails.
        """
        try:
            hiv = sim.diseases[self.disease_name]
            dur = hiv.pars.get('time_to_art_efficacy')
            return max(1, int(round(dur / sim.t.dt)))
        except Exception:
            return 6

    def step(self):
        sim = self.sim
        hiv = sim.diseases[self.disease_name]
        ti = sim.ti

        infected      = hiv.infected
        diagnosed     = hiv.diagnosed
        on_art        = hiv.on_art
        post_art      = hiv.post_art

        n_infected  = infected.sum()
        n_diagnosed = (infected & diagnosed).sum()
        n_on_art    = on_art.sum()
        n_post_art  = (infected & post_art).sum()
        n_undiag    = (infected & ~diagnosed).sum()
        # "Diagnosed but treatment naive" = diagnosed, never yet on ART.
        n_diag_not_on_art = (infected & diagnosed & ~on_art & ~post_art).sum()

        # Effective ART: on_art for >= time_to_art_efficacy steps
        steps_eff = self._time_to_art_efficacy_steps(sim)
        ti_art = np.asarray(hiv.ti_art.raw)
        on_art_raw = np.asarray(on_art.raw)
        effective = on_art_raw & np.isfinite(ti_art) & ((ti - ti_art) >= steps_eff)
        n_on_art_effective = int(effective.sum())

        # Cascade proportions (guard against div-zero)
        prop_dx  = n_diagnosed / n_infected  if n_infected  > 0 else np.nan
        prop_art = n_on_art    / n_diagnosed if n_diagnosed > 0 else np.nan
        prop_eff = n_on_art_effective / n_on_art if n_on_art > 0 else np.nan

        r = self.results
        r.prop_diagnosed[ti]      = prop_dx
        r.prop_diag_on_art[ti]    = prop_art
        r.prop_art_effective[ti]  = prop_eff
        r.n_undiagnosed[ti]       = n_undiag
        r.n_diag_not_on_art[ti]   = n_diag_not_on_art
        r.n_on_art_effective[ti]  = n_on_art_effective
        r.n_post_art[ti]          = n_post_art

        # Paper B Fig 1B: 15-64 aggregates (source is people.age; we filter
        # to alive agents via auids).
        people = sim.people
        auids  = people.auids
        ages_alive = np.asarray(people.age.raw)[auids]
        female_alive = np.asarray(people.female.raw)[auids]
        infected_alive = np.asarray(infected.raw)[auids]
        band_15_64 = (ages_alive >= 15) & (ages_alive < 65)
        r.n_alive_15_64[ti]    = int(band_15_64.sum())
        r.n_infected_15_64[ti] = int((band_15_64 & infected_alive).sum())

        # Paper B Fig 2B: mean age at acquisition, by sex.
        # `ti_infected == ti` marks agents newly infected this step. Filter
        # to alive agents so we don't include historical/dead uids.
        ti_infected_alive = np.asarray(hiv.ti_infected.raw)[auids]
        newly_infected = ti_infected_alive == ti
        r.new_infections_15_64[ti] = int((newly_infected & band_15_64).sum())
        newly_f = newly_infected & female_alive
        newly_m = newly_infected & ~female_alive
        r.n_new_inf_f[ti]        = int(newly_f.sum())
        r.n_new_inf_m[ti]        = int(newly_m.sum())
        r.age_sum_new_inf_f[ti]  = float(ages_alive[newly_f].sum())
        r.age_sum_new_inf_m[ti]  = float(ages_alive[newly_m].sum())

        # Transmission attribution: sources that transmitted at this step.
        # `ti_transmitted_sex` is set to the current ti for each source that
        # infected >=1 partner sexually this step; `new_transmissions_sex`
        # holds the count of transmissions each source produced.
        just_transmitted = np.asarray(hiv.ti_transmitted_sex.raw) == ti
        n_trans_per_src  = np.asarray(hiv.new_transmissions_sex.raw)

        if just_transmitted.any():
            diagnosed_raw = np.asarray(diagnosed.raw)
            on_art_r      = on_art_raw
            post_art_r    = np.asarray(post_art.raw)

            mask_undx    = just_transmitted & ~diagnosed_raw
            mask_diag_no = just_transmitted &  diagnosed_raw & ~on_art_r & ~post_art_r
            mask_on_art  = just_transmitted &  on_art_r
            mask_post    = just_transmitted &  post_art_r & ~on_art_r

            r.new_trans_undiagnosed[ti]     = n_trans_per_src[mask_undx].sum()
            r.new_trans_diag_not_on_art[ti] = n_trans_per_src[mask_diag_no].sum()
            r.new_trans_on_art[ti]          = n_trans_per_src[mask_on_art].sum()
            r.new_trans_post_art[ti]        = n_trans_per_src[mask_post].sum()
