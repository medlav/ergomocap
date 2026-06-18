import asyncio
import sys
from pathlib import Path
from typing import List, cast
from unittest.mock import MagicMock

from PySide6.QtCore import QCoreApplication, QEventLoop, QModelIndex, QTimer
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QComboBox,
    QMessageBox,
    QWidget,
)

PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from gui.frontend import MainWindow  # type: ignore  # noqa: E402
from gui.theme.style import get_stylesheet  # type: ignore # noqa: E402
from gui.utils.app_paths import ErgoPaths  # type: ignore # noqa: E402
from gui.utils.constants import AssessmentMethod  # type: ignore # noqa: E402
from gui.utils.models import AnalysisRequest  # type: ignore # noqa: E402

BASE_IMAGE_DIR = Path("docs/images")


# ==========================================
# UNIFIED TIMING & CAPTURE HELPERS
# ==========================================


async def settled_wait(seconds: float) -> None:
    """
    Asynchronously yields execution, forcing the Qt event loop to process
    all pending paint, layout, and network events while waiting.
    """
    step = 0.02
    iterations = max(1, int(seconds / step))
    for _ in range(iterations):
        QCoreApplication.processEvents(QEventLoop.ProcessEventsFlag.AllEvents)
        await asyncio.sleep(step)


def capture_snapshot(
    filename: str, subfolder: str = "screenshots", target_widget: QWidget | None = None
) -> None:
    """
    Freezes the UI context instantly to snap a pixel-perfect capture.
    If target_widget is provided, it grabs only that widget. Otherwise, snaps the full screen.
    """
    target_path = BASE_IMAGE_DIR / subfolder
    target_path.mkdir(parents=True, exist_ok=True)
    output_file = target_path / filename

    if target_widget is not None:
        pixmap: QPixmap = target_widget.grab()
        pixmap.save(str(output_file))
        print(f"Captured Widget ➔ [{subfolder}] {filename}")
    else:
        screen = QApplication.primaryScreen()
        if screen is not None:
            pixmap: QPixmap = screen.grabWindow(0)
            pixmap.save(str(output_file))
            print(f"Captured Screen ➔ [{subfolder}] {filename}")
        else:
            print(f"Error: Primary screen not found. Failed to snap {filename}")


async def hover_combo_item(combo: QComboBox, index_to_hover: int) -> None:
    """Programmatically highlights an item in the popup list and awaits rendering."""
    combo.showPopup()
    await settled_wait(0.2)

    view: QAbstractItemView = combo.view()
    model = combo.model()

    if model and index_to_hover < model.rowCount():
        model_index: QModelIndex = model.index(index_to_hover, 0)
        view.setCurrentIndex(model_index)
        view.scrollTo(model_index)

    await settled_wait(0.3)


async def safe_seek_canvas(mw: MainWindow, frame: int) -> None:
    """Safely seeks the canvas and awaits background thread rendering loops."""
    if hasattr(mw, "_handle_canvas_seek"):
        mw._handle_canvas_seek(frame)
        await settled_wait(0.75)  # Unified reliable wait for decoder threads
    else:
        print("WARNING: NO CANVAS SEEK METHOD FOUND")


# ==========================================
# ASYNC SCREENSHOT FLOWS
# ==========================================


async def take_tutorial_screenshots(mw: MainWindow) -> None:
    """Captures steps 1 through 4 exactly as written for the tutorial."""
    print("\n--- Running Tutorial Screenshots ---")

    # STEP 1: Get your data in
    await hover_combo_item(mw.sidebar.combo_sessions, 1)
    capture_snapshot("step1_select_recording_session.png")
    mw.sidebar.combo_sessions.hidePopup()
    await settled_wait(0.1)

    await hover_combo_item(mw.sidebar.combo_videos, 0)
    capture_snapshot("step1_select_video.png")
    mw.sidebar.combo_videos.hidePopup()
    await settled_wait(0.2)

    # STEP 2: Choose your method
    await hover_combo_item(mw.sidebar.combo_method, 0)
    capture_snapshot("step2_select_method_reba.png")
    mw.sidebar.combo_method.hidePopup()

    mw.sidebar.combo_method.setCurrentText("REBA")
    mock_request = AnalysisRequest(
        method=AssessmentMethod.REBA,
        data_ref=Path("scripts/assets/mock_reba_analysis_data.csv"),
        export_frames=False,
    )
    mw.run_analysis(analysis_request=mock_request)
    capture_snapshot("step2_analysis_started.png")

    await settled_wait(0.5)
    capture_snapshot("step2_analysis_finished.png")

    await settled_wait(0.5)
    mw.report_window.close()

    # STEP 3: Check the video
    await safe_seek_canvas(mw, 374)
    capture_snapshot("step3_video_skeleton_overlay.png")
    await settled_wait(0.2)

    # STEP 4: See the results and save
    mw.report_window.showFullScreen()
    await settled_wait(1.5)  # Complex charts need real time to layout
    capture_snapshot("step4_report_dashboard.png")


async def take_user_guide_screenshots(mw: MainWindow) -> None:
    """Systematically triggers and captures every button and functional area for the User Guide."""
    print("\n--- Running User Guide Screenshots ---")
    mw.report_window.close()
    await settled_wait(0.2)

    # 1. MAIN WINDOW OVERVIEW
    capture_snapshot("guide_main_window_overview.png")

    # DROPDOWN
    await hover_combo_item(mw.sidebar.combo_method, 0)
    capture_snapshot("guide_analysis_method_dropdown.png")
    mw.sidebar.combo_method.hidePopup()
    await settled_wait(0.1)

    # CONTROLS & VIDEO SEEKING
    await safe_seek_canvas(mw, 374)

    if hasattr(mw, "step_video"):
        mw.step_video(1)
        await settled_wait(0.1)
        mw.step_video(-1)
        await settled_wait(0.1)

    if hasattr(mw, "handle_toggle_video"):
        mw.handle_toggle_video()  # Play
        await settled_wait(0.2)
        mw.handle_toggle_video()  # Pause to freeze layout frame
        await settled_wait(0.1)

    if hasattr(mw.sidebar, "btn_play_video"):
        mw.sidebar.btn_play_video.setFocus()
        await settled_wait(0.1)

    capture_snapshot("guide_video_player_controls.png")

    # 2. REPORT DASHBOARD
    mw.report_window.showFullScreen()
    await settled_wait(1.5)

    capture_snapshot("guide_dashboard_charts_and_metrics.png")
    capture_snapshot("guide_dashboard_save_and_export_buttons.png")

    mw.report_window.close()
    await settled_wait(0.2)

    # 3. SETTINGS & INTERACTION
    mw.toggle_sidebar()
    await settled_wait(0.3)
    capture_snapshot("guide_settings_sidebar_collapsed.png")

    mw.toggle_sidebar()
    await settled_wait(0.2)

    mw.toggle_theme()
    await settled_wait(0.4)
    capture_snapshot("guide_settings_theme_light_mode.png")

    mw.toggle_theme()
    await settled_wait(0.3)

    capture_snapshot("guide_status_bar_indicators.png")


async def take_review_tutorial_screenshots(mw: MainWindow) -> None:
    """Systematically automates and handles the images/review_tutorial folder items."""
    print("\n--- Running Review Tutorial Screenshots ---")
    folder = "review_tutorial"

    await safe_seek_canvas(mw, 374)

    if not hasattr(mw, "review_window"):
        # Fallback catches if elements aren't loaded
        for name in [
            "review_scope_target",
            "review_joint_angles",
            "review_ergonomic_adjustments",
            "review_apply_changes",
            "review_save_changes",
            "review_video_mode",
        ]:
            capture_snapshot(f"{name}.png", subfolder=folder)
        return

    # STEP 2: Review Video Mode
    if hasattr(mw.sidebar, "btn_review") and hasattr(mw.sidebar.btn_review, "click"):
        mw.sidebar.btn_review.click()
        await settled_wait(0.3)
    capture_snapshot("review_view.png", subfolder=folder)

    # STEP 3: Scope Target
    if hasattr(mw.review_window, "combo_scope"):
        await hover_combo_item(mw.review_window.combo_scope, 0)
    capture_snapshot("review_scope_target.png", subfolder=folder)

    if hasattr(mw.review_window, "combo_scope"):
        mw.review_window.combo_scope.hidePopup()
        await settled_wait(0.1)

    # STEP 4: Joint Angles Table Manipulation
    if hasattr(mw.review_window, "metrics_table"):
        table = mw.review_window.metrics_table
        if table.model() and table.model().rowCount() > 0:
            target_idx = table.model().index(min(5, table.model().rowCount() - 1), 0)
            table.setCurrentIndex(target_idx)
            table.scrollTo(target_idx)
            await settled_wait(0.3)
    capture_snapshot("review_joint_angles.png", subfolder=folder)

    # Scroll down structural interface
    if hasattr(mw.review_window, "scroll_area"):
        scroll_bar = mw.review_window.scroll_area.verticalScrollBar()
        if scroll_bar:
            scroll_bar.setValue(scroll_bar.maximum())
            await settled_wait(0.4)

    # STEP 5: Ergonomic Adjustments
    if hasattr(mw.review_window, "combo_fields"):
        await hover_combo_item(mw.review_window.combo_fields, 0)
    capture_snapshot("review_ergonomic_adjustments.png", subfolder=folder)

    if hasattr(mw.review_window, "combo_fields"):
        mw.review_window.combo_fields.hidePopup()
        await settled_wait(0.1)

    # STEP 6A: Apply Changes
    if hasattr(mw.review_window, "btn_apply"):
        mw.review_window.btn_apply.setFocus()
        mw.review_window.btn_apply.click()
        await settled_wait(0.5)
    capture_snapshot("review_apply_changes.png", subfolder=folder)

    # STEP 6B: Save Changes & Modal Handling Interaction
    if hasattr(mw.review_window, "btn_save"):
        mw.review_window.btn_save.setFocus()

        def handle_msg():
            capture_snapshot("review_save_changes.png", subfolder=folder)
            for w in QApplication.topLevelWidgets():
                if isinstance(w, QMessageBox):
                    w.close()

        QTimer.singleShot(400, handle_msg)
        mw.review_window.btn_save.click()
        await settled_wait(0.6)

    # Close dashboard views completely
    mw.review_window.close()
    await settled_wait(0.2)

    # STEP 7: Toggle Analysis and Review Modes
    if hasattr(mw.sidebar, "radio_analysis") and hasattr(
        mw.sidebar.radio_analysis, "click"
    ):
        mw.sidebar.radio_analysis.click()
        await settled_wait(0.3)

    if hasattr(mw.sidebar, "radio_review") and hasattr(
        mw.sidebar.radio_review, "click"
    ):
        mw.sidebar.radio_review.click()
        await settled_wait(0.3)
        capture_snapshot("review_video_mode.png", subfolder=folder)


# ==========================================
# MAIN ASYNC RUNNER ORCHESTRATOR
# ==========================================


async def main() -> None:
    app: QApplication = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(cast(str, get_stylesheet()))

    icon_path: Path = cast(Path, ErgoPaths.LOGO)
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    mw: MainWindow = MainWindow()
    mw.showFullScreen()
    await settled_wait(0.5)

    # Mock Data Injection
    sessions_path: Path = cast(Path, ErgoPaths.SESSIONS)
    mw.handle_select_root = MagicMock()
    sessions: List[str] = mw.backend.set_root_and_scan(sessions_path)
    mw.sidebar.update_sessions(sessions)

    mw.sidebar.combo_sessions.setCurrentText("screenshots_test")
    mw.sidebar.update_videos(["reba_test.mp4"])
    mw.handle_video_selection_changed()

    video_path: str = rf"{sessions_path}/reba_test.mp4"
    mw.backend.load_video_source(video_path)
    await settled_wait(1.0)  # Let video player decoder initialization rest cleanly

    # Run unified tasks sequentially using async context
    await take_tutorial_screenshots(mw)
    await take_user_guide_screenshots(mw)
    await take_review_tutorial_screenshots(mw)

    print(
        "\n--- All execution complete. Output captured perfectly inside docs/images/ ---"
    )


if __name__ == "__main__":
    asyncio.run(main())
