# ROADMAP

## Current v0.0.1 (Pre-Alpha)

**Goal:** Fix the core math, clean up the UI, add manual overrides, and lay the foundation for new calculation tools.

* [ ] **Fix REBA & RULA Math:** Verify that the math for REBA and RULA is 100% accurate and matches standard scoring charts.
* [ ] **Test with Real Data:** Set up automated tests with sample data to catch calculation bugs or rounding errors early.
* [ ] **Fix Crashes & Logs:** Move logging to an asynchronous setup and fix race conditions causing background task crashes.
* [ ] **Clean Up PyQt6 UI:** Remove broken buttons and placeholder menus. Fully implement the global Settings page and finish the live data dashboard.
* [ ] **Add Manual Overrides:** Allow users to manually input Force/Load values and save these inputs to the session.
* [ ] **Refactor Code Architecture:** Clean up the base calculator code to make it easy for developers to integrate new tools later.

## v0.1.0 (Alpha)

**Goal:** Establish a stable core and GUI while adding new ergonomic calculation engines.

* [ ] **Stable Core and GUI:** Complete an audit of the core engine and interface to fix remaining bugs and stabilize operations.
* [ ] **Add NIOSH Lifting Engine:** Integrate the NIOSH Lifting Equation to handle complex, multi-task lifting calculations.
* [ ] **Add OCRA Index:** Build out the tools for the Occupational Repetitive Actions index and checklists.
* [ ] **Add Snook & EWAS Tables:** Implement EWAS and Snook tables for pushing, pulling, and carrying operations using array-based lookups.

---

## v0.2.0 (Beta)

**Goal:** Conduct thorough real-world QA testing, resolve edge-case bugs, and optimize calculation speeds.

* [ ] **Bug Fixes:** Identify and resolve user-facing bugs and interface inconsistencies.
* [ ] **Real-World QA Testing:** Test application features in real-world settings and update logic based on user feedback.
* [ ] **Numba Optimization:** Use Numba to compile heavy mathematical functions into native machine code for faster execution.
* [ ] **Performance Audit:** Run performance benchmarks on calculation loops using large datasets.

---

## v0.3.0+ (Production)

**Goal:** Continuous bug fixing, performance tuning, and adding minor feature updates only as strictly necessary.

... More to do

## v1.0.0 (Production)

**Goal:** Launch a complete, fully audited, and thoroughly tested standalone tool with minimal external dependencies.

---

### Progress Tracker

| Version | Main Focus | Status |
| --- | --- | --- |
| **v0.0.1 (Pre-Alpha)** | Fix math errors, clean up UI, add manual overrides, and prepare architecture | In Progress |
| **v0.1.0 (Alpha) & v0.2.0 (Beta)** | Stabilize core math and GUI; add NIOSH, OCRA, and Snook packages | Up Next |
| **v1.0.0 (Production)** | Comprehensive standalone tool with minimal dependencies | Planned |

---

### Quality Standards

* **Code Testing:** Maintain at least 90% automated test coverage for all math and calculation code.
* **Code Cleanliness:** Ensure zero errors or security warnings when running `ruff` and `bandit`.
* **Documentation:** Ensure all code documentation strictly passes `pydoclint` checks.

---

© 2026 medlav. Distributed under the AGPL-3.0 License.