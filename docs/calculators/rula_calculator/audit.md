# AUDIT: ErgoMoCap RULA Calculator


As of 2026-05-29 (ISO 8601) some values are not included but default value are used:

- muscle_score: int = 0,  -> Underestimate
- force_score: int = 0,   -> Underestimate
- is_arm_supported: bool = False, -> Overestimate
- are_legs_unsupported: bool = False, -> Underestimate


Overall the existing code is cleaner than the REBA calculator wich will need more refractoring

The calculator needs to add the 4 functions/inputs for the 4 values and include those in the real calculation.