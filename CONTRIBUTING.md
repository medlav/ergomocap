# Contributing to ErgoMoCap

First off, thanks for taking the time to contribute! As a solo maintainer, I’m excited to see others interested in ergonomic motion capture.

The following is a set of guidelines for contributing to ErgoMoCap on GitHub. These are mostly guidelines, not rules. Use your best judgment, and feel free to propose changes to this document in a pull request.

---

## How to contribute

### Reporting bugs

This section guides you through submitting a bug report for ErgoMoCap. Following these guidelines helps me understand your report, reproduce the behavior, and find related issues.

#### Before submitting a bug report

* **Check the [issue tracker]** to see if the problem has already been reported.
* **Make sure your issue is really a bug**, and not a support request or a question about ergonomic standards.
* **Verify your environment.** Ensure your virtual environment is active and dependencies are up to date.

#### How do I submit a bug report?

Bugs should be submitted to the [issue tracker]. To give me the best chance to fix it, please:

* **Use a clear and descriptive title.**
* **Describe the exact steps to reproduce the problem** in as much detail as possible.
* **Explain the behavior you observed** versus what you expected to see.
* **Include details about your setup:** Which OS are you on? What version of Python? (e.g., Windows 11, Python 3.11).

---

### Suggesting enhancements

I'm always looking for ways to make the math faster or the UI smoother! Whether you want to add a new ergonomic standard (like RULA or NIOSH) or a new sensor integration, I’d love to hear your thoughts.

#### How do I submit a suggested enhancement?

* **Open a Discussion or an Issue first.** This allows us to align on the architecture before you dive into the code.
* **Provide a detailed description** of the proposed enhancement and why it would be useful for the ergonomic community.

---

### Code contributions

#### Local development

ErgoMoCap uses modern tooling to keep the "core" safe and consistent. To get your development environment running:

1.  **Fork the repository** and clone it locally.
2.  **Set up your environment:**
    ```bash
    # Create and activate virtual environment
    python -m venv .venv
    source .venv/bin/activate  # Windows: .venv\Scripts\activate

    # Install with development tools
    pip install -e ".[dev]"
    ```
3.  **Install pre-commit hooks:**
    We use `pre-commit` to handle the "boring stuff" automatically.
    ```bash
    pre-commit install
    ```

#### Standards and Quality

When you contribute, automated tools will run to ensure the code is suitable to be merged:

* **Linting & Formatting:** We use `ruff` for consistent style and `pylance` for type checking.
* **Security:** `bandit` is integrated via `.toml` config to check for vulnerabilities.
* **Naming Conventions:** Please use `lowercase_snake_case` for all files. **No capital letters in filenames** (to avoid cross-OS compatibility issues).
* **Documentation:** We use `interrogate` to ensure docstrings aren't forgotten. Please follow simple standards for Docstrings (see our internal formatting guide).

#### Testing

I try to keep the core logic covered so we don't break things by accident.

* **Run tests:** Simply run `pytest`.
* **UI Testing:** We use `pytest-qt` for interface tests.
* **Coverage:** While we aim for high coverage, as long as your new code includes a relevant test, we’re good!

---

### Pull requests

>[!IMPORTANT]
>**A note on Pull Requests:** Since I am a solo maintainer with limited time, I may not be able to review or merge Pull Requests quickly. If you have a specific feature or fix you need right away, I highly encourage you to fork the project and maintain your own version. This ensures you aren't blocked by my schedule!

1.  **Fill out the PR body completely.** Describe what you improved or fixed.
2.  **Ensure tests pass.** Code without passing tests or that fails the `pre-commit` pipeline will generally not be merged.
3.  **Update Assets:** Our pipeline generates status badges (coverage, etc.) in the `assets/` folder. If your PR changes these, `git add` the updated SVGs to your commit.
4.  **Documentation:** If your changes warrant it, please update the `docs/` (we use `mkdocs`).
5. **Maintainer Discretion:** I reserve the right to decline any PR that doesn't align with the project's technical direction or my current maintenance capacity.

---

## Documentation Standards

I use `interrogate` to audit our documentation coverage and `mkdocstrings` to automatically generate the API reference. To help me keep the site professional and easy to navigate, please try to follow these guidelines:

### 1. Style & Formatting
* **Docstring Format:** Please use the **Google Python Style Guide**. It keeps everything consistent and readable.
* **Coverage:** Every public module, class, and function **must** have a docstring so `interrogate` stays happy.
* **Clarity over Complexity:** Keep your descriptions concise. I’m mostly interested in the *why* and *how* behind the component.

### 2. Automatic Cross-Referencing
One of the cool things about `mkdocstrings` is that you can create instant hyperlinks to internal or external docs just by using backticks:

* **Internal modules:** Use the full path, e.g., `` `calculators.reba.RebaScore` ``.
* **External libraries:** You can even link to PySide6 or other dependencies using the component name, e.g., `` `PySide6.QtWidgets.QMainWindow` ``.

### 3. File Naming Conventions
To keep the repo clean and ensure things don't break when moving between Windows, macOS, or Linux:
* **Lowercase only:** Use `snake_case` for all filenames (e.g., `reba_calculator.py`, not `RebaCalculator.py`).
* **No Caps:** Please avoid uppercase letters entirely in filenames to prevent case-sensitivity issues.
* **Descriptive names:** Make sure the filename gives a clear idea of the logic inside.

### 4. Docstring Template
Here is a quick example of how I usually structure things:

```python
def process_mocap_frame(frame_data: dict) -> float:
    """
    Processes a single frame of motion capture data to calculate joint angles.

    Args:
        frame_data: A dictionary containing raw sensor coordinates.

    Returns:
        The calculated angle in degrees.

    Raises:
        ValueError: If the sensor data is missing required markers.
    """
```

---


## Need help?

If you have an issue that hasn't had any attention, feel free to ping me on the issue tracker. Please remember I am a solo maintainer, but I will get back to you as soon as I can!

Your contributions help make ErgoMoCap better for everyone. I'm looking forward to seeing what you build!




