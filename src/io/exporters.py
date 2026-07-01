from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

from src.sim.eis_model import SimulationResult


def export_spectra_csv(file_path: str | Path, result: SimulationResult) -> None:
    destination = Path(file_path)

    freq = result.frequency_hz if result.frequency_hz is not None else np.array([])
    z_real = result.z_real_ohm
    z_imag = result.z_imag_ohm
    phase = result.z_phase_deg
    cap = result.capacitance_f
    jv_v = result.jv_voltage_v if result.jv_voltage_v is not None else np.array([])
    jv_j = result.jv_current_ma_cm2 if result.jv_current_ma_cm2 is not None else np.array([])

    row_count = max(len(freq), len(jv_v))

    def _value(arr: np.ndarray, idx: int):
        return "" if idx >= len(arr) else arr[idx]

    with destination.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "frequency_hz",
                "Z_real_ohm",
                "Z_imag_ohm",
                "Z_phase_deg",
                "C_farad",
                "JV_voltage_v",
                "JV_current_mA_cm2",
            ]
        )
        for idx in range(row_count):
            writer.writerow(
                [
                    _value(freq, idx),
                    _value(z_real, idx),
                    _value(z_imag, idx),
                    _value(phase, idx),
                    _value(cap, idx),
                    _value(jv_v, idx),
                    _value(jv_j, idx),
                ]
            )
