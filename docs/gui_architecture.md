# GUI Architecture & Folder Structure

## Architectural Overview

The `gui/` directory implements a Layered Architecture with a Model-Presenter-View (MVP) presentation layer. Due to the event-driven nature of Qt (via Signals and Slots), a pure MVP structure is adapted to accommodate multithreading and high modularity.

The application is organized into three core layers:

* **Presentation Layer (`views/`, `widgets/`, `backend/`, `frontend.py`)**: Structured around the MVP pattern. The `backend/` folder acts as the presenter layer to keep the user interface code clean and separate from core logic.
* **Concurrency/Service Layer (`workers/`)**: Serves as a multithreading buffer layer. Because Qt handles UI operations on a single main thread, long-running and CPU-intensive tasks are offloaded to this layer to prevent interface freezing.
* **Domain/Core Layer (`core/`)**: Contains pure, framework-agnostic business logic. This code operates independently of Qt, meaning the calculation engines could theoretically run via a Command Line Interface (CLI) or a completely different GUI framework.

```text
└── gui/
    ├── backend/          # Presenters: Orchestrate UI state and spawn background workers
    ├── core/             # Domain Layer: Framework-agnostic business logic and engines
    ├── templates/        # Report templates (Jinja2, DOCX) for ergonomic scoring
    ├── theme/            # Styling: Centralized QSS stylesheets and theme logic
    ├── utils/            # Shared utilities, constants, and data models
    ├── views/            # Windows: Main and secondary UI windows (Views)
    ├── widgets/          # Componentry: Reusable UI widgets embedded within Views
    ├── workers/          # Concurrency: CPU-intensive tasks executed on background QThreads
    ├── frontend.py       # Main Application Window (MainWindow View)
    └── __init__.py

```

---

## Architectural Components & Data Flow

### 1. Views (`views/`, `widgets/`, and `frontend.py`)

Views are strictly responsible for user interface layout and presentation logic.

* **`frontend.py`**: Defines the `MainWindow`, which acts as the main application interface. It connects to the `ErgoBackend` via direct dependency injection of the backend into the window.
* **`views/`**: Contains secondary windows, such as `ReportView`. Each window houses one or more widgets and establishes a 1-on-1, bidirectional connection with its corresponding backend (Presenter) using Qt Signals and Slots.
* **`widgets/`**: Contains reusable UI component blocks utilized by the larger views.

> **Architectural Debt Note:** Widgets are intended to contain only visual presentation logic. Currently, the charting widgets handle some calculations and business logic that should be shifted to a specialized worker. Additionally, certain components like the `VideoCanvas` communicate directly with background workers; this will be refactored in a future update to maintain a strict separation of concerns.

### 2. Presenters (`backend/`)

The `backend/` folder contains the Presenters, referred to as backends in this codebase. They manage presentation state and link the user interface to background processes.

* **`backend.py` (`ErgoBackend`)**: Drives the main window state.
* **`report_backend.py` (`ReportBackend`)**: Manages data flow and events for the `ReportView` in a 1-on-1 bidirectional connection.
* Both backends and views manage UI state changes and coordinate event routing with background workers.

### 3. Concurrency Layer (`workers/`)

The `workers/` folder contains classes designed to handle heavy, CPU-bound operations without locking up the user interface.

* Presenters manage these background processes by spawning and maintaining a dedicated `QThread` for each running worker.
* **`video_worker.py`**: Directs video tracking logic including operations like play, pause, and seek.
* **`frames_export_worker.py`**: Runs file I/O heavy processes to extract and export individual frames from video files.

### 4. Domain Layer (`core/`)

The `core/` folder encompasses core computational logic and standalone business classes. It contains zero dependencies on the Qt framework.

* **`analysis_engine.py`**: The primary calculation engine running ergonomic assessments.
* **`calculators_adapter.py`**: Formates and adapts data structures across different scoring variants like REBA and RULA.
* **`report_strategies.py`**: Uses a true Strategy Pattern to adjust and format generated report files depending on the active assessment score type.
* **`session_manager.py`**: Secures data alignment and application consistency across active workflows.

> **Session Definition:** A session refers to a distinct recording and analysis workflow. It is generated when one or more videos are processed in FreeMoCap (referred to as a `recording_session`), which outputs the raw motion capture data. The `SessionManager` ensures the application simultaneously reviews matching files (CSVs, joint angles, landmarks, videos) belonging to that exact same run, preventing data mismatches such as viewing one video while reading data tables from an entirely different session.

### 5. Templates (`templates/`)

Stores static layout documents and template files used to build end-user reports.

* **`REBA_report_template.docx`**: Word document layout for REBA data.
* **`REBA_report.j2`**: Jinja2 sheets used for rendering data out to HTML, PDF, or Word files. Currently covers the REBA format.

### 6. Support Layers (`theme/` & `utils/`)

* **`theme/`**: Manages UI look-and-feel using helper utilities alongside a central QSS (Qt Style Sheet) configuration file.
* **`utils/`**: Group of modules containing utility classes and shared logic accessed by both presentation views and backend presenters. Unlike `core/` (which is typically accessed only by the backend), `utils/` code is fluidly shared across frontend and backend elements.
* **`app_paths.py` (`ErgoPaths`)**: Houses all directory routing logic and serves as the single source of truth for file system paths across the software application.
* **`constants.py`**: Contains global application variables, classes, and Enums used by the frontend and backend layers (candidate for a future merge with models).
* **`models.py`**: Formulates structured data models and Enums passing through the system's Signals and Slots.
* **`utils.py`**: Helper functions for parsing and formatting strings or file names.

---

## Execution Entry Point

While layout trees and window assets are set up inside `frontend.py`, the core entry point that boots up the application is the root `main.py` file situated in the parent directory alongside the `gui/` folder.

---

## Detailed Directory Blueprint

```text
└── 📁gui
    ├── 📁backend
    │   ├── __init__.py
    │   ├── backend.py                  # ErgoBackend: Presenter for the MainWindow
    │   └── report_backend.py           # ReportBackend: Presenter for the ReportView
    ├── 📁core
    │   ├── __init__.py
    │   ├── analysis_engine.py          # Core calculations engine for ergonomic assessment
    │   ├── calculators_adapter.py      # Data adapters for specific assessment scores (REBA/RULA)
    │   ├── report_strategies.py        # Strategy implementation for report formatting
    │   └── session_manager.py          # Session synchronization and data alignment manager
    ├── 📁templates
    │   ├── REBA_report_template.docx   # Word document blueprint for REBA results
    │   └── REBA_report.j2              # Jinja2 template for HTML/PDF report serialization
    ├── 📁theme
    │   ├── __init__.py
    │   └── style.py                    # Global QSS stylesheet management and theme logic
    ├── 📁utils
    │   ├── __init__.py
    │   ├── app_paths.py                # ErgoPaths: Unified application path routing
    │   ├── constants.py                # Global application constants and Enums
    │   ├── models.py                   # Data models used in Slots and Signals
    │   └── utils.py                    # General text and file formatting utilities
    ├── 📁views
    │   ├── __init__.py
    │   ├── report_view.py              # Secondary View containing Report generation interfaces
    │   └── settings_view.py            # Secondary View containing application configurations [To Be Implemented]
    ├── 📁widgets
    │   ├── __init__.py
    │   ├── chart_report_widget.py      # Statistical graphing component embedded in ReportView
    │   ├── menu_actions.py             # Event mappings for top-level window actions
    │   ├── menu_bar.py                 # Primary window menu bar navigation
    │   ├── sidebar.py                  # Primary window navigation panel
    │   ├── table_report_widget.py      # Tabular data display embedded in ReportView
    │   └── video_canvas.py             # Main video rendering viewport
    ├── 📁workers
    │   ├── __init__.py
    │   ├── frames_export_worker.py     # Asynchronous file writing task for frame extraction
    │   └── video_worker.py             # Asynchronous video decoding, seeking, and playback looping
    ├── __init__.py
    └── frontend.py                     # MainWindow View definition

```

---

© 2026 medlav. Distributed under the AGPL-3.0 License.
