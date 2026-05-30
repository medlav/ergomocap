# ---
# project: ErgoMoCap
# file: main.py
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
ErgoMoCap: Application Entry Point
----------------------------------
Main execution script for the ErgoMoCap ergonomic analysis suite.

This module initializes the high-level application environment, including the
Qt event loop, localization (i18n), visual theming, and the primary window
instantiation. It serves as the bridge between the system environment and
the [MainWindow][gui.frontend.MainWindow] component.

Key Initialization Steps:
- **Environment Setup**: Configures the `QApplication` with system arguments.
- **Localization**: Detects system `QLocale` and attempts to load corresponding
  `.qm` translation files from the `intl/generated` directory.
- **Theming**: Applies the "Fusion" style and the project's custom dark-mode
  stylesheet via [get_stylesheet][gui.theme.style].
- **Path Management**: Utilizes [ErgoPaths][gui.utils.app_paths.ErgoPaths] to
  locate resources like the application icon.
- **Window Management**: Launches the main GUI and handles the clean exit
  of the process.
"""

import sys
from pathlib import Path

from qtpy.QtWidgets import QApplication
from qtpy.QtGui import QIcon
from qtpy.QtCore import QTranslator, QLocale

from gui.frontend import MainWindow
from gui.theme.style import get_stylesheet
from gui.utils.app_paths import ErgoPaths


def main() -> None:
    """
    Primary entry point for the ErgoMoCap application.

    Initializes the `QApplication` instance, configures the localization (i18n) settings based
    on the user's system locale, applies the global visual theme via [get_stylesheet][gui.theme.style],
    and instantiates the [MainWindow][gui.frontend.MainWindow].

    The function orchestrates the following bootstrap sequence:
    1.  Creates the `QApplication` and handles CLI arguments.
    2.  Searches for and loads `.qm` translation files from the `intl/generated` directory.
    3.  Sets the application style to 'Fusion' and applies the custom dark theme.
    4.  Configures the application-wide icon using [ErgoPaths][gui.utils.app_paths.ErgoPaths].
    5.  Enters the Qt main event loop.


    Returns:
        None: This function terminates the process by calling `sys.exit()`.

    Raises:
        FileNotFoundError: If critical UI resources are missing, though the application
            is designed to fail gracefully with logging in most resource-missing scenarios.

    Examples:
        To start the application from the command line:
        ```bash
        python main.py
        ```
    """
    app = QApplication(sys.argv)

    ### TRANSLATOR SECTION ###
    # TODO implement this

    translator = QTranslator()
    short_locale = QLocale.system().name()[:2]
    intl_dir = Path(__file__).parent / "intl" / "generated"
    translation_file = intl_dir / f"strings_{short_locale}.qm"

    if translation_file.exists():
        if translator.load(str(translation_file)):
            app.installTranslator(translator)

    ##########################

    app.setStyle("Fusion")

    app.setStyleSheet(get_stylesheet())

    icon_path = ErgoPaths.LOGO

    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    win = MainWindow()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
