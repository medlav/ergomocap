# Repository Quality Checklist

## 1/5 Core Logic & Functionality

* [ ] **Calculator Validation:** Verify mathematical formulas for edge cases (division by zero, float overflows).
* [ ] **Type Consistency:** Validate and cast inputs using Pylance static analysis.
* [ ] **Error Handling:** Implement descriptive exceptions instead of letting core logic crash.
* [ ] **Redundancy Check:** Refactor calculation logic to eliminate duplicate code (DRY).

## 2/5 Testing

* [ ] **Unit Tests:** Implement tests for all core calculator functions.
* [ ] **Edge Case Coverage:** Test against empty inputs, null values, and extreme boundaries.
* [ ] **Integration Tests:** Verify pipeline dataflow across separate modules.
* [ ] **Coverage Report:** Maintain test coverage reporting via `pytest-cov`.

## 3/5 Documentation (MkDocs & MkDocstrings)

* [ ] **Docstring Completeness:** Write Google-style docstrings for `mkdocstrings` parsing.
* [ ] **Type Hinting:** Add PEP 484 type hints to function signatures for IDE and auto-doc support.
* [ ] **MkDocs Configuration:**
* [ ] Validate navigation hierarchy in `mkdocs.yml`.
* [ ] Standardize note callouts using MkDocs Admonitions (`!!! info`, `!!! warning`).
* [ ] Fix broken internal Markdown links.


* [ ] **README.md:** Document installation and quick-start instructions on the main landing page.

## 4/5 Code Quality & Maintenance

* [ ] **Linting:** Run `ruff` for static analysis and formatting compliance.
* [ ] **Auto-formatting:** Format code with `black`.
* [ ] **Dependencies:** Consolidate and update dependencies in `pyproject.toml` (drop `requirements.txt`).

## 5/5 Deployment / CI

* [ ] **Pre-commit Hooks:** Register hooks locally via `pre-commit install` to block invalid commits.
* [ ] **Security Scans:** Run `bandit` via the pre-commit pipeline using rules defined in `pyproject.toml`.
* [ ] **Docstring Compliance:** Run `interrogate` and `pydoclint` hooks to to check docstring formatting and coverage.
* [ ] **License Tracking:** Auto-generate third-party dependency licenses into `CREDITS.md` using `pip-licenses`.
* [ ] **Task Centralization:** Parse code comments to update the root `TODO.md` file using `todo_scanner.py`.
* [ ] **Dynamic Metrics Badges:** Automate SVG status generation using `anybadge` and `coverage-badge` on successful runs.
* [ ] **GitHub Actions Cloud CI:** Configure automated test execution, matrix verification, and documentation site deployment on **Python 3.12.10** runners via `.github/workflows/audit.yml`.
* [ ] **Version Tagging:** Synchronize the active documentation release version badge dynamically via `pyproject.toml`.


# ErgoMoCap Development Progress

| File Path | Logic | Tests | Docs (MkDocs) | Types | Integration |
| --- | --- | --- | --- | --- | --- |
| **Root** |  |  |  |  |  |
| `main.py` | [ ] | [ ] | [ ] | [ ] | [ ] |
| **Calculators (Core)** |  |  |  |  |  |
| `calculators/calculators.py` | [ ] | [ ] | [ ] | [ ] | [ ] |
| `calculators/adapters/force_adapter.py` | [ ] | [ ] | [ ] | [ ] | [ ] |
| `calculators/adapters/freemocap_adapter.py` | [ ] | [ ] | [ ] | [ ] | [ ] |
| `calculators/calculators_utils/constants.py` | [ ] | [ ] | [ ] | [ ] | [ ] |
| `calculators/calculators_utils/conversion_utils.py` | [ ] | [ ] | [ ] | [ ] | [ ] |
| `calculators/ewas_calculator/EWAS_calculator.py` | [ ] | [ ] | [ ] | [ ] | [ ] |
| `calculators/niosh_calculator/NIOSH_calculator.py` | [ ] | [ ] | [ ] | [ ] | [ ] |
| `calculators/ocra_calculator/OCRA_calculator.py` | [ ] | [ ] | [ ] | [ ] | [ ] |
| `calculators/rula_calculator/RULA_calculator.py` | [ ] | [ ] | [ ] | [ ] | [ ] |
| `calculators/rula_calculator/rula_body_parts.py` | [ ] | [ ] | [ ] | [ ] | [ ] |
| `calculators/rula_calculator/rula_score_tables.py` | [ ] | [ ] | [ ] | [ ] | [ ] |
| `calculators/snook_calculator/SNOOK_calculator.py` | [ ] | [ ] | [ ] | [ ] | [ ] |
| **REBA Specialized** |  |  |  |  |  |
| `calculators/reba_calculator/REBA_calculator.py` | [ ] | [ ] | [ ] | [ ] | [ ] |
| `calculators/reba_calculator/reba_score_tables.py` | [ ] | [ ] | [ ] | [ ] | [ ] |
| `calculators/reba_calculator/body_parts/leg_reba.py` | [ ] | [ ] | [ ] | [ ] | [ ] |
| `calculators/reba_calculator/body_parts/lower_arm_reba.py` | [ ] | [ ] | [ ] | [ ] | [ ] |
| `calculators/reba_calculator/body_parts/neck_reba.py` | [ ] | [ ] | [ ] | [ ] | [ ] |
| `calculators/reba_calculator/body_parts/trunk_reba.py` | [ ] | [ ] | [ ] | [ ] | [ ] |
| `calculators/reba_calculator/body_parts/upper_arm_reba.py` | [ ] | [ ] | [ ] | [ ] | [ ] |
| `calculators/reba_calculator/body_parts/wrist_reba.py` | [ ] | [ ] | [ ] | [ ] | [ ] |
| **GUI Backend** |  |  |  |  |  |
| `gui/backend/backend.py` | [ ] | [ ] | [ ] | [ ] | [ ] |
| `gui/backend/report_backend.py` | [ ] | [ ] | [ ] | [ ] | [ ] |
| `gui/core/analysis_engine.py` | [ ] | [ ] | [ ] | [ ] | [ ] |
| `gui/core/calculators_adapter.py` | [ ] | [ ] | [ ] | [ ] | [ ] |
| `gui/core/report_strategies.py` | [ ] | [ ] | [ ] | [ ] | [ ] |
| `gui/core/session_manager.py` | [ ] | [ ] | [ ] | [ ] | [ ] |
| `gui/workers/frames_export_worker.py` | [ ] | [ ] | [ ] | [ ] | [ ] |
| `gui/workers/video_worker.py` | [ ] | [ ] | [ ] | [ ] | [ ] |
| **GUI Frontend & Theme** |  |  |  |  |  |
| `gui/frontend.py` | [ ] | [ ] | [ ] | [ ] | [ ] |
| `gui/theme/style.py` | [ ] | [ ] | [ ] | [ ] | [ ] |
| `gui/views/report_view.py` | [ ] | [ ] | [ ] | [ ] | [ ] |
| `gui/views/settings_view.py` | [ ] | [ ] | [ ] | [ ] | [ ] |
| `gui/widgets/chart_report_widget.py` | [ ] | [ ] | [ ] | [ ] | [ ] |
| `gui/widgets/menu_actions.py` | [ ] | [ ] | [ ] | [ ] | [ ] |
| `gui/widgets/menu_bar.py` | [ ] | [ ] | [ ] | [ ] | [ ] |
| `gui/widgets/sidebar.py` | [ ] | [ ] | [ ] | [ ] | [ ] |
| `gui/widgets/table_report_widget.py` | [ ] | [ ] | [ ] | [ ] | [ ] |
| `gui/widgets/video_canvas.py` | [ ] | [ ] | [ ] | [ ] | [ ] |
| `gui/utils/app_paths.py` | [ ] | [ ] | [ ] | [ ] | [ ] |
| `gui/utils/constants.py` | [ ] | [ ] | [ ] | [ ] | [ ] |
| `gui/utils/models.py` | [ ] | [ ] | [ ] | [ ] | [ ] |
| `gui/utils/utils.py` | [ ] | [ ] | [ ] | [ ] | [ ] |
| **Internationalization** |  |  |  |  |  |
| `intl/update_intl.py` | [ ] | [ ] | [ ] | [ ] | [ ] |
| `scripts/todo_scanner.py` | [ ] | [ ] | [ ] | [ ] | [ ] |

---

### Matrix Definitions:

* **Logic:** Formulations validated and edge cases handled.
* **Tests:** Target unit tests implemented in `tests/`.
* **Docs:** Google-style docstrings present and valid.
* **Types:** Function signatures include explicit PEP 484 type hints.
* **Integration:** Verified end-to-end execution across CLI and GUI runtimes.

---

© 2026 medlav. Distributed under the AGPL-3.0 License.