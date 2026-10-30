"""
PROJECT KYOKKO
Gesture-Controlled Invisibility Virtual Camera
Main Entrypoint
"""

import os
import sys
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication
from services.logger_service import logger
from ui.main_window import MainWindow


def main():
    # Enable High DPI scaling
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("KYOKKO")
    app.setOrganizationName("KYOKKO Studio")
    app.setApplicationVersion("1.0.0")

    logger.info("APP", "Launching PROJECT KYOKKO v1.0.0...")

    window = MainWindow()
    window.show()

    try:
        sys.exit(app.exec())
    except Exception as e:
        logger.error("APP", f"Unhandled application exception: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
