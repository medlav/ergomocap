# Module Info: Calculators

This page is still to be completed, for now is just collecting general info about the calculators in this module as a list.

## Technical Specification

This module integrates six distinct, internationally recognized ergonomic assessment methods. Each method addresses specific risk factors associated with manual labor:

* **REBA (Rapid Entire Body Assessment):** Selected for whole-body postural analysis in dynamic or rapidly changing environments (e.g., healthcare, logistics). It prioritizes sudden changes in posture and unstable loads.
* **RULA (Rapid Upper Limb Assessment):** Selected specifically for sedentary, sedentary-repetitive, or workstation-bound tasks (e.g., office work, static assembly). It focuses heavily on upper extremity strain and neck/trunk positioning.
* **NIOSH Lifting Equation:** Evaluates symmetric and asymmetric manual lifting and lowering tasks. It calculates recommended weight limits based on lift geometry and task frequency to prevent low-back injuries.
* **SNOOK Tables (Liberty Mutual):** Selected to evaluate manual materials handling involving horizontal forces, specifically pushing, pulling, and carrying tasks, which are not covered by the NIOSH lifting equation.
* **OCRA (Occupational Repetitive Actions):** Selected for high-frequency, highly repetitive cycles of the upper limbs. It tracks cumulative mechanical stress, insufficient recovery periods, and force application over complete work shifts.
* **EWAS (Ergonomic Assessment Worksheet):** Evaluates cumulative postural, force, and metabolic strain across an entire work shift.


## Planned System Architecture
Once implemented, each calculator in this module must expose a standardized execution interface identical to the core evaluation classes to maintain compatibility with the gui module.

---

*For development timelines and feature tracking, please refer to the global project roadmap.*