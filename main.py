#!/usr/bin/env python3
"""JRPaint - A cross-platform paint application inspired by classic Microsoft Paint."""

import sys
import os
import logging
import traceback
import faulthandler
from datetime import datetime

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtGui import QColor, QPalette

# ── Logging setup ────────────────────────────────────────────────────────────
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, f"jrpaint_{datetime.now():%Y%m%d_%H%M%S}.log")

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s – %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stderr),
    ],
)
log = logging.getLogger("jrpaint")


def exception_hook(exc_type, exc_value, exc_tb):
    """Global handler for uncaught exceptions — logs and shows a dialog."""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_tb)
        return

    tb_text = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    log.critical("Uncaught exception:\n%s", tb_text)

    # Try to show a dialog if a QApplication exists
    app = QApplication.instance()
    if app:
        dialog = QMessageBox()
        dialog.setIcon(QMessageBox.Icon.Critical)
        dialog.setWindowTitle("JRPaint – Error")
        dialog.setText("An unexpected error occurred.")
        dialog.setInformativeText(str(exc_value))
        dialog.setDetailedText(tb_text)
        dialog.addButton("Copy to Clipboard", QMessageBox.ButtonRole.ActionRole)
        dialog.addButton(QMessageBox.StandardButton.Close)
        result = dialog.exec()
        # If the first button (Copy) was clicked
        if dialog.clickedButton() != dialog.button(QMessageBox.StandardButton.Close):
            QApplication.clipboard().setText(tb_text)


sys.excepthook = exception_hook


# ── Dark theme ───────────────────────────────────────────────────────────────
def apply_dark_theme(app: QApplication):
    from jrpaint.icon_loader import get_theme_color
    app_bg = QColor(get_theme_color("app_background", "#2D2D30"))
    btn_bg = QColor(get_theme_color("tool_button_background", "#4A4A4E"))

    app.setStyle("Fusion")
    p = app.palette()
    p.setColor(p.ColorRole.Window, app_bg)
    p.setColor(p.ColorRole.WindowText, QColor(220, 220, 220))
    p.setColor(p.ColorRole.Base, QColor(30, 30, 30))
    p.setColor(p.ColorRole.AlternateBase, app_bg)
    p.setColor(p.ColorRole.Text, QColor(220, 220, 220))
    p.setColor(p.ColorRole.Button, btn_bg)
    p.setColor(p.ColorRole.ButtonText, QColor(220, 220, 220))
    p.setColor(p.ColorRole.BrightText, QColor(255, 255, 255))
    p.setColor(p.ColorRole.Highlight, QColor(42, 130, 218))
    p.setColor(p.ColorRole.HighlightedText, QColor(255, 255, 255))
    p.setColor(p.ColorRole.ToolTipBase, QColor(60, 60, 60))
    p.setColor(p.ColorRole.ToolTipText, QColor(220, 220, 220))
    p.setColor(p.ColorRole.PlaceholderText, QColor(128, 128, 128))
    p.setColor(p.ColorRole.Light, QColor(70, 70, 70))
    p.setColor(p.ColorRole.Midlight, QColor(60, 60, 60))
    p.setColor(p.ColorRole.Dark, QColor(30, 30, 30))
    p.setColor(p.ColorRole.Mid, QColor(45, 45, 48))
    p.setColor(p.ColorRole.Shadow, QColor(20, 20, 20))
    p.setColor(QPalette.ColorGroup.Disabled, p.ColorRole.WindowText, QColor(128, 128, 128))
    p.setColor(QPalette.ColorGroup.Disabled, p.ColorRole.Text, QColor(128, 128, 128))
    p.setColor(QPalette.ColorGroup.Disabled, p.ColorRole.ButtonText, QColor(128, 128, 128))
    app.setPalette(p)


# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    # Enable faulthandler to dump tracebacks on segfaults/aborts
    fault_log_path = os.path.join(LOG_DIR, "crash.log")
    fault_log_file = open(fault_log_path, "w")
    faulthandler.enable(file=fault_log_file, all_threads=True)
    # Also dump to stderr
    faulthandler.enable(file=sys.stderr, all_threads=True)

    log.info("Starting JRPaint  (log → %s)", LOG_FILE)
    log.info("Faulthandler crash log → %s", fault_log_path)

    app = QApplication(sys.argv)
    apply_dark_theme(app)

    from jrpaint.main_window import MainWindow
    window = MainWindow()
    window.show()

    log.info("Window shown – entering event loop")
    ret = app.exec()
    log.info("Exiting with code %d", ret)
    fault_log_file.close()
    sys.exit(ret)


if __name__ == "__main__":
    main()
