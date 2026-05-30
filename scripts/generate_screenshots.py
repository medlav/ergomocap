import sys
from pathlib import Path
import time
from typing import List, cast
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QApplication, QComboBox, QAbstractItemView
from PySide6.QtCore import (
    QCoreApplication,
    QEventLoop,
    QAbstractItemModel,
    QModelIndex,
)
from unittest.mock import MagicMock

project_root: Path = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from gui.utils.app_paths import ErgoPaths  # type: ignore # noqa: E402
from gui.theme.style import get_stylesheet  # type: ignore # noqa: E402
from gui.utils.constants import AssessmentMethod  # type: ignore # noqa: E402
from gui.utils.models import AnalysisRequest  # type: ignore # noqa: E402
from gui.frontend import MainWindow  # type: ignore  # noqa: E402


def take_snapshot(filename: str) -> None:
    """Force the UI to process events, repaint, and grab the primary screen."""
    # Process all pending events multiple times to ensure layout recalculations complete
    for _ in range(3):
        QCoreApplication.processEvents(QEventLoop.ProcessEventsFlag.AllEvents)
    time.sleep(0.3)  # Short pause for physical screen synchronization

    path: Path = Path("docs/images/screenshots")
    path.mkdir(parents=True, exist_ok=True)

    # Explicitly check for screen availability before attempting to grab
    screen = QApplication.primaryScreen()
    if screen is not None:
        pixmap: QPixmap = screen.grabWindow(0)
        pixmap.save(str(path / filename))
        print(f"Captured: {filename}")
    else:
        print(f"Error: Primary screen instance not found. Failed to snap {filename}")


def hover_combo_item(combo: QComboBox, index_to_hover: int) -> None:
    """Programmatically highlights an item in the popup list."""
    combo.showPopup()
    QCoreApplication.processEvents()

    view: QAbstractItemView = combo.view()
    model: QAbstractItemModel = combo.model()

    if index_to_hover < model.rowCount():
        model_index: QModelIndex = model.index(index_to_hover, 0)
        view.setCurrentIndex(model_index)
        view.scrollTo(model_index)

    QCoreApplication.processEvents()
    time.sleep(0.5)


# ==========================================
# REUSABLE SPLIT FUNCTIONS
# ==========================================


def take_tutorial_screenshots(mw: MainWindow) -> None:
    """Captures steps 1 through 4 exactly as written for the tutorial."""
    # ==========================================
    # STEP 1: Get your data in
    # ==========================================
    # 3. Use the Select Recording Session list to pick the specific folder
    hover_combo_item(mw.sidebar.combo_sessions, 1)
    take_snapshot("step1_select_recording_session.png")
    mw.sidebar.combo_sessions.hidePopup()

    # 4. From the Select Video list, pick a file. You should see the video and the skeleton appear.
    hover_combo_item(mw.sidebar.combo_videos, 0)
    take_snapshot("step1_select_video.png")
    mw.sidebar.combo_videos.hidePopup()

    # ==========================================
    # STEP 2: Choose your method
    # ==========================================
    # 1. Go to the Select Ergonomic Method list. 2. Pick REBA
    hover_combo_item(mw.sidebar.combo_method, 0)  # Highlights REBA
    take_snapshot("step2_select_method_reba.png")
    mw.sidebar.combo_method.hidePopup()

    # 3. Click RUN ANALYSIS. Wait for the status bar at the bottom to say it's finished.
    mw.sidebar.combo_method.setCurrentText("REBA")
    mock_request: AnalysisRequest = AnalysisRequest(
        method=AssessmentMethod.REBA,
        data_ref=Path("scripts/assets/mock_reba_analysis_data.csv"),
        export_frames=False,
    )
    mw.run_analysis(analysis_request=mock_request)

    take_snapshot("step2_analysis_started.png")

    # Let UI and status bar update to represent the completed computation state
    time.sleep(10.0)
    take_snapshot("step2_analysis_finished.png")

    # ==========================================
    # STEP 3: Check the video
    # ==========================================
    # 1. Click PLAY / PAUSE. 2. Watch the video to make sure the skeleton is on top.
    for _ in range(20):
        mw._reconnect_video_signals()
        mw.step_video(1)
        QCoreApplication.processEvents(QEventLoop.ProcessEventsFlag.AllEvents)
        mw.canvas.repaint()

    take_snapshot("step3_video_skeleton_overlay.png")

    # ==========================================
    # STEP 4: See the results and save
    # ==========================================
    # 1. Click OPEN REPORT DASHBOARD. A new window will pop up.
    # 2. Look at the Risk Pie Charts...
    mw.report_window.showFullScreen()

    # Critical: give the dashboard layout and chart engine time to paint completely
    time.sleep(1.5)
    take_snapshot("step4_report_dashboard.png")


def take_user_guide_screenshots(mw: MainWindow) -> None:
    """Systematically triggers and captures every button and functional area for the User Guide."""
    # Ensure a clean slate on the main window first
    mw.report_window.close()
    QCoreApplication.processEvents()

    # ==========================================
    # 1. MAIN WINDOW - FILES & RECORDING
    # ==========================================
    # Highlight the primary configuration controls on the sidebar
    take_snapshot("guide_main_window_overview.png")

    # ==========================================
    # 1. MAIN WINDOW - ANALYSIS BUTTONS
    # ==========================================
    # Show the dropdown choices for ergonomic methods (Working vs Coming Soon)
    hover_combo_item(mw.sidebar.combo_method, 0)
    take_snapshot("guide_analysis_method_dropdown.png")
    mw.sidebar.combo_method.hidePopup()

    # ==========================================
    # 1. MAIN WINDOW - VIDEO PLAYER CONTROLS
    # ==========================================
    # Focus and capture the Play/Pause, Browse, and Selection layout
    take_snapshot("guide_video_player_controls.png")

    # ==========================================
    # 2. REPORT DASHBOARD - NUMBERS, CHARTS & SAVE BUTTONS
    # ==========================================
    mw.report_window.showFullScreen()
    # Give complex math plots (Pie Charts, Bar Graphs, Tables) time to draw
    time.sleep(1.5)

    # Capture the full overview showing TOTAL FRAMES, AVG REBA, and Risk Charts
    take_snapshot("guide_dashboard_charts_and_metrics.png")

    # Highlight the document management area (LOAD DATA, EXPORT PDF, EXPORT DOCX)
    # assuming these live in a toolbar/button layout on report_window
    take_snapshot("guide_dashboard_save_and_export_buttons.png")

    # Close dashboard window to return focus back to the primary shell
    mw.report_window.close()
    QCoreApplication.processEvents()

    # ==========================================
    # 3. SETTINGS - SIDEBAR TOGGLE (☰)
    # ==========================================
    # Click ☰ to collapse the menu and verify the viewport contraction expansion
    mw.toggle_sidebar()
    take_snapshot("guide_settings_sidebar_collapsed.png")

    # Restore Sidebar back to default state
    mw.toggle_sidebar()
    QCoreApplication.processEvents()

    # ==========================================
    # 4. SETTINGS - THEME SWITCHER (☀️/🌓)
    # ==========================================
    # Toggle theme from default Dark directly into Light Mode
    mw.toggle_theme()
    take_snapshot("guide_settings_theme_light_mode.png")

    # Revert back to original development system layout (Dark Mode)
    mw.toggle_theme()
    QCoreApplication.processEvents()

    # ==========================================
    # 5. STATUS BAR (BOTTOM LEFT METRICS)
    # ==========================================
    # Zero-in on the bottom left tracking metrics (File parsing state, session counters)
    take_snapshot("guide_status_bar_indicators.png")


# ==========================================
# ORCHESTRATOR
# ==========================================


def run_documentation_flow() -> None:
    app: QApplication = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(cast(str, get_stylesheet()))

    icon_path: Path = cast(Path, ErgoPaths.LOGO)
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    # Initialize Main Window and show fullscreen
    mw: MainWindow = MainWindow()
    mw.showFullScreen()
    QCoreApplication.processEvents()

    # Mocking Backend Data & Roots
    sessions_path: Path = cast(Path, ErgoPaths.SESSIONS)
    mw.handle_select_root = MagicMock()
    sessions: List[str] = mw.backend.set_root_and_scan(sessions_path)
    mw.sidebar.update_sessions(sessions)

    # Setup initial states
    mw.sidebar.combo_sessions.setCurrentText("screenshots_test")
    mw.sidebar.update_videos(["reba_test.mp4"])
    mw.handle_video_selection_changed()

    video_path: str = rf"{sessions_path}/reba_test.mp4"
    mw.backend.load_video_source(video_path)
    time.sleep(1)  # Allow video frame decoding to load initial frame

    # Execute split layout capturing tasks
    take_tutorial_screenshots(mw)
    take_user_guide_screenshots(mw)

    print(
        "\n--- All matching screenshots captured precisely in docs/images/screenshots/ ---"
    )


if __name__ == "__main__":
    run_documentation_flow()
