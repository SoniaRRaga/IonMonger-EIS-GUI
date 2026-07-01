from __future__ import annotations

import csv
from pathlib import Path

from src.sim.eis_model import SimulationResult


def export_spectra_csv(file_path: str | Path, result: SimulationResult) -> None:
    destination = Path(file_path)
    with destination.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "frequency_hz",
                "Z_real_ohm",
                "Z_imag_ohm",
                "Z_mag_ohm",
                "Z_phase_deg",
            ]
        )
        for row in zip(
            result.frequency_hz,
            result.z_real_ohm,
            result.z_imag_ohm,
            result.z_mag_ohm,
            result.z_phase_deg,
        ):
            writer.writerow(row)
