# ---
# project: ErgoMoCap
# file: update_intl.py
# author: medlav
# created: 2026-05-19
# license: AGPL-3.0
# ---
# Copyright (C) 2026 medlav
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the representation of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
ErgoMoCap: Internationalization (i18n) Manager
----------------------------------------------
Localization workflow automation for Qt-based strings.

This utility streamlines the process of updating and compiling translation files
for the ErgoMoCap interface. It automates the extraction of translatable strings
from the `/gui` and `/calculators` directories and manages the conversion between
Qt XML source files (`.ts`) and binary runtime files (`.qm`).

Workflow:
1.  **Extraction**: Scans Python source files using `pyside6-lupdate`.
2.  **Aggregation**: Updates the regional translation source files.
3.  **Compilation**: Converts human-readable translations into high-performance
    binary formats via `pyside6-lrelease`.
"""

import logging
import subprocess
from pathlib import Path


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("intl logger")


def run_intl() -> None:
    """
    [intl.update_intl.run_intl][]

    Orchestrates the extraction and compilation of translatable strings for the ErgoMoCap project.

    This function automates the Qt localization workflow by:
    1.  Identifying all Python source files within the `/gui` and `/calculators` directories.
    2.  Executing `pyside6-lupdate` to synchronize translatable strings into an XML-based `.ts` file.
    3.  Prompting the user to compile the updated source into a high-performance binary `.qm` file
        using `pyside6-lrelease`.

    The generated files are stored in the `intl/generated` directory, which is utilized by
    the [main][main.main] application entry point for runtime translation.

    Returns:
        None: The return value is always None.

    Raises:
        subprocess.CalledProcessError: If the external Qt tools (`lupdate` or `lrelease`) fail
            during execution.
        OSError: If there are issues creating the `generated` directory or accessing source files.

    Examples:
        To update project translations from the terminal:
        ```bash
        python -m intl.update_intl
        ```
    """
    # 1. Path Setup
    # Script is in /intl, so root is one level up
    intl_dir = Path(__file__).parent
    root_dir = intl_dir.parent

    # Target directory for generated files
    try:
        gen_dir = intl_dir / "generated"
        gen_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        logger.error(f"❌ Failed to create generated directory: {e}")
        raise

    folders_to_scan = ["gui", "calculators"]
    ts_file = gen_dir / "strings_it.ts"
    qm_file = gen_dir / "strings_it.qm"

    # 2. Manually collect all .py files for a deep scan
    py_files = []
    try:
        for folder in folders_to_scan:
            target_path = root_dir / folder
            if target_path.exists():
                # rglob finds everything in subdirectories too
                found = [str(f) for f in target_path.rglob("*.py")]
                py_files.extend(found)
    except OSError as e:
        logger.error(f"❌ Failed to scan directories: {e}")
        raise

    if not py_files:
        logger.info(f"❌ No .py files found in: {', '.join(folders_to_scan)}")
        return

    logger.info(f"Scanning {len(py_files)} files across {folders_to_scan}...")

    # 3. Extract strings (lupdate)
    cmd_update = ["pyside6-lupdate"] + py_files + ["-ts", str(ts_file)]

    try:
        subprocess.run(cmd_update, check=True)
        logger.info(f"✅ TS file updated at: {ts_file}")
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ lupdate failed: {e}")
        raise

    # 4. Compile strings (lrelease)
    logger.info(
        f"\nIf you have pasted the LLM translations into {ts_file.name}, press 'y' to compile."
    )
    confirm = input("Compile to binary .qm? (y/n): ").lower()

    if confirm == "y":
        cmd_release = ["pyside6-lrelease", str(ts_file), "-qm", str(qm_file)]
        try:
            subprocess.run(cmd_release, check=True)
            logger.info(f"✅ Binary ready at: {qm_file}")
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ lrelease failed: {e}")
            raise


if __name__ == "__main__":
    run_intl()

    # TODO remove print statement and place proper logging
