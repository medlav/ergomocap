# ---
# project: ErgoMoCap
# file: style.py
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
ErgoMoCap: Volks-Typo Design System
-----------------------------------
Centralized styling and theme management for the ErgoMoCap application.

This module implements the "Volks-Typo" system, a design-token-driven architecture
that manages color palettes, typography, and spatial grids. It generates
dynamic Qt Style Sheets (QSS) to maintain a consistent visual language across
the GUI while supporting seamless switching between light and dark modes.

Key components:
- **Design Tokens**: Standardized `GRID` and `THEMES` dictionaries for layout and color.
- **Typography**: Specialized font mappings for headings (`Oswald`, `Roboto Condensed`),
  body text (`Work Sans`), and technical data (`JetBrains Mono`).
- **Dynamic Theming**: The [get_stylesheet][gui.theme.style] function
  injects theme tokens into a global QSS template.
"""

# style.py - VOLKS-TYPO SYSTEM
# DESIGN TOKENS
from enum import StrEnum


GRID: int = 6


class ErgoTheme(StrEnum):
    DARK = "dark"
    LIGHT = "light"


THEMES: dict[str, dict[str, str]] = {
    "light": {
        "background": "#ffffff",
        "surface": "#f5f5f5",
        "text_primary": "#000000",
        "text_secondary": "#333333",
        "text_muted": "#888888",
        "border": "#333333",
        "accent": "#dc2626",
        "accent_bright": "#ef4444",
        "btn_main": "#000000",
        "btn_main_text": "#ffffff",
        "btn_hover": "#dc2626",
        "btn_active": "#f97316",
    },
    "dark": {
        "background": "#0a0a0a",
        "surface": "#1a1a1a",
        "text_primary": "#f5f5f5",
        "text_secondary": "#b8b8b8",
        "text_muted": "#777777",
        "border": "#444444",
        "accent": "#ff3333",
        "accent_bright": "#ff5555",
        "btn_main": "#dc2626",
        "btn_main_text": "#ffffff",
        "btn_hover": "#ff3333",
        "btn_active": "#ffffff",
    },
}

FONTS = {
    "heading_primary": "Oswald",
    "heading_secondary": "Roboto Condensed",
    "body": "Work Sans",
    "mono": "JetBrains Mono",
}


def get_stylesheet(mode=ErgoTheme.DARK) -> str:
    """
    Generates the Qt Style Sheet (QSS) based on the specified visual mode.

    Maps the design tokens defined in [THEMES][gui.theme.style] and
    [FONTS][gui.theme.style] to a comprehensive QSS string. This includes
    base widget configuration, typography for custom label IDs (h1, h2, h3), and
    dynamic states for interactive components.

    Args:
        mode (ErgoTheme): The visual theme to retrieve. Must be one of `ErgoTheme.LIGHT` or `ErgoTheme.DARK`. Defaults to "ErgoTheme.DARK".

    Returns:
        str: A formatted QSS string ready to be applied via `setStyleSheet()`.

    Raises:
        KeyError: If an invalid `mode` is provided that does not exist in the [THEMES][gui.theme.style] dictionary.

    Examples:
        Applying the dark theme to a QApplication instance:
        ```python
        app = QApplication(sys.argv)
        style_qss = get_stylesheet("dark")
        app.setStyleSheet(style_qss)
        ```
    """
    c = THEMES[mode.value]

    return f"""
    /* BASE WIDGET CONFIGURATION */
    QWidget {{
        background-color: {c["background"]};
        color: {c["text_primary"]};
        font-family: "{FONTS["body"]}";
        font-size: 11px;
        outline: none;
    }}

    /* TYPOGRAPHY H1-H3 */
    QLabel#h1 {{
        font-family: "{FONTS["heading_primary"]}";
        font-size: 24px;
        font-weight: 700;
        color: {c["accent"]};
        letter-spacing: 2px;
        text-transform: uppercase;
        margin-bottom: {GRID * 2}px;
        padding: 0px;
    }}

    QLabel#h2 {{
        font-family: "{FONTS["heading_secondary"]}";
        font-size: 18px;
        font-weight: 700;
        color: {c["accent"]};
        letter-spacing: 1px;
        text-transform: uppercase;
        padding: {GRID}px 0px;
    }}

    QLabel#h3 {{
        font-family: "{FONTS["heading_secondary"]}";
        font-size: 14px;
        font-weight: 600;
        color: {c["accent"]};
        text-transform: uppercase;
        padding: {GRID // 2}px 0px;
    }}

    /* NAVIGATION COMPONENTS */
    QFrame#NavCard {{
        background-color: {c["surface"]};
        border: 2px solid {c["text_primary"]};
        padding: {GRID * 2}px;
    }}

    QFrame#NavCard:hover {{
        border-color: {c["accent"]};
        background-color: {c["accent"]};
    }}

    /* TOOLTIP SYSTEM */
    QToolTip {{
        background-color: {c["background"]};
        color: {c["text_primary"]};
        border: 1px solid {c["accent"]};
        border-radius: 4px;
        padding: 5px;
        font-family: {FONTS["mono"]};
        font-size: 40px;
    }}

    /* BUTTON SYSTEM */
    QPushButton {{
        font-family: "{FONTS["heading_primary"]}";
        text-transform: uppercase;
        font-weight: 800;
        letter-spacing: 0.5px;
        padding: {GRID * 2}px {GRID * 2}px;
        font-size: 11px;
        border: 1px solid {c["border"]};
        background-color: {c["btn_main"]};
        color: {c["btn_main_text"]};
    }}

    QPushButton:hover {{
        background-color: {c["btn_hover"]};
        color: #ffffff;
        border-color: {c["accent"]};
    }}

    QPushButton:pressed {{
        background-color: {c["btn_active"]};
        color: #000000;
    }}

    QPushButton#btnAction {{
        padding: {GRID * 2}px;
        font-size: 12px;
        background-color: {c["accent"]};
        color: #ffffff;
        border: 2px solid {c["text_primary"]};
    }}

    QPushButton#btnNega {{
        background-color: {c["text_primary"]};
        color: {c["background"]};
        padding: {GRID // 2}px {GRID * 2}px;
        font-family: "{FONTS["mono"]}";
        font-size: 9px;
    }}

    /* TOOLBAR SYSTEM */
    QFrame#Toolbar {{
        background-color: {c["surface"]};
        border-bottom: 2px solid {c["text_primary"]};
        min-height: 40px;
        padding: 0px {GRID * 2}px;
    }}

    /* FORM PANEL (LEFT SIDEBAR) */
    QFrame#FormPanel {{
        background-color: {c["background"]};
        border-right: 1px solid {c["text_primary"]};
        padding: {GRID * 2}px;
    }}

    /* INFO-MODAL SYSTEM */
    QDialog#InfoModal {{
        background-color: {c["background"]};
        border: 2px solid {c["text_primary"]};
    }}

    QFrame#ModalHeader {{
        background-color: {c["background"]};
        border-bottom: 1px solid {c["text_primary"]};
        min-height: 30px;
        padding: 0px {GRID}px;
    }}

    QLabel#ModalTitle {{
        font-family: "{FONTS["heading_primary"]}";
        text-transform: uppercase;
        letter-spacing: 1px;
        font-size: 11px;
        color: {c["text_primary"]};
    }}

    /* INFO-TABLE SYSTEM */
    QTableWidget#InfoTable {{
        background-color: {c["surface"]};
        gridline-color: {c["text_primary"]};
        border: 1px solid {c["text_primary"]};
        font-family: "{FONTS["body"]}";
        font-size: 10px;
        outline: none;
    }}

    QHeaderView::section {{
        background-color: {c["background"]};
        color: {c["accent"]};
        padding: {GRID // 2}px {GRID}px;
        font-family: "{FONTS["heading_secondary"]}";
        font-weight: 700;
        font-size: 9px;
        text-transform: uppercase;
        border: 1px solid {c["text_primary"]};
    }}

    QTableWidget::item {{
        background-color: {c["background"]};
        color: {c["text_primary"]};
        padding: {GRID // 2}px {GRID}px;
        border-bottom: 1px solid {c["text_primary"]};
    }}


    QTableWidget::item:hover{{
        background-color: {c["accent"]};
        color: {c["btn_main_text"]};
    }}

    /* GROUPBOX / FIELDSETS */
    QGroupBox {{
        font-family: "{FONTS["heading_secondary"]}";
        font-weight: 700;
        font-size: 12px;
        text-transform: uppercase;
        border: 1px solid {c["text_primary"]};
        margin-top: 6px;
        padding-top: 8px;
        background-color: {c["background"]};
    }}

    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 0 {GRID}px;
        background-color: {c["background"]};
        left: {GRID}px;
        color: {c["accent"]};
        letter-spacing: 0.5px;
    }}

    /* FIELD LABELS (MICRO-TYPOGRAPHY) */
    QLabel#FieldLabel {{
        font-family: "{FONTS["heading_secondary"]}";
        font-weight: 700;
        text-transform: uppercase;
        font-size: 10px;
        color: {c["text_secondary"]};
        margin-bottom: 1px;
    }}

    /* INPUT FIELDS */
    QLineEdit, QTextEdit, QComboBox {{
        background-color: {c["surface"]};
        border: 1px solid {c["text_primary"]};
        padding: {GRID}px;
        font-family: "{FONTS["mono"]}";
        font-size: 12px;
        color: {c["text_primary"]};
    }}

    QLineEdit:focus, QComboBox:focus {{
        border: 1px solid {c["accent"]};
        background-color: {c["background"]};
    }}

    QComboBox::drop-down {{
        width: 18px;
        border-left: 1px solid {c["text_primary"]};
    }}

    /* THE CBOX ARROW ICON */
    QComboBox::down-arrow {{
         border-left: 1px solid {c["text_primary"]};
        border-bottom: 1px solid {c["text_primary"]};
        width: 5px;
        height: 5px;
        margin-top: -2px; /* Visual centering */
        margin-right: 2px;
    }}

    /* ARROW STATE WHEN OPEN */
    QComboBox::down-arrow:on {{
        border-top: none;
        border-bottom: 5px solid {c["accent"]};
    }}

    /* SCROLLBAR SYSTEM (SUPER THIN) */
    QScrollBar:vertical {{
        background: {c["surface"]};
        width: 6px;
        margin: 0px;
    }}

    QScrollBar::handle:vertical {{
        background: {c["text_primary"]};
        min-height: 15px;
    }}

    QScrollBar::handle:vertical:hover {{
        background: {c["accent"]};
    }}

    QScrollBar:horizontal {{
        background: {c["surface"]};
        height: 6px;
        margin: 0px;
    }}

    QScrollBar::handle:horizontal {{
        background: {c["text_primary"]};
        min-width: 15px;
    }}

    /* TAB WIDGET SYSTEM */
    QTabWidget::pane {{
        border: 1px solid {c["text_primary"]};
        background-color: {c["background"]};
        top: -1px;
    }}

    QTabBar::tab {{
        background-color: {c["surface"]};
        border: 1px solid {c["text_primary"]};
        font-family: "{FONTS["heading_secondary"]}";
        font-weight: 700;
        font-size: 9px;
        text-transform: uppercase;
        padding: {GRID}px {GRID * 2}px;
        margin-right: 1px;
        color: {c["text_secondary"]};
        letter-spacing: 0.5px;
    }}

    QTabBar::tab:selected {{
        background-color: {c["background"]};
        border-bottom-color: {c["background"]};
        color: {c["accent"]};
    }}

    QTabBar::tab:hover {{
        background-color: {c["accent"]};
        color: #ffffff;
    }}

    /* PROGRESS BAR (SLIM INDUSTRIAL) */
    QProgressBar {{
        border: 1px solid {c["text_primary"]};
        background-color: {c["surface"]};
        text-align: center;
        font-family: "{FONTS["mono"]}";
        font-size: 8px;
        font-weight: bold;
        color: {c["text_primary"]};
        height: 10px;
    }}

    QProgressBar::chunk {{
        background-color: {c["accent"]};
        width: 4px;
        margin: 0.5px;
    }}

    /* SLIDERS */
    QSlider::groove:horizontal {{
        border: 1px solid {c["text_primary"]};
        height: 2px;
        background: {c["surface"]};
    }}

    QSlider::handle:horizontal {{
        background: {c["text_primary"]};
        border: 1px solid {c["text_primary"]};
        width: 10px;
        height: 10px;
        margin: -4px 0;
    }}

    QSlider::handle:horizontal:hover {{
        background: {c["accent"]};
    }}

    /* STATUS BAR & TOOLTIPS */
    QStatusBar {{
        background-color: {c["text_primary"]};
        color: {c["background"]};
        font-family: "{FONTS["mono"]}";
        font-size: 9px;
        text-transform: uppercase;
        padding: 0px {GRID}px;
    }}

    QToolTip {{
        background-color: {c["text_primary"]};
        color: {c["background"]};
        border: none;
        font-family: "{FONTS["mono"]}";
        font-size: 9px;
        padding: {GRID // 2}px;
    }}

    /* VIDEO CANVAS & SPECIALTY BUTTONS */
    QLabel#VideoCanvas {{
        background-color: #000000;
        border: 2px solid {c["text_primary"]};
        border-radius: 4px;
        padding: {GRID * 3}px;
        margin: {GRID}px;
    }}

    QPushButton#btnInfoCircle {{
        background-color: {c["surface"]};
        border: 1px solid {c["text_primary"]};
        color: {c["text_primary"]};
        border-radius: 9px;
        max-width: 18px;
        max-height: 18px;
        font-size: 10px;
        font-weight: bold;
        padding: 4px;
    }}

    /* UTILITY CLASSES */
    .TextMuted {{
        color: {c["text_muted"]};
        font-size: 8px;
        font-family: "{FONTS["mono"]}";
    }}

    QFrame#hr {{
        background-color: {c["text_primary"]};
        max-height: 1px;
        min-height: 1px;
        margin: {GRID * 2}px 0px;
    }}

    QMenuBar {{
            background-color: {c["background"]};
            border-bottom: 2px solid {c["text_primary"]};
            font-family: "{FONTS["heading_secondary"]}";
            font-weight: 700;
            text-transform: uppercase;
            font-size: 10px;
            letter-spacing: 1px;
            padding: 0px;
        }}

    QMenuBar::item {{
        background: transparent;
        padding: {GRID * 2}px {GRID * 2}px;
        margin-right: {GRID}px;
        margin-left: {GRID}px;
        color: {c["text_primary"]};
    }}

    QMenuBar::item:selected {{
        background-color: {c["accent"]};
        color: #ffffff;
    }}

    QMenu {{
        background-color: {c["background"]};
        border: 2px solid {c["text_primary"]};
        padding: {GRID // 2}px;
    }}

    QMenu::item {{
        font-family: "{FONTS["body"]}";
        font-weight: 500;
        text-transform: uppercase;
        font-size: 10px;
        padding: {GRID * 2}px {GRID * 2}px;
        color: {c["text_primary"]};
        min-width: 150px;
    }}

    QMenu::item:selected {{
        background-color: {c["text_primary"]};
        color: {c["background"]};
    }}

    QMenu::separator {{
        height: 1px;
        background: {c["text_muted"]};
        margin: {GRID}px {GRID}px;
    }}

    QMenu::shortcut {{
        color: {c["text_muted"]};
        font-family: "{FONTS["mono"]}";
        font-size: 9px;
        padding-left: {GRID * 3}px;
    }}

    QMenu::indicator {{
        width: 10px;
        height: 10px;
        border: 1px solid {c["text_primary"]};
        margin-left: {GRID}px;
    }}

    QMenu::indicator:checked {{
        background-color: {c["accent"]};
    }}

    QToolButton {{
        font-family: "{FONTS["heading_primary"]}";
        font-weight: 800;
        font-size: 18px;
        border: none;
        background-color: transparent;
        color: {c["text_primary"]};

        /* Forced Geometry (Required for a circle) */
        width: 36px;
        height: 36px;
        padding: 0px;
        margin: 0px {GRID}px 0px {GRID * 2}px; /* Left padding as requested, centering the box */

        qproperty-toolButtonStyle: ToolButtonTextOnly;
        text-align: center;
    }}

    QToolButton:hover {{
        /* The Circle Highlight */
        color: {c["accent"]};
     }}

    QToolButton:pressed {{
        color: {c["accent"]};
    }}

    """


# --- APPLICATION HELPERS ---


def apply_style(app_instance, mode=ErgoTheme.DARK):
    qss = get_stylesheet(mode)
    app_instance.setStyleSheet(qss)


def get_theme_colors(mode=ErgoTheme.DARK):
    return THEMES.get(mode, THEMES[mode.value])
