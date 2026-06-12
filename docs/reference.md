# API Reference

This page provides the technical documentation for all ErgoMoCap modules, automatically extracted from the source code docstrings.

Check the Source Code on GitHub: [Official Repo](https://github.com/medlav/ergomocap) | Structural details are accessible at the [GUI Architecture Documentation](gui_architecture.md).

---

## Core Calculators

These modules contain the mathematical logic for the ergonomic assessment standards.

### REBA (Rapid Entire Body Assessment)

The REBA engine is divided into specific body part modules to calculate localized scores.

**Main Calculator Engine**
::: calculators.reba_calculator.REBA_calculator
  options:
    heading_level:  4

**Body Part Sub-modules**
::: calculators.reba_calculator.body_parts.leg_reba
  options:
    heading_level: 4
::: calculators.reba_calculator.body_parts.lower_arm_reba
  options:
    heading_level:  4
::: calculators.reba_calculator.body_parts.neck_reba
  options:
    heading_level:  4
::: calculators.reba_calculator.body_parts.trunk_reba
  options:
    heading_level:  4
::: calculators.reba_calculator.body_parts.upper_arm_reba
  options:
    heading_level:  4
::: calculators.reba_calculator.body_parts.wrist_reba
  options:
    heading_level:  4

**Internal Tables**
::: calculators.reba_calculator.reba_score_tables
  options:
    heading_level:  4

---

### RULA (Rapid Upper Limb Assessment)

The RULA engine extracts scoring bounds from dedicated body layouts and internal mapping grids.

::: calculators.rula_calculator.RULA_calculator
  options:
    heading_level:  4

::: calculators.rula_calculator.rula_body_parts
  options:
    heading_level:  4

::: calculators.rula_calculator.rula_score_tables
  options:
    heading_level:  4

---

### NIOSH, OCRA, & Specialized Engines

::: calculators.niosh_calculator.NIOSH_calculator
  options:
    heading_level:  3

::: calculators.ocra_calculator.OCRA_calculator
  options:
    heading_level:  3

::: calculators.ewas_calculator.EWAS_calculator
  options:
    heading_level:  3

::: calculators.snook_calculator.SNOOK_calculator
  options:
    heading_level:  3

---

### Calculator Global Utilities

::: calculators.calculators
  options:
    show_root_heading: true
    heading_level: 3

::: calculators.calculators_utils.conversion_utils
  options:
    show_root_heading: true
    heading_level:  3

::: calculators.calculators_utils.constants
  options:
    show_root_heading: true
    heading_level:  3

---

## Data Adapters

Adapters responsible for converting raw sensor, computer vision tracking, or force metrics into calculator-ready formats.

::: calculators.adapters.freemocap_adapter
  options:
    show_root_heading: true
    heading_level:  3

::: calculators.adapters.force_adapter
  options:
    show_root_heading: true
    heading_level:  3

---

## GUI & Layered Architecture System

Detailed component definitions across Presentation, Domain, and Asynchronous Worker execution paths.

### Domain Core Logic

::: gui.core.analysis_engine
  options:
    show_root_heading: true

::: gui.core.session_manager
  options:
    show_root_heading: true

::: gui.core.calculators_adapter
  options:
    show_root_heading: true

::: gui.core.report_strategies
  options:
    show_root_heading: true

### Presenters (MVP Coordination)

::: gui.backend.backend
  options:
    show_root_heading: true

::: gui.backend.report_backend
  options:
    show_root_heading: true

::: gui.backend.review_backend
  options:
    show_root_heading: true

### Asynchronous Concurrency Workers

::: gui.workers.analysis_worker
  options:
    show_root_heading: true


::: gui.workers.video_worker
  options:
    show_root_heading: true

::: gui.workers.frames_export_worker
  options:
    show_root_heading: true

### Passive Views & Reusable UI Components

::: gui.frontend
  options:
    show_root_heading: true

::: gui.views.report_view
  options:
    show_root_heading: true

::: gui.views.review_view
  options:
    show_root_heading: true

::: gui.views.settings_view
  options:
    show_root_heading: true

::: gui.widgets.sidebar
  options:
    show_root_heading: true

::: gui.widgets.video_canvas
  options:
    show_root_heading: true

::: gui.widgets.table_report_widget
  options:
    show_root_heading: true

::: gui.widgets.chart_report_widget
  options:
    show_root_heading: true

::: gui.widgets.review_metrics_table
  options:
    show_root_heading: true

::: gui.widgets.menu_bar
  options:
    show_root_heading: true

::: gui.widgets.menu_actions
  options:
    show_root_heading: true

---

## Utilities & Internationalization

::: gui.theme.style
  options:
    show_root_heading: true

::: gui.utils.utils
  options:
    show_root_heading: true

::: gui.utils.app_paths
  options:
    show_root_heading: true

::: gui.utils.constants
  options:
    show_root_heading: true

::: gui.utils.models
  options:
    show_root_heading: true

::: intl.update_intl
  options:
    show_root_heading: true

---

## Main Entry Point

::: main
  options:
    show_root_heading: true

---

© 2026 medlav. Distributed under the AGPL-3.0 License.