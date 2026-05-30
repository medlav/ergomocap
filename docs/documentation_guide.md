# ErgoMoCap Documentation Reference

This reference sheet outlines the **MkDocs** and **mkdocstrings** implementation used to generate the ErgoMoCap documentation hub.

---

## Configuration (`mkdocs.yml`)

The complete global settings file mapping the theme configurations, Python environment setups, cross-references, and the documentation navigation tree.

```yaml
site_name: ErgoMoCap
theme:
  name: material
  features:
      - navigation.sections
      - navigation.expand
      - content.code.copy

use_directory_urls: false # IMPORTANT for browsing static local docs offline from ErgoMoCap app. No server needed

plugins:
  - search
  - autorefs
  - mkdocstrings:

... Look at the mkdocs.yml for complete and updated config


nav:
  - Home: index.md
  - Install and Get Started: install.md
  - User Guide: user_guide.md
  - Tutorial: tutorial.md
  - Roadmap: roadmap.md
  - GUI Architecture: gui_architecture.md
  - Calculators Docs and Audit: calculators.md
  - API Reference: reference.md
  - Checklist: checklist.md
  - Doc Guide: documentation_guide.md
  ... Add docs here if you add a new md file to docs/ folder


```

---

## How MkDocs & mkdocstrings Work

### Component Breakdown

* **Static Site Engine:** MkDocs converts the Markdown files listed in the navigation tree into static HTML pages.
* **Docstring Bridge:** `mkdocstrings` inspects the Python code and extracts Google-style docstrings into formatted HTML tables.
* **Import Paths:** Targets are referenced using standard Python dot notation (`.`) rather than directory paths (`/`).

### Inline Injection Syntax

To embed documentation for a module within an `.md` file, use the following syntax:

```markdown
# API Reference

## Leg Scoring Logic
::: calculators.reba_calculator.body_parts.leg_reba

## Neck Scoring Logic
::: calculators.reba_calculator.body_parts.neck_reba


```

---

## Docstring Style Guide

Use the Google docstring format so that `mkdocstrings` can parse the code correctly:

```python
def calculate_frame_rula_from_degs(upper_arm: int, lower_arm: int, wrist: int, wrist_twist: int) -> int:
    """
    Calculates the final RULA (Rapid Upper Limb Assessment) score based on
    posture inputs for Group A (Upper limb).

    This function aggregates the positional scores of the arm and wrist to
    determine the musculoskeletal load. It follows the standard RULA scoring
    matrix for Table A defined in `calculators.reba_calculator.reba_score_tables`.

    Args:
        upper_arm (int): Score for the upper arm position (1-6).
        lower_arm (int): Score for the lower arm position (1-3).
        wrist (int): Score for the wrist position (1-4).
        wrist_twist (int): Score for wrist twist (1-2).

    Returns:
        int: The resulting Table A score (range 1-9+).

    Raises:
        ValueError: If any of the input scores are outside their valid
            ergonomic ranges.

    Examples:
        >>> calculate_frame_rula_from_degs(1, 1, 1, 1)
        1
        >>> calculate_frame_rula_from_degs(4, 2, 3, 2)
        7
    """
    # Logic here
    pass


```

---

## Site Generation & Setup

### Installation

```bash
pip install "mkdocstrings[python]" mkdocs-material mkdocs


```

### Development Server

```bash
mkdocs serve


```

#### To build a static site

Docs can be browsed with a simple command from ErgoMoCap (using `use_directory_urls: false` option to serve the docs without servers)

```bash
mkdocs build


```

## Further Resources

For more advanced configuration regarding navigation, plugins, and custom CSS:

* [Official MkDocs Documentation](https://www.mkdocs.org/)
* [Custom Doctrings Generation PROMPT](docstring_prompt.md)

---

© 2026 medlav. Distributed under the AGPL-3.0 License.