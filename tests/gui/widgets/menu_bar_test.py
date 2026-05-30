# ---
# project: ErgoMoCap
# file: menu_bar_test.py
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

import pytest
from unittest.mock import MagicMock
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMainWindow, QMenu
from gui.widgets.menu_bar import MenuBar
from gui.widgets.menu_actions import MenuActions


class MockParent(QMainWindow):
    """Mock parent that implements all required toggle slots and action handlers."""

    def __init__(self):
        super().__init__()
        self.toggle_sidebar = MagicMock()
        self.toggle_theme = MagicMock()

        # All handlers required for MenuActions initialization validation
        self.handle_new_recording = MagicMock()
        self.handle_load_recording = MagicMock()
        self.handle_run_fmc = MagicMock()
        self.handle_select_root = MagicMock()
        self.kill_running_threads = MagicMock()
        self.handle_reboot = MagicMock()
        self.open_settings = MagicMock()
        self.open_docs = MagicMock()
        self.open_tutorial = MagicMock()
        self.open_source = MagicMock()
        self.safe_close = MagicMock()


@pytest.fixture
def actions_and_parent(qtbot):
    """Fixture to provide initialized actions and a valid mock parent window."""
    parent = MockParent()
    qtbot.addWidget(parent)
    actions = MenuActions(parent)
    return actions, parent


def test_menu_bar_initialization(actions_and_parent, qtbot):
    """
    Test that the MenuBar initializes correctly with all menus and corner widgets.
    """
    actions, parent = actions_and_parent
    menu_bar = MenuBar(actions, parent)
    qtbot.addWidget(menu_bar)

    # 1. Verify Corner Widgets
    assert menu_bar.sidebar_btn.text() == "☰"
    assert menu_bar.cornerWidget(Qt.Corner.TopLeftCorner) == menu_bar.sidebar_btn

    assert menu_bar.theme_btn.text() == "☀️"
    assert menu_bar.cornerWidget(Qt.Corner.TopRightCorner) == menu_bar.theme_btn

    # 2. Verify Menu Structure via Top-Level Actions
    bar_actions = menu_bar.actions()
    titles = [a.text() for a in bar_actions]

    assert "File" in titles
    assert "Controller" in titles
    assert "Settings" in titles
    assert "Help" in titles


def test_menu_bar_button_clicks(actions_and_parent, qtbot):
    """Test signal-slot connections for the integrated corner buttons using high-level actions."""
    actions, parent = actions_and_parent
    menu_bar = MenuBar(actions, parent)
    qtbot.addWidget(menu_bar)

    # Use native Qt click simulation on the corner tool buttons
    menu_bar.sidebar_btn.click()
    parent.toggle_sidebar.assert_called_once()

    menu_bar.theme_btn.click()
    parent.toggle_theme.assert_called_once()


def test_menu_content_logic(actions_and_parent, qtbot):
    """Verify that specific menus contain the expected configured actions."""
    actions, parent = actions_and_parent
    menu_bar = MenuBar(actions, parent)
    qtbot.addWidget(menu_bar)

    # Type-safe verification for File menu layout matches menu_bar.py setup
    file_menu = None
    for menu in menu_bar.findChildren(QMenu):
        if menu.title() == "File":
            file_menu = menu
            break

    assert file_menu is not None
    file_actions = file_menu.actions()
    assert actions.new_rec in file_actions
    assert actions.load_rec in file_actions
    assert actions.run_fmc in file_actions
    assert actions.select_fmc_root in file_actions
    assert any(a.isSeparator() for a in file_actions)
    assert actions.exit_act in file_actions


def test_controller_and_settings_menu_content(actions_and_parent, qtbot):
    """Verify that Controller and Settings menus map correctly to their designated actions."""
    actions, parent = actions_and_parent
    menu_bar = MenuBar(actions, parent)
    qtbot.addWidget(menu_bar)

    controller_menu = None
    settings_menu = None
    for menu in menu_bar.findChildren(QMenu):
        if menu.title() == "Controller":
            controller_menu = menu
        elif menu.title() == "Settings":
            settings_menu = menu

    assert controller_menu is not None
    assert actions.kill_threads in controller_menu.actions()
    assert actions.reboot_gui in controller_menu.actions()

    assert settings_menu is not None
    assert actions.settings in settings_menu.actions()


def test_help_menu_content(actions_and_parent, qtbot):
    """Verify the Help menu items systematically matching configuration container."""
    actions, parent = actions_and_parent
    menu_bar = MenuBar(actions, parent)
    qtbot.addWidget(menu_bar)

    help_menu = None
    for menu in menu_bar.findChildren(QMenu):
        if menu.title() == "Help":
            help_menu = menu
            break

    assert help_menu is not None
    help_actions = help_menu.actions()
    assert actions.docs in help_actions
    assert actions.tutorial in help_actions
    assert actions.open_source in help_actions


def test_menu_actions_trigger_callbacks(actions_and_parent):
    """Verify that every single registered QAction correctly routes back to the parent callback."""
    actions, parent = actions_and_parent

    # Test all File interactions
    actions.new_rec.trigger()
    parent.handle_new_recording.assert_called_once()

    actions.load_rec.trigger()
    parent.handle_load_recording.assert_called_once()

    actions.run_fmc.trigger()
    parent.handle_run_fmc.assert_called_once()

    actions.select_fmc_root.trigger()
    parent.handle_select_root.assert_called_once()

    actions.exit_act.trigger()
    parent.safe_close.assert_called_once()

    # Test Controller interactions
    actions.kill_threads.trigger()
    parent.kill_running_threads.assert_called_once()

    actions.reboot_gui.trigger()
    parent.handle_reboot.assert_called_once()

    # Test Settings interaction
    actions.settings.trigger()
    parent.open_settings.assert_called_once()

    # Test Help interactions
    actions.docs.trigger()
    parent.open_docs.assert_called_once()

    actions.tutorial.trigger()
    parent.open_tutorial.assert_called_once()

    actions.open_source.trigger()
    parent.open_source.assert_called_once()


@pytest.mark.parametrize(
    "missing_attr",
    [
        "handle_new_recording",
        "handle_load_recording",
        "handle_run_fmc",
        "handle_select_root",
        "kill_running_threads",
        "handle_reboot",
        "open_settings",
        "open_docs",
        "open_tutorial",
        "open_source",
        "safe_close",
    ],
)
def test_menu_actions_validation_failures(qtbot, missing_attr):
    """
    Branch Coverage: Verifies that missing any crucial handler on the parent QMainWindow
    accurately raises an AttributeError preventing an invalid state.
    """
    parent = MockParent()
    qtbot.addWidget(parent)

    # Remove the explicit attribute to test safety guard gates
    delattr(parent, missing_attr)

    with pytest.raises(AttributeError, match=f"NO {missing_attr}"):
        MenuActions(parent)
