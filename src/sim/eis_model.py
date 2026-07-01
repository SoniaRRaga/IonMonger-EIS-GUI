from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class SimulationResult:
    frequency_hz: np.ndarray | None = None
    impedance_ohm: np.ndarray | None = None
    jv_voltage_v: np.ndarray | None = None
    jv_current_ma_cm2: np.ndarray | None = None

    @property
    def z_real_ohm(self) -> np.ndarray:
        return np.array([]) if self.impedance_ohm is None else self.impedance_ohm.real

    @property
    def z_imag_ohm(self) -> np.ndarray:
        return np.array([]) if self.impedance_ohm is None else self.impedance_ohm.imag

    @property
    def z_phase_deg(self) -> np.ndarray:
        return np.array([]) if self.impedance_ohm is None else np.angle(self.impedance_ohm, deg=True)

    @property
    def capacitance_f(self) -> np.ndarray:
        if self.impedance_ohm is None or self.frequency_hz is None:
            return np.array([])
        y = 1.0 / self.impedance_ohm
        omega = 2.0 * np.pi * self.frequency_hz
        return -np.imag(y) / omega


def validate_inputs(values: dict[str, object]) -> None:
    mode = str(values.get("measurement_mode", "eis"))
    if mode not in {"eis", "jv"}:
        raise ValueError("Measurement mode must be either 'eis' or 'jv'.")

    if not str(values.get("matlab_command", "")).strip():
        raise ValueError("MATLAB command cannot be empty.")

    if not str(values.get("ionmonger_root", "")).strip():
        raise ValueError("IonMonger root folder is required.")

    _require_positive(values, "N", integer=True)
    _require_positive(values, "atol")
    _require_positive(values, "rtol")

    if mode == "eis":
        _require_positive(values, "eis_fmin")
        _require_positive(values, "eis_fmax")
        _require_positive(values, "eis_vac")
        _require_non_negative(values, "eis_nfreq", integer=True)
        _require_positive(values, "eis_nwaves", integer=True)
        fmin = float(values["eis_fmin"])
        fmax = float(values["eis_fmax"])
        if fmin >= fmax:
            raise ValueError("EIS fmin must be smaller than fmax.")

    if mode == "jv":
        _require_positive(values, "jv_scan_rate")


def _require_positive(values: dict[str, object], key: str, integer: bool = False) -> None:
    number = int(values[key]) if integer else float(values[key])
    if number <= 0:
        raise ValueError(f"{key} must be greater than zero.")


def _require_non_negative(values: dict[str, object], key: str, integer: bool = False) -> None:
    number = int(values[key]) if integer else float(values[key])
    if number < 0:
        raise ValueError(f"{key} must be non-negative.")
