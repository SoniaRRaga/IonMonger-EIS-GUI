from __future__ import annotations

import json
from pathlib import Path

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
from matplotlib.gridspec import GridSpec
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.io.exporters import export_spectra_csv
from src.sim.eis_model import SimulationResult
from src.sim.ionmonger_backend import run_ionmonger
from src.sim.parameter_schema import ParameterField, default_values, field_by_key, grouped_schema


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("IonMonger DD GUI")
        self.resize(1400, 850)

        self._last_result: SimulationResult | None = None
        self._field_defs = field_by_key()
        self._widgets: dict[str, QWidget] = {}
        self._row_labels: dict[str, QLabel] = {}

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
        box = QGroupBox("Drift-diffusion parameters")
        layout = QVBoxLayout(box)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search parameters...")
        self.search_input.textChanged.connect(self._apply_filter)
        layout.addWidget(self.search_input)

        self.tabs = QTabWidget()
        for group, fields in grouped_schema().items():
            self.tabs.addTab(self._build_group_tab(fields), group)
        layout.addWidget(self.tabs, 1)

        self.help_label = QLabel(
            "Status flow: Ready → Running MATLAB → Parsing output → Done. "
            "Bode capacitance uses C(f) = -imag(1/Z)/(2πf)."
        )
        self.help_label.setWordWrap(True)
        layout.addWidget(self.help_label)

        buttons = QVBoxLayout()
        self.run_button = QPushButton("Run IonMonger")
        self.reset_button = QPushButton("Reset defaults")
        self.import_json_button = QPushButton("Import JSON")
        self.export_json_button = QPushButton("Export JSON")
        self.export_csv_button = QPushButton("Export CSV")
        self.save_plots_button = QPushButton("Save plots")

        self.run_button.clicked.connect(self.run_simulation)
        self.reset_button.clicked.connect(self.reset_defaults)
        self.import_json_button.clicked.connect(self.import_json)
        self.export_json_button.clicked.connect(self.export_json)
        self.export_csv_button.clicked.connect(self.export_csv)
        self.save_plots_button.clicked.connect(self.save_plots)

        self.export_csv_button.setEnabled(False)
        self.save_plots_button.setEnabled(False)

        for button in (
            self.run_button,
            self.reset_button,
            self.import_json_button,
            self.export_json_button,
            self.export_csv_button,
            self.save_plots_button,
        ):
            buttons.addWidget(button)

        buttons.addStretch(1)
        layout.addLayout(buttons)
        return box

    def _build_group_tab(self, fields: list[ParameterField]) -> QWidget:
        content = QWidget()
        form = QFormLayout(content)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        for field in fields:
            widget = self._create_widget(field)
            label = QLabel(field.label)
            label.setToolTip(field.tooltip)
            widget.setToolTip(field.tooltip)
            form.addRow(label, widget)
            self._widgets[field.key] = widget
            self._row_labels[field.key] = label

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(content)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.addWidget(scroll)
        return container

    def _create_widget(self, field: ParameterField) -> QWidget:
        if field.field_type == "bool":
            return QCheckBox()
        if field.field_type == "choice":
            combo = QComboBox()
            combo.addItems(list(field.choices))
            return combo
        if field.field_type == "multiline":
            editor = QTextEdit()
            editor.setMinimumHeight(80)
            return editor
        return QLineEdit()

    def _build_plot_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Left column: square I-V and square Nyquist.
        # Right column: 1.5× wider for rectangular Bode plots.
        self.figure = Figure(figsize=(10, 7))
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)

        gs = GridSpec(2, 2, figure=self.figure, width_ratios=[1, 1.5],
                      hspace=0.45, wspace=0.35)
        self.ax_jv = self.figure.add_subplot(gs[0, 0])       # top-left
        self.ax_nyquist = self.figure.add_subplot(gs[1, 0])   # bottom-left
        self.ax_bode_phase = self.figure.add_subplot(gs[0, 1])  # top-right
        self.ax_bode_cap = self.figure.add_subplot(gs[1, 1])    # bottom-right

        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        return panel

    def _apply_defaults(self) -> None:
        defaults = default_values()
        for key, field in self._field_defs.items():
            self._set_widget_value(self._widgets[key], field, defaults[key])

    def reset_defaults(self) -> None:
        self._apply_defaults()
        self.statusBar().showMessage("Ready")

    def _apply_filter(self, query: str) -> None:
        text = query.strip().lower()
        for key, field in self._field_defs.items():
            visible = not text or text in key.lower() or text in field.label.lower()
            self._row_labels[key].setVisible(visible)
            self._widgets[key].setVisible(visible)

    def _collect_values(self) -> dict[str, object]:
        values: dict[str, object] = {}
        for key, field in self._field_defs.items():
            raw = self._widget_value(self._widgets[key], field)
            try:
                if field.field_type == "float":
                    values[key] = float(raw)
                elif field.field_type == "int":
                    values[key] = int(raw)
                elif field.field_type == "bool":
                    values[key] = bool(raw)
                else:
                    values[key] = raw
            except ValueError as exc:
                raise ValueError(f"{field.label} has an invalid value: {raw!r}") from exc
        return values

    def _widget_value(self, widget: QWidget, field: ParameterField):
        if field.field_type == "bool":
            return bool(widget.isChecked())  # type: ignore[attr-defined]
        if field.field_type == "choice":
            return str(widget.currentText())  # type: ignore[attr-defined]
        if field.field_type == "multiline":
            return str(widget.toPlainText())  # type: ignore[attr-defined]
        return str(widget.text()).strip()  # type: ignore[attr-defined]

    def _set_widget_value(self, widget: QWidget, field: ParameterField, value: object) -> None:
        if field.field_type == "bool":
            widget.setChecked(bool(value))  # type: ignore[attr-defined]
            return
        if field.field_type == "choice":
            combo: QComboBox = widget  # type: ignore[assignment]
            index = combo.findText(str(value))
            combo.setCurrentIndex(max(0, index))
            return
        if field.field_type == "multiline":
            widget.setPlainText(str(value))  # type: ignore[attr-defined]
            return
        widget.setText(str(value))  # type: ignore[attr-defined]

    def run_simulation(self) -> None:
        self.statusBar().showMessage("Running MATLAB")
        try:
            values = self._collect_values()
            result = run_ionmonger(values, status_callback=self._on_backend_status)
            self._last_result = result
            self._update_plots()
        except ValueError as exc:
            self._last_result = None
            self.export_csv_button.setEnabled(False)
            self.save_plots_button.setEnabled(False)
            self.statusBar().showMessage("Error")
            QMessageBox.warning(self, "Invalid input", str(exc))
            return
        except Exception as exc:  # pragma: no cover - defensive GUI handling
            self._last_result = None
            self.export_csv_button.setEnabled(False)
            self.save_plots_button.setEnabled(False)
            self.statusBar().showMessage("Error")
            QMessageBox.critical(self, "Simulation failed", str(exc))
            return

        self.export_csv_button.setEnabled(True)
        self.save_plots_button.setEnabled(True)
        self.statusBar().showMessage("Done")

    def _on_backend_status(self, status) -> None:
        if status.detail:
            self.statusBar().showMessage(f"{status.step}: {status.detail}")
        else:
            self.statusBar().showMessage(status.step)

    def _update_plots(self) -> None:
        result = self._last_result
        if result is None:
            return

        self.ax_jv.clear()
        self.ax_nyquist.clear()
        self.ax_bode_phase.clear()
        self.ax_bode_cap.clear()

        # --- I-V (top-left) ---
        if result.jv_voltage_v is not None and result.jv_current_ma_cm2 is not None:
            self.ax_jv.plot(result.jv_voltage_v, result.jv_current_ma_cm2, color="#1f77b4")
        else:
            self.ax_jv.text(0.5, 0.5, "No JV data", ha="center", va="center", transform=self.ax_jv.transAxes)
        self.ax_jv.set_title("Current–Voltage (I–V)")
        self.ax_jv.set_xlabel("Voltage, $V$ (V)")
        self.ax_jv.set_ylabel("Current Density, $J$ (mA cm$^{-2}$)")
        self.ax_jv.grid(True)

        # --- Nyquist Z′–Z″ (bottom-left, isometric) ---
        if result.frequency_hz is not None and result.impedance_ohm is not None:
            self.ax_nyquist.plot(result.z_real_ohm, -result.z_imag_ohm, color="#ff7f0e")
            self.ax_bode_phase.semilogx(result.frequency_hz, result.z_phase_deg, color="#2ca02c")
            self.ax_bode_cap.semilogx(result.frequency_hz, result.capacitance_f, color="#d62728")
        else:
            self.ax_nyquist.text(0.5, 0.5, "No EIS data", ha="center", va="center", transform=self.ax_nyquist.transAxes)
            self.ax_bode_phase.text(0.5, 0.5, "No EIS data", ha="center", va="center", transform=self.ax_bode_phase.transAxes)
            self.ax_bode_cap.text(0.5, 0.5, "No EIS data", ha="center", va="center", transform=self.ax_bode_cap.transAxes)

        self.ax_nyquist.set_title("Nyquist ($Z'$–$Z''$)")
        self.ax_nyquist.set_xlabel(r"Real Impedance, $Z'$ ($\Omega$)")
        self.ax_nyquist.set_ylabel(r"Neg. Imaginary Impedance, $-Z''$ ($\Omega$)")
        self.ax_nyquist.set_aspect("equal", adjustable="box")
        self.ax_nyquist.grid(True)

        # --- Phase–Frequency (top-right) ---
        self.ax_bode_phase.set_title("Phase Angle vs. Frequency")
        self.ax_bode_phase.set_xlabel("Frequency, $f$ (Hz)")
        self.ax_bode_phase.set_ylabel("Phase Angle, $\\varphi$ (°)")
        self.ax_bode_phase.grid(True, which="both")

        # --- Capacitance–Frequency (bottom-right) ---
        self.ax_bode_cap.set_title("Capacitance vs. Frequency")
        self.ax_bode_cap.set_xlabel("Frequency, $f$ (Hz)")
        self.ax_bode_cap.set_ylabel("Capacitance, $C(f)$ (F)")
        self.ax_bode_cap.grid(True, which="both")

        self.canvas.draw_idle()

    def import_json(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import parameter set",
            str(Path.cwd()),
            "JSON files (*.json)",
        )
        if not file_path:
            return

        loaded = json.loads(Path(file_path).read_text(encoding="utf-8"))
        for key, value in loaded.items():
            field = self._field_defs.get(key)
            widget = self._widgets.get(key)
            if field and widget:
                self._set_widget_value(widget, field, value)
        self.statusBar().showMessage("Parameter set imported")

    def export_json(self) -> None:
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export parameter set",
            str(Path.cwd() / "ionmonger_parameters.json"),
            "JSON files (*.json)",
        )
        if not file_path:
            return

        values = self._collect_values()
        Path(file_path).write_text(json.dumps(values, indent=2), encoding="utf-8")
        self.statusBar().showMessage("Parameter set exported")

    def export_csv(self) -> None:
        if self._last_result is None:
            QMessageBox.information(self, "No data", "Run a simulation before exporting.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export simulation output",
            str(Path.cwd() / "ionmonger_output.csv"),
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
            str(Path.cwd() / "ionmonger_plots.png"),
            "PNG files (*.png)",
        )
        if not file_path:
            return

        self.figure.savefig(file_path, dpi=200, bbox_inches="tight")
        self.statusBar().showMessage("Plot image saved")
