import sys
from pathlib import Path
import time
from typing import List, cast
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QAbstractItemView,
    QMessageBox,
    QWidget,
)
from PySide6.QtCore import (
    QCoreApplication,
    QEventLoop,
    QAbstractItemModel,
    QModelIndex,
    QTimer,
)
from unittest.mock import MagicMock

PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from gui.utils.app_paths import ErgoPaths  # type: ignore # noqa: E402
from gui.theme.style import get_stylesheet  # type: ignore # noqa: E402
from gui.utils.constants import AssessmentMethod  # type: ignore # noqa: E402
from gui.utils.models import AnalysisRequest  # type: ignore # noqa: E402
from gui.frontend import MainWindow  # type: ignore  # noqa: E402


BASE_IMAGE_DIR = Path("docs/images")


def wait_and_process(seconds: float, iterations: int = 10):
    """Helper to pause execution without freezing the Qt Main Event Loop."""
    step = seconds / iterations
    for _ in range(iterations):
        QCoreApplication.processEvents(QEventLoop.ProcessEventsFlag.AllEvents)
        time.sleep(step)


def take_widget_snapshot(widget: QWidget, folder: str, filename: str) -> None:
    """
    Forces the specific widget to paint itself and saves a pixel-perfect
    image without desktop backgrounds or artifacts.
    """
    wait_and_process(0.5)

    target_path = BASE_IMAGE_DIR / folder
    target_path.mkdir(parents=True, exist_ok=True)

    # widget.grab() is much safer and cleaner than QApplication.primaryScreen().grabWindow(0)
    pixmap: QPixmap = widget.grab()
    output_file = target_path / filename
    pixmap.save(str(output_file))
    print(f"Captured ➔ [{folder}] {filename}")


def take_snapshot(filename: str, subfolder: str = "screenshots") -> None:
    """Force the UI to process events, repaint, and grab the primary screen area."""
    wait_and_process(0.05)  # Short pause for physical screen synchronization

    path: Path = BASE_IMAGE_DIR / subfolder
    path.mkdir(parents=True, exist_ok=True)

    screen = QApplication.primaryScreen()
    if screen is not None:
        pixmap: QPixmap = screen.grabWindow(0)
        pixmap.save(str(path / filename))
        print(f"Captured Screen: {path / filename}")
    else:
        print(f"Error: Primary screen instance not found. Failed to snap {filename}")


def hover_combo_item(combo: QComboBox, index_to_hover: int) -> None:
    """Programmatically highlights an item in the popup list."""
    combo.showPopup()
    wait_and_process(0.2)

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
    wait_and_process(0.1)

    # 4. From the Select Video list, pick a file. You should see the video and the skeleton appear.
    hover_combo_item(mw.sidebar.combo_videos, 0)
    take_snapshot("step1_select_video.png")
    mw.sidebar.combo_videos.hidePopup()
    wait_and_process(0.2)

    QCoreApplication.processEvents()

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
    wait_and_process(0.5)
    take_snapshot("step2_analysis_finished.png")

    # ==========================================
    # STEP 3: Check the video TODO NOTE the numbers order is wrong btw 2 n 3
    # ==========================================
    # Force a direct seek to frame 374 instead of stepping in a choking signal loop
    if hasattr(mw, "_handle_canvas_seek"):
        mw._handle_canvas_seek(374)
        for _ in range(15):
            QCoreApplication.processEvents()
            time.sleep(0.05)

    else:
        print("ERROR: NO CANVAS SEEK METHOD")
        return

    QCoreApplication.processEvents()

    take_snapshot("step3_video_skeleton_overlay.png")
    time.sleep(0.5)

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
    # Seek to target frame and allow the background decoder to paint
    if hasattr(mw, "_handle_canvas_seek"):
        mw._handle_canvas_seek(374)
        for _ in range(10):
            QCoreApplication.processEvents()
            time.sleep(0.05)

    # Fire the step controllers forward and backward to cycle the pipeline frame states
    if hasattr(mw, "step_video"):
        mw.step_video(1)
        QCoreApplication.processEvents()
        time.sleep(0.1)
        mw.step_video(-1)
        QCoreApplication.processEvents()
        time.sleep(0.1)

    # Trigger Play/Pause state and toggle back to prevent playback thread overrun
    if hasattr(mw, "handle_toggle_video"):
        mw.handle_toggle_video()  # Toggle Play
        QCoreApplication.processEvents()
        time.sleep(0.2)
        mw.handle_toggle_video()  # Toggle Pause to freeze state for snapshot
        QCoreApplication.processEvents()

    # Ensure focus lands on the primary controller widget for visibility in the shot
    if hasattr(mw.sidebar, "btn_play_video"):
        mw.sidebar.btn_play_video.setFocus()
        QCoreApplication.processEvents()

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


# =====================================================================
# ADDED NEW: COMPLETE WORKING WORKSPACE FOR REVIEW_TUTORIAL AUTOMATION
# =====================================================================
def take_review_tutorial_screenshots(mw: MainWindow) -> None:
    """Systematically automates and handles the images/review_tutorial folder items."""
    print("\n--- Starting Review Tutorial Automation Execution ---")
    folder = "review_tutorial"

    if hasattr(mw, "_handle_canvas_seek"):
        mw._handle_canvas_seek(374)

        # Give the background worker thread a moment to decode the frame and update the canvas
        for _ in range(15):
            QCoreApplication.processEvents()
            time.sleep(0.05)

    # 2. Snapshot full screen window states for all targeted tutorial steps
    if hasattr(mw, "review_window"):
        # --- STEP 2: Review Video Mode ---
        if hasattr(mw.sidebar, "btn_review") and hasattr(
            mw.sidebar.btn_review, "click"
        ):
            mw.sidebar.btn_review.click()
            QCoreApplication.processEvents()
        take_snapshot("review_view.png", subfolder=folder)

        # --- STEP 3: Scope Target ---
        if hasattr(mw.review_window, "combo_scope"):
            hover_combo_item(mw.review_window.combo_scope, 0)
        take_snapshot("review_scope_target.png", subfolder=folder)
        if hasattr(mw.review_window, "combo_scope"):
            mw.review_window.combo_scope.hidePopup()
            QCoreApplication.processEvents()

        # --- STEP 4: Joint Angles (Scroll & Display Frame Data) ---
        if hasattr(mw.review_window, "metrics_table"):
            table = mw.review_window.metrics_table
            if table.model() and table.model().rowCount() > 0:
                # Scroll down a few rows to show data movement
                target_idx = table.model().index(
                    min(5, table.model().rowCount() - 1), 0
                )
                table.setCurrentIndex(target_idx)
                table.scrollTo(target_idx)
                QCoreApplication.processEvents()
                time.sleep(0.3)
        take_snapshot("review_joint_angles.png", subfolder=folder)

        # ====================================================================
        # SCROLL DOWN TO EXPOSE SECTIONS 2, 3, 4 & STATUS BAR
        # ====================================================================
        if hasattr(mw.review_window, "scroll_area"):
            scroll_bar = mw.review_window.scroll_area.verticalScrollBar()
            if scroll_bar:
                # Force the scrollbar to its absolute maximum position
                scroll_bar.setValue(scroll_bar.maximum())
                # Let layout engine update, paint, and sync the viewport shifts
                QCoreApplication.processEvents()
                time.sleep(0.5)

        # --- STEP 5: Ergonomic Adjustments ---
        if hasattr(mw.review_window, "combo_fields"):
            hover_combo_item(mw.review_window.combo_fields, 0)
        take_snapshot("review_ergonomic_adjustments.png", subfolder=folder)
        if hasattr(mw.review_window, "combo_fields"):
            mw.review_window.combo_fields.hidePopup()
            QCoreApplication.processEvents()

        # ====================================================================
        # --- STEP 6: Action Buttons (WITH ACTIVE TRIGGERS & MODAL HANDLING)
        # ====================================================================

        # 6A: Apply Changes & wait for status update
        if hasattr(mw.review_window, "btn_apply"):
            mw.review_window.btn_apply.setFocus()
            mw.review_window.btn_apply.click()

            # Inline wait loop for the backend to process the status label
            for _ in range(15):
                QCoreApplication.processEvents()
                time.sleep(0.1)

        take_snapshot("review_apply_changes.png", subfolder=folder)

        # 6B: Save Changes & handle blocking QMessageBox concisely
        if hasattr(mw.review_window, "btn_save"):
            mw.review_window.btn_save.setFocus()

            def handle_msg():
                QCoreApplication.processEvents()
                time.sleep(0.3)
                take_snapshot("review_save_changes.png", subfolder=folder)
                time.sleep(0.3)
                # Hunt down and close any active QMessageBox dialogs
                [
                    w.close()
                    for w in QApplication.topLevelWidgets()
                    if isinstance(w, QMessageBox)
                ]

            QTimer.singleShot(500, handle_msg)
            mw.review_window.btn_save.click()
            QCoreApplication.processEvents()

        # Return context back to the layout state runner
        mw.review_window.close()
        QCoreApplication.processEvents()

        # --- STEP 7: Toggle Analysis and Review Modes ---
        if hasattr(mw.sidebar, "radio_analysis") and hasattr(
            mw.sidebar.radio_analysis, "click"
        ):
            mw.sidebar.radio_analysis.click()
            QCoreApplication.processEvents()
            # take_snapshot("sidebar_analysis_mode.png", subfolder=folder)
            time.sleep(0.5)

        if hasattr(mw.sidebar, "radio_review") and hasattr(
            mw.sidebar.radio_review, "click"
        ):
            mw.sidebar.radio_review.click()
            time.sleep(0.5)
            QCoreApplication.processEvents()
            take_snapshot("review_video_mode.png", subfolder=folder)
            time.sleep(1)
    else:
        # Fallback to general window context screenshots if variables aren't initialized

        take_snapshot("review_scope_target.png", subfolder=folder)
        take_snapshot("review_joint_angles.png", subfolder=folder)
        take_snapshot("review_ergonomic_adjustments.png", subfolder=folder)
        take_snapshot("review_apply_changes.png", subfolder=folder)
        take_snapshot("review_save_changes.png", subfolder=folder)
        take_snapshot("review_video_mode.png", subfolder=folder)


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
    take_review_tutorial_screenshots(mw)

    print(
        "\n--- All matching screenshots captured precisely in docs/images/screenshots/ ---"
    )


if __name__ == "__main__":
    run_documentation_flow()
