# ErgoMoCap: Ergonomics Motion Capture

**ErgoMoCap** is a local-first Python desktop application that connects computer vision-based motion capture (FreeMoCap) with standardized occupational ergonomic assessments. It features a modular calculation engine for multi-joint risk analysis.

If you want a quick look at the project you can click the badge below to open the **Visual Docs**

<a href="https://medlav.github.io/ergomocap/">
      <img src="https://img.shields.io/badge/Documentation-Visual_Docs-4866cf?style=for-the-badge&logo=readthedocs&logoColor=white" alt="Visual Docs" style="margin: 0 4px;">
</a>

---

## System Architecture

The project is decoupled into two primary domains to isolate technical logic from the user interface.

### 1. The Calculator Domain (`/calculators`)

The biomechanical scoring engine operates independently of the GUI framework. It ingests kinematic data (such as FreeMoCap `joint_angles.csv` files) via domain adapters and maps spatial coordinates to standard ergonomic assessment modules. Supported international standards include REBA, RULA, NIOSH, OCRA, EWAS, and Snook.

For architectural details, see the [Calculators Architecture Docs](calculators/README.md).

### 2. The GUI Interface Domain (`/gui`)

The interface utilizes a Model-Presenter-View (MVP) architecture implemented via PyQt6. It adapts standard MVP paradigms to support Qt's asynchronous, event-driven architecture (Signals and Slots), multithreading, and independent data pipeline processing.

For user interface details, see the [GUI Architecture Docs](gui_architecture.md).

---

## Project Structure

```text
ergomocap/
├── calculators/           # Validated Biomechanical Logic
│   ├── adapters/          # Data Mapping (MoCap & Force sensors)
│   ├── ewas_calculator/   # EWAS Standard Implementation
│   ├── niosh_calculator/  # RNLE Lifting Equation
│   ├── ocra_calculator/   # Repetitive Task Analysis
│   ├── reba_calculator/   # Full Body Assessment (Sub-module based)
│   ├── rula_calculator/   # Upper Limb Assessment
│   └── snook_calculator/  # Snook & Ciriello Tables
├── gui/                   # PyQt6 Desktop Application
│   ├── backend/           # Presenters: UI State Orchestration & Worker Lifecycles
│   ├── core/              # Domain Layer: Independent Engine & Session Management
│   ├── templates/         # Report Document Blueprints (Jinja2 & DOCX Templates)
│   ├── theme/             # Styling & Look-and-Feel (style.py & QSS)
│   ├── utils/             # Shared App Paths, Data Models, and Constants
│   ├── views/             # Dumb Windows/Screens (ReportView, SettingsView)
│   └── widgets/           # Reusable UI Elements (VideoCanvas, Sidebars, Charts)
├── intl/                  # i18n Translation Layer (Generated TS for Italian)
├── tests/                 # Mirror-Tree Test Suite
│   ├── calculators/       # Unit tests for core mathematical logic
│   ├── gui/               # Component, Presenter, and Integration tests
│   └── e2e/               # Full system data pipeline validation
└── main.py                # Main Application Entry Point

```

---

## Quality Assurance & Verification

* **Mirror Testing**: Test modules are organized using a mirror-tree hierarchy, where each source file has a corresponding `_test.py` file in the equivalent sub-path within `/tests`.
* **Audit Documentation**: Individual calculator packages contain an `audit.md` file mapping mathematical functions directly to reference tables in peer-reviewed ergonomic literature.
* **Coverage Verification**: Automated workflows generate tracking metrics (`coverage.svg` and `interrogate_badge.svg`) stored in the assets directory.

Read the main README.md file for more info [README](https://medlav.github.io/ergomocap/README.md)

---

## Technical Roadmap

The software is currently in a pre-alpha state (v0.0.X). Breaking changes to the API and architecture will occur frequently until the release of the first stable milestones:

* **v0.1 (Alpha Release):** Establishment of the definitive, maintainable architecture. Integration of baseline functionality for all core calculators.
* **v0.2 (Beta Release):** Verification of calculation accuracy and stability. The system will be considered ready for production use in academic and professional ergonomic research.

Refer to the [Ergomocap Roadmap](roadmap.md) for development milestones.

---

© 2026 medlav. Distributed under the AGPL-3.0 License.