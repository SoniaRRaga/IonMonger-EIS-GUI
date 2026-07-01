from __future__ import annotations

from pathlib import Path

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from src.io.exporters import export_spectra_csv
from src.sim.eis_model import SimulationParameters, default_parameters, simulate_eis


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("IonMonger EIS GUI")
        self.resize(1200, 750)
        self._last_result = None

        self._build_ui()
        self._apply_defaults()
        self.statusBar().showMessage("Ready")

    def _build_ui(self) -> None:
        central = QWidget()
        root_layout = QHBoxLayout(central)

        controls = self._build_controls()
        plot_panel = self._build_plot_panel()

        root_layout.addWidget(controls, 0)
        root_layout.addWidget(plot_panel, 1)

        self.setCentralWidget(central)

    def _build_controls(self) -> QWidget:
        box = QGroupBox("Simulation Parameters")
        layout = QVBoxLayout(box)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.rs_input = self._line_edit("10", "Series resistance in ohms.")
        self.rct_input = self._line_edit("100", "Charge-transfer resistance in ohms.")
        self.cdl_input = self._line_edit("1e-5", "Double-layer capacitance in farads.")
        self.sigma_input = self._line_edit(
            "20", "Warburg sigma in ohm·s^-0.5. Used only when enabled."
        )
        self.f_min_input = self._line_edit("1", "Minimum frequency in hertz.")
        self.f_max_input = self._line_edit("1e5", "Maximum frequency in hertz.")
        self.ppd_input = QSpinBox()
        self.ppd_input.setRange(2, 200)
        self.ppd_input.setValue(10)
        self.ppd_input.setToolTip("Number of points per decade in the frequency sweep.")

        self.warburg_checkbox = QCheckBox("Enable Warburg element")
        self.warburg_checkbox.setToolTip(
            "Adds a simple semi-infinite diffusion contribution to the impedance."
        )
        self.warburg_checkbox.toggled.connect(self.sigma_input.setEnabled)

        form.addRow("Rs (Ω)", self.rs_input)
        form.addRow("Rct (Ω)", self.rct_input)
        form.addRow("Cdl (F)", self.cdl_input)
        form.addRow(self.warburg_checkbox)
        form.addRow("Warburg σ", self.sigma_input)
        form.addRow("f min (Hz)", self.f_min_input)
        form.addRow("f max (Hz)", self.f_max_input)
        form.addRow("Points / decade", self.ppd_input)

        layout.addLayout(form)

        self.help_label = QLabel(
            "Tip: defaults produce a standard Randles-style EIS spectrum immediately."
        )
        self.help_label.setWordWrap(True)
        layout.addWidget(self.help_label)

        buttons_layout = QVBoxLayout()
        self.run_button = QPushButton("Run simulation")
        self.reset_button = QPushButton("Reset defaults")
        self.export_button = QPushButton("Export CSV")
        self.save_plots_button = QPushButton("Save plots")

        self.run_button.clicked.connect(self.run_simulation)
        self.reset_button.clicked.connect(self.reset_defaults)
        self.export_button.clicked.connect(self.export_csv)
        self.save_plots_button.clicked.connect(self.save_plots)

        self.export_button.setEnabled(False)
        self.save_plots_button.setEnabled(False)

        for button in (
            self.run_button,
            self.reset_button,
            self.export_button,
            self.save_plots_button,
        ):
            buttons_layout.addWidget(button)

        buttons_layout.addStretch(1)
        layout.addLayout(buttons_layout)
        return box

    def _build_plot_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)

        self.figure = Figure(figsize=(8, 6), tight_layout=True)
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)

        self.ax_nyquist = self.figure.add_subplot(2, 2, 1)
        self.ax_bode_mag = self.figure.add_subplot(2, 2, 2)
        self.ax_bode_phase = self.figure.add_subplot(2, 2, 4)

        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        return panel

    def _line_edit(self, value: str, tooltip: str) -> QLineEdit:
        widget = QLineEdit(value)
        widget.setToolTip(tooltip)
        return widget

    def _apply_defaults(self) -> None:
        params = default_parameters()
        self.rs_input.setText(str(params.rs_ohm))
        self.rct_input.setText(str(params.rct_ohm))
        self.cdl_input.setText(f"{params.cdl_f:g}")
        self.warburg_checkbox.setChecked(params.enable_warburg)
        self.sigma_input.setText(str(params.warburg_sigma))
        self.sigma_input.setEnabled(params.enable_warburg)
        self.f_min_input.setText(f"{params.f_min_hz:g}")
        self.f_max_input.setText(f"{params.f_max_hz:g}")
        self.ppd_input.setValue(params.points_per_decade)

    def reset_defaults(self) -> None:
        self._apply_defaults()
        self.statusBar().showMessage("Ready")

    def _read_float(self, field: QLineEdit, label: str) -> float:
        text = field.text().strip()
        try:
            return float(text)
        except ValueError as exc:
            raise ValueError(f"{label} must be a number. Received: {text!r}.") from exc

    def _read_parameters(self) -> SimulationParameters:
        return SimulationParameters(
            rs_ohm=self._read_float(self.rs_input, "Rs"),
            rct_ohm=self._read_float(self.rct_input, "Rct"),
            cdl_f=self._read_float(self.cdl_input, "Cdl"),
            enable_warburg=self.warburg_checkbox.isChecked(),
            warburg_sigma=self._read_float(self.sigma_input, "Warburg sigma"),
            f_min_hz=self._read_float(self.f_min_input, "Minimum frequency"),
            f_max_hz=self._read_float(self.f_max_input, "Maximum frequency"),
            points_per_decade=self.ppd_input.value(),
        )

    def run_simulation(self) -> None:
        self.statusBar().showMessage("Running...")
        try:
            params = self._read_parameters()
            self._last_result = simulate_eis(params)
            self._update_plots()
        except ValueError as exc:
            self._last_result = None
            self.export_button.setEnabled(False)
            self.save_plots_button.setEnabled(False)
            self.statusBar().showMessage("Error")
            QMessageBox.warning(self, "Invalid input", str(exc))
            return
        except Exception as exc:  # pragma: no cover - defensive GUI handling
            self._last_result = None
            self.export_button.setEnabled(False)
            self.save_plots_button.setEnabled(False)
            self.statusBar().showMessage("Error")
            QMessageBox.critical(self, "Simulation failed", str(exc))
            return

        self.export_button.setEnabled(True)
        self.save_plots_button.setEnabled(True)
        self.statusBar().showMessage("Done")

    def _update_plots(self) -> None:
        result = self._last_result
        if result is None:
            return

        self.ax_nyquist.clear()
        self.ax_bode_mag.clear()
        self.ax_bode_phase.clear()

        self.ax_nyquist.plot(result.z_real_ohm, -result.z_imag_ohm, color="#1f77b4")
        self.ax_nyquist.set_title("Nyquist Plot")
        self.ax_nyquist.set_xlabel("Re(Z) [Ω]")
        self.ax_nyquist.set_ylabel("-Im(Z) [Ω]")
        self.ax_nyquist.grid(True)

        self.ax_bode_mag.semilogx(result.frequency_hz, result.z_mag_ohm, color="#ff7f0e")
        self.ax_bode_mag.set_title("Bode Magnitude")
        self.ax_bode_mag.set_xlabel("Frequency [Hz]")
        self.ax_bode_mag.set_ylabel("|Z| [Ω]")
        self.ax_bode_mag.grid(True, which="both")

        self.ax_bode_phase.semilogx(
            result.frequency_hz, result.z_phase_deg, color="#2ca02c"
        )
        self.ax_bode_phase.set_title("Bode Phase")
        self.ax_bode_phase.set_xlabel("Frequency [Hz]")
        self.ax_bode_phase.set_ylabel("Phase [deg]")
        self.ax_bode_phase.grid(True, which="both")

        self.figure.tight_layout()
        self.canvas.draw_idle()

    def export_csv(self) -> None:
        if self._last_result is None:
            QMessageBox.information(self, "No data", "Run a simulation before exporting.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export simulated spectrum",
            str(Path.cwd() / "simulated_eis_spectrum.csv"),
            "CSV files (*.csv)",
        )
        if not file_path:
            return

        export_spectra_csv(file_path, self._last_result)
        self.statusBar().showMessage("CSV exported")

    def save_plots(self) -> None:
        if self._last_result is None:
            QMessageBox.information(self, "No plot", "Run a simulation before saving plots.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save plots",
            str(Path.cwd() / "simulated_eis_plots.png"),
            "PNG files (*.png)",
        )
        if not file_path:
            return

        self.figure.savefig(file_path, dpi=200, bbox_inches="tight")
        self.statusBar().showMessage("Plot image saved")
