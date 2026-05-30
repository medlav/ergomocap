# ---
# project: ErgoMoCap
# file: todo_scanner.py
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
ErgoMoCap: Task Inventory Scanner
---------------------------------
Automated task tracking and documentation utility.

This module provides a lightweight scanner that traverses the project directory
to extract `TODO`, `FIXME`, and `DEBUG` comments. It aggregates these technical
debts into a centralized Markdown dashboard, facilitating project management
directly from the source code.

Features:
- **Configurable Scanning**: Respects exclusion rules and file extensions defined
  in `pyproject.toml`.
- **Regex Extraction**: Case-insensitive pattern matching for standard task tags.
- **Auto-Documentation**: Generates a GitHub-flavored Markdown table with
  deep-links to specific code lines for rapid navigation.
"""

import os
import re
import tomllib
from pathlib import Path


def load_config():
    """Reads exclusion rules from pyproject.toml."""
    default_config = {
        "exclude": [".git", ".venv"],
        "include_extensions": [".py"],
        "output_file": "TODO.md",
    }

    config_path = Path("pyproject.toml")
    if config_path.exists():
        with open(config_path, "rb") as f:
            data = tomllib.load(f)
            return data.get("tool", {}).get("todo_scanner", default_config)
    return default_config


def get_todos(config):
    """Walks the repo and extracts TODO strings."""
    todo_items = []
    exclude_set = set(config.get("exclude", []))
    extensions = tuple(config.get("include_extensions", []))

    # Regex to catch "TODO:", "todo ", "FIXME:", etc.
    pattern = re.compile(r"(TODO|FIXME|DEBUG)[:\s]+(.*)", re.IGNORECASE)

    for root, dirs, files in os.walk("."):
        # Modifying dirs in-place allows os.walk to skip excluded folders entirely
        dirs[:] = [d for d in dirs if d not in exclude_set]

        for file in files:
            if file.endswith(extensions) and file != config.get("output_file"):
                path = Path(root) / file
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        for i, line in enumerate(f, 1):
                            match = pattern.search(line)
                            if match:
                                tag = match.group(1).upper()
                                content = match.group(2).strip()
                                todo_items.append(
                                    {
                                        "file": str(path),
                                        "line": i,
                                        "tag": tag,
                                        "content": content,
                                    }
                                )
                except (UnicodeDecodeError, PermissionError):
                    continue
    return todo_items


def update_todo_md(todos, output_path):
    """Generates the Markdown table."""
    content = [
        "# Project Task Board\n",
        "> [!NOTE]\n",
        "> This file is auto-generated. Do not edit manually.\n\n",
        "| Status | Location | Description |\n",
        "| :--- | :--- | :--- |\n",
    ]

    if not todos:
        content.append("| Clean | - | No pending tasks found! |\n")
    else:
        for t in todos:
            # Creates a clickable link for GitHub/VSCode
            link = f"[`{t['file']}:{t['line']}`]({t['file']}#L{t['line']})"
            content.append(f"| **{t['tag']}** | {link} | {t['content']} |\n")

    with open(output_path, "w", encoding="utf-8") as f:
        f.writelines(content)


if __name__ == "__main__":
    cfg = load_config()
    items = get_todos(cfg)
    update_todo_md(items, cfg.get("output_file"))
    print(f"Successfully tracked {len(items)} tasks in {cfg.get('output_file')}")
