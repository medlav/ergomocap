# ---
# project: ErgoMoCap
# file: menu_bar.py
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
ErgoMoCap: Menu Bar
-------------------
Custom Navigation and Command Interface for the Main Application.

This module implements the `MenuBar` class, which extends the standard `QMenuBar`
to include specialized corner widgets for UI interaction. It integrates a
hamburger-style sidebar toggle and a theme switcher directly into the menu
bar real estate, providing a compact and modern navigation experience. The
menus are populated using centralized actions defined in
[MenuActions][gui.widgets.menu_actions.MenuActions].
"""

from PySide6.QtWidgets import QMenu, QMenuBar, QSizePolicy, QToolButton
from PySide6.QtCore import Qt
from gui.widgets.menu_actions import MenuActions


class MenuBar(QMenuBar):
    """
    Custom menu bar implementation with integrated corner controls.

    This class organizes the application's top-level navigation into logical
    categories (File, Controller, Settings, Help) while providing immediate
    access to global UI state toggles via `QToolButton` corner widgets.

    Attributes:
        sidebar_btn (QToolButton): A button positioned in the top-left corner used
            to toggle the navigation sidebar.
        theme_btn (QToolButton): A button positioned in the top-right corner used
            to switch between light and dark visual themes.
    """

    def __init__(self, actions: MenuActions, parent):
        """
        Initialize the menu bar with structured menus and corner widgets.

        Sets up the visual layout by injecting the sidebar toggle and theme switcher
        into the bar's corners and populating the dropdown menus with actions
        provided by the [MenuActions][gui.widgets.menu_actions.MenuActions] container.

        Args:
            actions (MenuActions): The container holding pre-configured `QAction` objects.
            parent (QMainWindow): The parent [MainWindow][gui.frontend.MainWindow]
                instance. This parent must implement `toggle_sidebar()` and
                `toggle_theme()` slots.

        Returns:
            None (None): Initializer return.
        """

        super().__init__(parent)

        # --- THE SIDEBAR BUTTON ---
        self.sidebar_btn: QToolButton = QToolButton(self)
        self.sidebar_btn.setText("☰")
        self.sidebar_btn.setMinimumWidth(24)
        self.sidebar_btn.setSizePolicy(
            QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding
        )
        # Disable default focus rectangle and OS-level hover shadows
        self.sidebar_btn.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.sidebar_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.sidebar_btn.clicked.connect(parent.toggle_sidebar)

        # Inject the button into the TOP LEFT corner of the menu bar
        self.setCornerWidget(self.sidebar_btn, Qt.Corner.TopLeftCorner)

        # --- THE THEME BUTTON ---
        self.theme_btn: QToolButton = QToolButton(self)
        self.theme_btn.setText("☀️")
        self.theme_btn.setMinimumWidth(28)
        self.theme_btn.setSizePolicy(
            QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding
        )
        self.theme_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.theme_btn.clicked.connect(parent.toggle_theme)

        # Inject the button into the TOP RIGHT corner of the menu bar
        self.setCornerWidget(self.theme_btn, Qt.Corner.TopRightCorner)

        # File
        file_menu: QMenu = self.addMenu(self.tr("File"))
        file_menu.addAction(actions.new_rec)
        file_menu.addAction(actions.load_rec)
        file_menu.addAction(actions.run_fmc)
        file_menu.addAction(actions.select_fmc_root)
        file_menu.addSeparator()
        file_menu.addAction(actions.exit_act)

        # Controller
        controller_menu: QMenu = self.addMenu(self.tr("Controller"))
        controller_menu.addAction(actions.kill_threads)
        controller_menu.addAction(actions.reboot_gui)

        # Settings
        settings_menu: QMenu = self.addMenu(self.tr("Settings"))
        settings_menu.addAction(actions.settings)

        # Help
        help_menu: QMenu = self.addMenu(self.tr("Help"))
        help_menu.addAction(actions.docs)
        help_menu.addAction(actions.tutorial)
        help_menu.addAction(actions.open_source)
