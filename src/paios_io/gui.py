"""Minimal PySide6 batch converter: python -m src.paios_io.gui"""

from __future__ import annotations

import sys

from PySide6.QtWidgets import (
    QApplication, QCheckBox, QFileDialog, QHBoxLayout, QLabel, QListWidget,
    QPushButton, QTextEdit, QVBoxLayout, QWidget,
)

from .exporters import convert_files


class Window(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PAIOS -> ZView converter")
        self.out_dir = ""
        self.files = QListWidget()
        self.log = QTextEdit(readOnly=True)
        self.out_label = QLabel("Output folder: (not set)")
        self.neg = QCheckBox("Negate Z'' (flip sign convention)")
        add, out, go = QPushButton("Add files..."), QPushButton("Output folder..."), QPushButton("Export")
        add.clicked.connect(self.add)
        out.clicked.connect(self.pick_out)
        go.clicked.connect(self.export)
        row = QHBoxLayout()
        for b in (add, out, go):
            row.addWidget(b)
        lay = QVBoxLayout(self)
        for w in (self.files, self.out_label, self.neg):
            lay.addWidget(w)
        lay.addLayout(row)
        lay.addWidget(self.log)

    def add(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Select PAIOS files")
        self.files.addItems(paths)

    def pick_out(self):
        d = QFileDialog.getExistingDirectory(self, "Output folder")
        if d:
            self.out_dir = d
            self.out_label.setText(f"Output folder: {d}")

    def export(self):
        if not self.out_dir or not self.files.count():
            self.log.append("Select files and an output folder first.")
            return
        paths = [self.files.item(i).text() for i in range(self.files.count())]
        convert_files(paths, self.out_dir, negate_imag=self.neg.isChecked(), log=self.log.append)


def main() -> int:
    app = QApplication(sys.argv)
    w = Window()
    w.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
