"""Main entry point for the beginner-friendly EIS desktop application."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.gui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("IonMonger EIS GUI")
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
