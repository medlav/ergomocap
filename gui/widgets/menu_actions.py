# ---
# project: ErgoMoCap
# file: menu_actions.py
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
ErgoMoCap: Menu Actions
-----------------------
Centralized Action Management for the ErgoMoCap Main Window.

This module defines the `MenuActions` class, which serves as a container for all
`QAction` objects used in the application's menu bar and toolbars. By decoupling
action definitions from the UI layout, it ensures that shortcuts, signals, and
translations are managed in a single, testable location. It performs strict
attribute validation to ensure the parent `QMainWindow` implements the necessary
handler methods.
"""

from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QMainWindow


class MenuActions:
    """
    Factory class for creating and connecting GUI actions.

    This class encapsulates the initialization of all user-triggerable actions within
    the ErgoMoCap interface. It maps keyboard shortcuts to specific logic handlers
    defined in the main window.

    Attributes:
        new_rec (QAction): Action to initiate a new motion capture recording.
        load_rec (QAction): Action to load an existing recording for analysis.
        run_fmc (QAction): Action to execute the FreeMoCap processing pipeline.
        select_fmc_root (QAction): Action to define the root directory for FreeMoCap data.
        exit_act (QAction): Action to safely close the application.
        kill_threads (QAction): Action to terminate all background processing threads.
        reboot_gui (QAction): Action to refresh/restart the GUI state.
        settings (QAction): Action to open the application configuration dialog.
        docs (QAction): Action to open the external project documentation.
        tutorial (QAction): Action to open the user tutorial.
        open_source (QAction): Action to open the project's source code repository.
    """

    def __init__(self, main_win: QMainWindow):
        """
        Initialize and validate menu actions for the ErgoMoCap application.

        Performs a safety check to ensure the provided `main_win` contains all required
        callback methods. If validation passes, it initializes `QAction` objects with
        translations, standard shortcuts, and signal-slot connections.

        [MainWindow][gui.frontend.MainWindow]

        Args:
            main_win (QMainWindow): The target application window that implements the
                necessary handler slots for the frontend.

        Returns:
            None (None): Initializer return.

        Raises:
            AttributeError (AttributeError): If `main_win` is missing any required
                handler method (e.g., `handle_new_recording`, `kill_running_threads`, etc.).
        """

        if not hasattr(main_win, "handle_new_recording"):
            raise AttributeError("NO handle_new_recording")
        if not hasattr(main_win, "handle_load_recording"):
            raise AttributeError("NO handle_load_recording")

        if not hasattr(main_win, "handle_run_fmc"):
            raise AttributeError("NO handle_run_fmc")
        if not hasattr(main_win, "handle_select_root"):
            raise AttributeError("NO handle_select_root")

        if not hasattr(main_win, "kill_running_threads"):
            raise AttributeError("NO kill_running_threads")
        if not hasattr(main_win, "handle_reboot"):
            raise AttributeError("NO handle_reboot")
        if not hasattr(main_win, "open_settings"):
            raise AttributeError("NO open_settings")
        if not hasattr(main_win, "open_docs"):
            raise AttributeError("NO open_docs")
        if not hasattr(main_win, "open_tutorial"):
            raise AttributeError("NO open_tutorial")
        if not hasattr(main_win, "open_source"):
            raise AttributeError("NO open_source")
        if not hasattr(main_win, "safe_close"):
            raise AttributeError("NO safe_close")

        # --- File Section ---
        self.new_rec: QAction = QAction(main_win.tr("New Recording"), main_win)
        self.new_rec.setShortcut(QKeySequence.StandardKey.New)
        self.new_rec.triggered.connect(main_win.handle_new_recording)  # type: ignore Already Fixed using if gate

        self.load_rec: QAction = QAction(main_win.tr("Load Recording"), main_win)
        self.load_rec.setShortcut(QKeySequence.StandardKey.Open)
        self.load_rec.triggered.connect(main_win.handle_load_recording)  # type: ignore Already Fixed using if gate

        self.run_fmc: QAction = QAction(main_win.tr("Run FreeMoCap"), main_win)
        self.run_fmc.setShortcut(QKeySequence.StandardKey.Bold)
        self.run_fmc.triggered.connect(main_win.handle_run_fmc)  # type: ignore Already Fixed using if gate

        self.select_fmc_root: QAction = QAction(
            main_win.tr("Select FMC Folder"), main_win
        )
        self.select_fmc_root.setShortcut(QKeySequence.StandardKey.Italic)
        self.select_fmc_root.triggered.connect(main_win.handle_select_root)  # type: ignore Already Fixed using if gate

        self.exit_act: QAction = QAction(main_win.tr("Exit"), main_win)
        self.exit_act.setShortcut("Ctrl+Q")
        self.exit_act.triggered.connect(main_win.safe_close)  # type: ignore Already Fixed using if gate

        # --- Controller Section ---
        self.kill_threads: QAction = QAction(
            main_win.tr("Kill Threads and Processes"), main_win
        )
        self.kill_threads.setShortcut("Ctrl+K")
        self.kill_threads.triggered.connect(main_win.kill_running_threads)  # type: ignore Already Fixed using if gate

        self.reboot_gui: QAction = QAction(main_win.tr("Reboot GUI"), main_win)
        self.reboot_gui.setShortcut("Ctrl+R")
        self.reboot_gui.triggered.connect(main_win.handle_reboot)  # type: ignore Already Fixed using if gate

        # --- Settings Section ---
        self.settings: QAction = QAction(main_win.tr("Settings"), main_win)
        self.settings.setShortcut("Ctrl+,")
        self.settings.triggered.connect(main_win.open_settings)  # type: ignore Already Fixed using if gate

        # --- Help Section ---
        self.docs: QAction = QAction(main_win.tr("Documentation"), main_win)
        self.docs.triggered.connect(main_win.open_docs)  # type: ignore Already Fixed using if gate

        self.tutorial: QAction = QAction(main_win.tr("Tutorial"), main_win)
        self.tutorial.triggered.connect(main_win.open_tutorial)  # type: ignore Already Fixed using if gate

        self.open_source: QAction = QAction(main_win.tr("Source Code"), main_win)
        self.open_source.triggered.connect(main_win.open_source)  # type: ignore Already Fixed using if gate
