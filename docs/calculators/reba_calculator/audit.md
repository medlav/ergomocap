# AUDIT: ErgoMoCap REBA Calculator

date: 2026-05-26 (ISO-8601)

As of now 5/6 body_parts files have some issue to fix that is altering the normal result of REBA score..

and starting from the main **REBA_calculator.py** file:

inside the calculate_frame_reba_from_degs() function

```python
    # TODO adjust for load score
    # If load < 11 lbs. : +0
    # If load 11 to 22 lbs. : +1
    # If load > 22 lbs.: +2
    # Adjust: If shock or rapid build up of force: add +1


    # TODO adjust for coupling/activity score
    # Coupling/Activity Score Adjustments (to be added to Score B):
    # Well fitting Handle and mid rang power grip, good: +0
    # Acceptable but not ideal hand hold or coupling
    # acceptable with another body part, fair: +1
    # Hand hold not acceptable but possible, poor: +2
    # No handles, awkward, unsafe with any body part,
    # Unacceptable: +3
    coupling_score = 0  # Placeholder for coupling/activity score (to be integrated with actual task data)
    adjusted_score_b = score_b + coupling_score

```

## neck_reba.py

Apparently no issues.

## legs_reba.py

### Balance Check

As of now the balance is not checked and count as always stable. BIAS: **UNDERESTIMATION OF RISK**

### TODOs

| **TODO** | [`/calculators/reba_calculator/body_parts/leg_reba.py:68`](/calculators/reba_calculator/body_parts/leg_reba.py) | remove with REBA FIX #1 |
| **TODO** | [`/calculators/reba_calculator/body_parts/leg_reba.py:70`](/calculators/reba_calculator/body_parts/leg_reba.py) | implement a way to chek legs balance |
| **TODO** | [`/calculators/reba_calculator/body_parts/leg_reba.py:89`](/calculators/reba_calculator/body_parts/leg_reba.py) | REBA FIX #1 implement logic here for leg score Balanced/Unbalanced! |

## trunk_reba.py

### Torsion Score is always 0

```python
    trunk_torsion_score = 0

    total: int = trunk_flex_score + trunk_side_score + trunk_torsion_score

```

As of now the trunk_torsion_score is ALWAYS 0. BIAS: **UNDERESTIMATION OF RISK**

### TODOs

```python
    trunk_torsion_degree = trunk_degrees[
            2
        ]  # TODO EFFECTIVELY ALWAYS 0 !! MUST IMPLEMENT IN FMC ADAPTER TO GET REAL VALUES

```

Because in the freemocap_adapter generated degrees `# SPINE_ROTATION_TORSION = 0` and thats because FreeMoCap spine rotation isn't always in base CSV (joint_angles.csv), so it default to 0 check freemocap_adapter.py for implementation

```python
    trunk_torsion_score = 0  # TODO EFFECTIVELY ALWAYS 0 !! MUST IMPLEMENT IN FMC ADAPTER TO GET REAL VALUES

```

| **TODO** | [`/calculators/reba_calculator/body_parts/trunk_reba.py:71`](/calculators/reba_calculator/body_parts/trunk_reba.py) | EFFECTIVELY ALWAYS 0 !! MUST IMPLEMENT IN FMC ADAPTER TO GET REAL VALUES |
| **TODO** | [`/calculators/reba_calculator/body_parts/trunk_reba.py:76`](/calculators/reba_calculator/body_parts/trunk_reba.py) | EFFECTIVELY ALWAYS 0 !! MUST IMPLEMENT IN FMC ADAPTER TO GET REAL VALUES |
| **TODO** | [`/calculators/reba_calculator/body_parts/trunk_reba.py:99`](/calculators/reba_calculator/body_parts/trunk_reba.py) | EFFECTIVELY ALWAYS 0 !! MUST IMPLEMENT IN FMC ADAPTER TO GET REAL VALUES |
| **TODO** | [`/calculators/reba_calculator/body_parts/trunk_reba.py:116`](/calculators/reba_calculator/body_parts/trunk_reba.py) | REBA FIX #2 Find a way to calculate the trunk_torsion_degree or ALERT USER ABOUT THIS.. |

## lower_arm_reba.py

write tests but seems to be working

### TODOs

| **TODO** | [`/calculators/reba_calculator/body_parts/lower_arm_reba.py:42`](/calculators/reba_calculator/body_parts/lower_arm_reba.py) | test numba and activate |
| **TODO** | [`/calculators/reba_calculator/body_parts/lower_arm_reba.py:60`](/calculators/reba_calculator/body_parts/lower_arm_reba.py) | remove or implement this chekc if works with numba |
| **TODO** | [`/calculators/reba_calculator/body_parts/lower_arm_reba.py:71`](/calculators/reba_calculator/body_parts/lower_arm_reba.py) | important test for the degrees as this are calculated from a saggital perspective and the sign can be inconsistent based on the direction of movement or sensor placement. |

## upper_arm_reba.py

### Shoulder Rise Penalty

As of now the shoulder rise degree is always zero, so NO Penalty for shoulder rise > 90° BIAS: **UNDERESTIMATION OF RISK**

Also person_leaning and arm_supported are ALWAYS 0 so the Arm Supported/ Leaning Penalty is 0 BIAS: **UNDERESTIMATION OF RISK**

```python
    # R/L Shoulder rise usually mapped from abduction or separate landmarks
    # degs[12] = 0
    # degs[13] = 0


    right_shoulder_rise = upper_arm_degrees[
        4
    ]  # TODO EFFECTIVELY ALWAYS 0 !! MUST IMPLEMENT IN FMC ADAPTER TO GET REAL VALUES
    left_shoulder_rise = upper_arm_degrees[
        5
    ]  # TODO EFFECTIVELY ALWAYS 0 !! MUST IMPLEMENT IN FMC ADAPTER TO GET REAL VALUES

    arm_supported: bool = False  # TODO EFFECTIVELY ALWAYS FALSE !! MUST IMPLEMENT IN FMC ADAPTER TO GET REAL VALUES
    person_leaning: bool = False  # TODO EFFECTIVELY ALWAYS FALSE !! MUST IMPLEMENT IN FMC ADAPTER TO GET REAL VALUES


    # Arm Supported/ Leaning Penalty
    if arm_supported or person_leaning:
        # TODO EFFECTIVELY ALWAYS 0 !! MUST IMPLEMENT IN FMC ADAPTER TO GET REAL VALUES
        support_leaning_score = -1


        # Shoulder Rise Penalty
    if right_shoulder_rise > 90.0 or left_shoulder_rise > 90.0:
        # TODO EFFECTIVELY ALWAYS 0 !! MUST IMPLEMENT IN FMC ADAPTER TO GET REAL VALUES
        upper_arm_shoulder_rise = 1

```

### TODOs

| **TODO** | [`/calculators/reba_calculator/body_parts/upper_arm_reba.py:78`](/calculators/reba_calculator/body_parts/upper_arm_reba.py) | EFFECTIVELY ALWAYS 0 !! MUST IMPLEMENT IN FMC ADAPTER TO GET REAL VALUES |
| **TODO** | [`/calculators/reba_calculator/body_parts/upper_arm_reba.py:81`](/calculators/reba_calculator/body_parts/upper_arm_reba.py) | EFFECTIVELY ALWAYS 0 !! MUST IMPLEMENT IN FMC ADAPTER TO GET REAL VALUES |
| **TODO** | [`/calculators/reba_calculator/body_parts/upper_arm_reba.py:90`](/calculators/reba_calculator/body_parts/upper_arm_reba.py) | this is almost all WRONG! should check the degrees, now it consider normal position at 0 |
| **TODO** | [`/calculators/reba_calculator/body_parts/upper_arm_reba.py:122`](/calculators/reba_calculator/body_parts/upper_arm_reba.py) | EFFECTIVELY ALWAYS 0 !! MUST IMPLEMENT IN FMC ADAPTER TO GET REAL VALUES |
| **TODO** | [`/calculators/reba_calculator/body_parts/upper_arm_reba.py:125`](/calculators/reba_calculator/body_parts/upper_arm_reba.py) | EFFECTIVELY ALWAYS FALSE !! MUST IMPLEMENT IN FMC ADAPTER TO GET REAL VALUES |
| **TODO** | [`/calculators/reba_calculator/body_parts/upper_arm_reba.py:126`](/calculators/reba_calculator/body_parts/upper_arm_reba.py) | EFFECTIVELY ALWAYS FALSE !! MUST IMPLEMENT IN FMC ADAPTER TO GET REAL VALUES |
| **TODO** | [`/calculators/reba_calculator/body_parts/upper_arm_reba.py:130`](/calculators/reba_calculator/body_parts/upper_arm_reba.py) | EFFECTIVELY ALWAYS 0 !! MUST IMPLEMENT IN FMC ADAPTER TO GET REAL VALUES |
| **TODO** | [`/calculators/reba_calculator/body_parts/upper_arm_reba.py:154`](/calculators/reba_calculator/body_parts/upper_arm_reba.py) | REBA FIX #3 FIX ALL THIS FILE IS A MESS OF COURSE IS THE ONE CAUSING THE MOST PORBLEMS IN MY CALCULATOR!! |

## wrist_reba.py

### Wrist score is MAX 2 (not max 3)

2 scores: wrist_side_bend_score + wrist_torsion_score ARE ALWAYS 0!

```python
    total: int = wrist_flex_score + wrist_side_bend_score + wrist_torsion_score
    wrist_reba_score = min(total, 3)  # Capped at 3 for wrist (as per REBA guidelines)

```

As of now only the wrist_flex_score is changing the basic score from starting value of 1. BIAS: **UNDERESTIMATION OF RISK**

```python
    right_side = wrist_degrees[
        2
    ]  # TODO EFFECTIVELY ALWAYS 0 !! MUST IMPLEMENT IN FMC ADAPTER TO GET REAL VALUES
    left_side = wrist_degrees[
        3
    ]  # TODO EFFECTIVELY ALWAYS 0 !! MUST IMPLEMENT IN FMC ADAPTER TO GET REAL VALUES
    right_twist = wrist_degrees[
        4
    ]  # TODO EFFECTIVELY ALWAYS 0 !! MUST IMPLEMENT IN FMC ADAPTER TO GET REAL VALUES
    left_twist = wrist_degrees[
        5
    ]  # TODO EFFECTIVELY ALWAYS 0 !! MUST IMPLEMENT IN FMC ADAPTER TO GET REAL VALUES



    # Side Bending (Deviation) Penalty
    if (
        right_side != 0.0 or left_side != 0.0
    ):  # TODO EFFECTIVELY ALWAYS 0 !! MUST IMPLEMENT IN FMC ADAPTER TO GET REAL VALUES
        wrist_side_bend_score = 1

    # Torsion (Twist) Penalty
    if (
        right_twist != 0.0 or left_twist != 0.0
    ):  # TODO EFFECTIVELY ALWAYS 0 !! MUST IMPLEMENT IN FMC ADAPTER TO GET REAL VALUES
        wrist_torsion_score = 1

    total: int = wrist_flex_score + wrist_side_bend_score + wrist_torsion_score
    wrist_reba_score = min(total, 3)  # Capped at 3 for wrist (as per REBA guidelines)

```

SHOULD NOTIFY THE USER THAT IS NOT GREATAT WRIST ANGLE CALCULATION.. BUT IT SHOULD BE SIMPLER TO IJMPL;EMNT USING THE HOLISITC MODELS:.

### TODOs

| **TODO** | [`/calculators/reba_calculator/body_parts/wrist_reba.py:74`](/calculators/reba_calculator/body_parts/wrist_reba.py) | EFFECTIVELY ALWAYS 0 !! MUST IMPLEMENT IN FMC ADAPTER TO GET REAL VALUES |
| **TODO** | [`/calculators/reba_calculator/body_parts/wrist_reba.py:77`](/calculators/reba_calculator/body_parts/wrist_reba.py) | EFFECTIVELY ALWAYS 0 !! MUST IMPLEMENT IN FMC ADAPTER TO GET REAL VALUES |
| **TODO** | [`/calculators/reba_calculator/body_parts/wrist_reba.py:80`](/calculators/reba_calculator/body_parts/wrist_reba.py) | EFFECTIVELY ALWAYS 0 !! MUST IMPLEMENT IN FMC ADAPTER TO GET REAL VALUES |
| **TODO** | [`/calculators/reba_calculator/body_parts/wrist_reba.py:83`](/calculators/reba_calculator/body_parts/wrist_reba.py) | EFFECTIVELY ALWAYS 0 !! MUST IMPLEMENT IN FMC ADAPTER TO GET REAL VALUES |
| **TODO** | [`/calculators/reba_calculator/body_parts/wrist_reba.py:105`](/calculators/reba_calculator/body_parts/wrist_reba.py) | EFFECTIVELY ALWAYS 0 !! MUST IMPLEMENT IN FMC ADAPTER TO GET REAL VALUES |
| **TODO** | [`/calculators/reba_calculator/body_parts/wrist_reba.py:111`](/calculators/reba_calculator/body_parts/wrist_reba.py) | EFFECTIVELY ALWAYS 0 !! MUST IMPLEMENT IN FMC ADAPTER TO GET REAL VALUES |
| **TODO** | [`/calculators/reba_calculator/body_parts/wrist_reba.py:128`](/calculators/reba_calculator/body_parts/wrist_reba.py) | SHOULD NOTIFY THE USER THAT IS NOT GREATAT WRIST ANGLE CALCULATION.. BUT IT SHOULD |




---
*For development timelines and feature tracking, please refer to the global project roadmap.*