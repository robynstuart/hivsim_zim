"""
Prior distributions for the Zimbabwe HIV calibration (HIVsim-only subset).

Format: {column_name: (label, low, high, log_scale)}.

These are the HIV-relevant priors extracted from the joint HIV + STI
calibration in the sti_notification project (experiment 06, 500-draw
LHS with K=5 sim-averaging on stisim fix/ng-tx@731bc1d). Structural
network parameters (prop_f0, m2_conc, dur_sw) are retained because
they materially affect HIV transmission. The full joint prior set,
including syph and NG/CT/TV priors, lives in the sti_notification repo.
"""

import sciris as sc


calib_pars = sc.objdict({
    'hiv.beta_m2f':                 ('HIV beta (M->F)',           0.005, 0.04, False),
    'hiv.rel_init_prev':            ('HIV rel init prev',         0.3,   1.5,  False),
    'hiv.dur_on_art':               ('Mean dur on ART (yrs)',     8,     25,   False),
    'hiv.rel_death':                ('HIV death scale',           0.5,   2.5,  False),
    'hiv.rel_death_on_art':         ('HIV death scale (on ART)',  0.1,   2.0,  False),
    'structuredsexual.prop_f0':     ('Prop F low-risk',           0.55,  0.90, False),
    'structuredsexual.m2_conc':     ('M2 concurrency',            2.0,   8.0,  False),
    'structuredsexual.dur_sw':      ('FSW duration (yrs)',        2,     15,   False),
})
