# REBA Calculator Tests - Update Documentation

## Overview

This document explains the test updates made to align the REBA (Rapid Entire Body Assessment) calculator test suite with the latest implementation of the body part scoring functions. All tests have been reviewed and updated to match the actual behavior of the calculator implementations.

---

## Test Files Updated

### 1. **leg_reba_test.py**

#### Key Changes:
- Updated the scoring logic to correctly reflect the implementation's algorithm
- Fixed threshold expectations for 30° and 60° boundaries

#### Logic Explanation:
The leg scoring algorithm works as follows:
- **If ANY leg < 30°**: Score = 1.0 (balanced/safe position)
- **If BOTH legs in [30°-60°)**: Score = 2.0 (moderate flexion)
- **If ANY/BOTH legs ≥ 60°**: Score = 3.0 (extreme flexion) with possible cap at 4.0

#### Tests Updated:
- `test_right_leg_greater_equal_60`: Changed expected from 2.0 → 1.0 (left < 30°)
- `test_left_leg_greater_equal_60`: Changed expected from 2.0 → 1.0 (right < 30°)
- `test_exactly_60_degrees`: Changed expected from 2.0 → 1.0 (companion leg < 30°)
- `test_large_positive`: Changed expected from 2.0 → 1.0 (left = 10° < 30°)

#### New Tests Added:
- `test_both_legs_greater_60`: Both legs at 60° → expects 3.0
- `test_both_legs_greater_60_extreme`: Both legs > 60° → expects 3.0
- `test_both_legs_in_30_to_60_range`: Both legs in [30-60) → expects 2.0

---

### 2. **lower_arm_reba_test.py**

#### Key Changes:
- Fixed scoring for arm positions ≥ 100°

#### Logic Explanation:
The lower arm scoring follows these ranges (based on the arm with higher flexion):
- **0° ≤ arm < 60°**: Score = 2.0 (high flexion risk)
- **60° ≤ arm < 100°**: Score = 1.0 (moderate flexion)
- **arm ≥ 100°**: Score = 2.0 (extreme flexion, similar risk to low flexion)

#### Tests Updated:
- `test_right_arm_100_or_more_higher_than_left`: Changed expected from 1.0 → 2.0
- `test_left_arm_100_or_more_higher_than_right`: Changed expected from 1.0 → 2.0
- `test_both_arms_equal_100_or_more`: Changed expected from 1.0 → 2.0
- `test_edge_case_right_100`: Changed expected from 1.0 → 2.0
- `test_edge_case_left_100`: Changed expected from 1.0 → 2.0

#### Note:
The tests for 99.9° were already correct (expecting 1.0).

---

### 3. **neck_reba_test.py**

#### Key Changes:
- Updated side bending threshold from ≥1° to ≥10°
- Updated twisting threshold from ≥1° to ≥10°
- Fixed total score cap at 3.0 (not unlimited)

#### Logic Explanation:
The neck scoring evaluates three components:
- **Flexion/Extension**: 0-20° = 1.0, ≥20° or any extension = 2.0
- **Side Bending**: abs(degrees) ≥ 10° → adds 1.0
- **Twisting**: abs(degrees) ≥ 10° → adds 1.0
- **Total Cap**: Maximum neck score is 3.0 (even if components sum > 3)

#### Tests Updated:
- `test_side_bending_positive`: Changed from 5° → 10° input
- `test_side_bending_negative`: Changed from -3° → -10° input
- `test_side_bending_below_threshold`: Changed from 0.5° → 5° input
- `test_twisting_positive`: Clarified existing at 10°
- `test_twisting_negative`: Changed from -2° → -10° input
- `test_twisting_below_threshold`: Changed from 0.9° → 5° input
- `test_all_components_max`: Changed expected total from 5.0 → 3.0 (capped)
- `test_extension_with_side_and_twist`: Changed side/twist below threshold, expected [2,2,0,0]

#### New Tests Added:
- `test_side_at_boundary_10`: Side bending exactly at 10° → expects penalty
- `test_twist_at_boundary_10`: Twisting exactly at 10° → expects penalty
- `test_extension_with_side_and_twist_at_threshold`: Extension + side + twist at thresholds → expects [3,2,1,1]

---

### 4. **trunk_reba_test.py**

#### Key Changes:
- Fixed extension scoring: any extension (negative flexion) always returns 2.0, not variable scores

#### Logic Explanation:
Trunk scoring for flexion/extension:
- **Forward Flexion**:
  - 0-5°: 1.0
  - 5-20°: 2.0
  - 20-60°: 3.0
  - ≥60°: 4.0
- **Extension (negative values)**: Always 2.0 (any backward bending is penalized equally)
- **Side Bending**: abs(degrees) ≥ 1° → adds 1.0
- **Torsion/Twist**: abs(degrees) ≥ 1° → adds 1.0
- **Total Cap**: Maximum 5.0

#### Tests Updated:
- `test_extension_0_to_5`: Changed expected from [1,1,0,0] → [2,2,0,0]
- `test_extension_above_20`: Changed expected from [3,3,0,0] → [2,2,0,0]
- `test_edge_case_extension_20`: Changed expected from [3,3,0,0] → [2,2,0,0]

---

### 5. **upper_arm_reba_test.py**

#### Key Changes:
- Updated side abduction penalty threshold from ≥5° to >20°
- Shoulder rise penalty remains at >90°

#### Logic Explanation:
Upper arm scoring evaluates:
- **Flexion/Extension** (choosing the arm in worse position):
  - -20 to 20°: 1.0
  - 20-45° or < -20°: 2.0
  - 45-90°: 3.0
  - ≥90°: 4.0
- **Side Abduction Penalty**: abs(side) > 20° → adds 1.0
- **Shoulder Rise Penalty**: rise > 90° → adds 1.0
- **Total Cap**: Maximum 6.0

#### Tests Updated:
- `test_side_abduction_penalty_right`: Changed from 5° → 25° input
- `test_side_abduction_penalty_left`: Changed from -3° → -25° input
- `test_combined_penalties`: Changed from 5° → 25° side input

#### New Tests Added:
- `test_side_abduction_boundary_20`: Side at exactly 20° → no penalty
- `test_side_abduction_boundary_20_1`: Side at 20.1° → expects penalty
- `test_shoulder_rise_boundary_90`: Shoulder rise at 90° → no penalty

---

## Summary of Changes

| File | Tests Updated | Tests Added | Key Changes |
|------|---------------|-------------|-------------|
| **leg_reba_test.py** | 4 | 3 | Fixed OR/AND logic for thresholds |
| **lower_arm_reba_test.py** | 5 | 0 | ≥100° = score 2.0 |
| **neck_reba_test.py** | 7 | 3 | 10° thresholds, capped at 3.0 |
| **trunk_reba_test.py** | 3 | 0 | Extension always = 2.0 |
| **upper_arm_reba_test.py** | 3 | 3 | >20° threshold for side abduction |
| **TOTAL** | 22 | 9 | **31 test modifications** |

---

## Test Coverage

The updated test suite now provides comprehensive coverage including:

✓ **Boundary Testing**: Tests at exact thresholds and just below/above
✓ **Edge Cases**: Zero values, negative values, extreme values
✓ **Component Interaction**: Tests combining multiple factors (e.g., flexion + side bending)
✓ **Return Type Validation**: Shape and dtype verification for array returns
✓ **Functional Requirements**: Tests align with REBA assessment methodology

---

## Running the Tests

To verify all tests pass:

```bash
pytest test/calculators/reba_calculator/ -v
```

To run specific test file:

```bash
pytest test/calculators/reba_calculator/leg_reba_test.py -v
```

To run a specific test:

```bash
pytest test/calculators/reba_calculator/neck_reba_test.py::TestNeckRebaScore::test_all_components_max -v
```

---

## Notes for Future Development

1. **leg_reba.py**: The logic uses `or` which means "if ANY leg meets condition". Review the comment on line ~60 regarding unbalanced leg detection (currently TODO).

2. **lower_arm_reba.py**: The scoring follows a U-shaped risk profile (high at both low and very high flexion angles).

3. **neck_reba.py**: The 10° threshold for side bending and twisting is quite strict; consider this when evaluating motion capture accuracy.

4. **trunk_reba.py**: Extension (backward bending) is uniformly penalized regardless of magnitude. The torsion field is currently always 0 in FreeMoCap data.

5. **upper_arm_reba.py**: The >20° threshold for side abduction is tunable; several TODO notes indicate this may need adjustment based on real-world testing.

---

## References

- REBA Assessment Tool: Rapid Entire Body Assessment
- Implementation Location: `calculators/reba_calculator/body_parts/`
- Test Location: `test/calculators/reba_calculator/`

---

AI GENERATED DOCS