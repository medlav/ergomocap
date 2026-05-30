# Ergonomic Analysis Calculators

Index of ErgoMoCap `calculators` module.

---

## Calculators Directory

| Assessment Method | Documentation | Validation Audit | General Info / Guidelines |
| --- | --- | --- | --- |
| **Core Adapters** | [Core Docs](calculators/adapters/docs.md) | [Core Audit](calculators/adapters/audit.md) | N/A |
| **EWAS Calculator** | [EWAS Docs](calculators/ewas_calculator/docs.md) | [EWAS Audit](calculators/ewas_calculator/audit.md) | [Info](calculators/ewas_calculator/info.md) |
| **NIOSH Lifting Equation** | [NIOSH Docs](calculators/niosh_calculator/docs.md) | [NIOSH Audit](calculators/niosh_calculator/audit.md) | [Roadmap](calculators/niosh_calculator/ROADMAP.md) |
| **OCRA Index** | [OCRA Docs](calculators/ocra_calculator/docs.md) | [OCRA Audit](calculators/ocra_calculator/audit.md) | [Info](calculators/ocra_calculator/info.md) | [Roadmap](calculators/ocra_calculator/ROADMAP.md) |
| **REBA** *(Rapid Entire Body Assessment)* | [REBA Docs](calculators/reba_calculator/docs.md) | [REBA Audit](calculators/reba_calculator/audit.md) | [Info](calculators/reba_calculator/info.md) |
| **RULA** *(Rapid Upper Limb Assessment)* | [RULA Docs](calculators/rula_calculator/docs.md) | [RULA Audit](calculators/rula_calculator/audit.md) | [Info](calculators/rula_calculator/info.md) |
| **Snook Tables** *(Liberty Mutual)* | [Snook Docs](calculators/snook_calculator/docs.md) | [Snook Audit](calculators/snook_calculator/audit.md) | [Info](calculators/snook_calculator/info.md) |

---

## Global Resources

* **Overview:** [Calculators Root README](calculators/README.md)
* **Guidelines:** [Global Info Guide](calculators/info.md)
* **Quality Assurance:** [Global Audit Log](calculators/audit.md)

### Internal Utilities

Python backend modules supporting the calculation engine:

* `calculators/calculators_utils/constants.py`: mocap and ergonomicconstants.
* `calculators/calculators_utils/conversion_utils.py`: Functions and matrix utilities for converting motion capture data into joint angles.

---

> **Contribution Note:** To implement a new assessment method, replicate an existing calculator directory structure (e.g., `rula_calculator`), ensure your mathematical formulas are documented cleanly, and add your new module links to this directory table.

---

© 2026 medlav. Distributed under the AGPL-3.0 License.