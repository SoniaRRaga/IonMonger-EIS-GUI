from pathlib import Path

import numpy as np
import pytest

from src.io.exporters import export_spectra_csv
from src.sim.eis_model import SimulationResult, validate_inputs
from src.sim.ionmonger_backend import preview_generated_parameters
from src.sim.parameter_schema import default_values


def test_validate_inputs_rejects_invalid_eis_bounds() -> None:
    values = default_values()
    values.update(
        {
            "ionmonger_root": "/tmp/ionmonger",
            "matlab_command": "matlab",
            "measurement_mode": "eis",
            "eis_fmin": 100.0,
            "eis_fmax": 10.0,
        }
    )

    with pytest.raises(ValueError, match="fmin"):
        validate_inputs(values)


def test_capacitance_computation_matches_definition() -> None:
    freq = np.array([1.0, 10.0])
    z = np.array([2.0 - 1.0j, 3.0 - 0.5j])
    result = SimulationResult(frequency_hz=freq, impedance_ohm=z)

    expected = -np.imag(1.0 / z) / (2.0 * np.pi * freq)
    assert np.allclose(result.capacitance_f, expected)


def test_csv_export_writes_combined_columns(tmp_path: Path) -> None:
    result = SimulationResult(
        frequency_hz=np.array([1.0]),
        impedance_ohm=np.array([5.0 - 2.0j]),
        jv_voltage_v=np.array([0.9]),
        jv_current_ma_cm2=np.array([20.0]),
    )

    output = tmp_path / "spectrum.csv"
    export_spectra_csv(output, result)

    rows = output.read_text(encoding="utf-8").strip().splitlines()
    assert rows[0] == "frequency_hz,Z_real_ohm,Z_imag_ohm,Z_phase_deg,C_farad,JV_voltage_v,JV_current_mA_cm2"
    assert len(rows) == 2


def test_generated_parameter_preview_contains_impedance_and_stats() -> None:
    values = default_values()
    values.update(
        {
            "measurement_mode": "eis",
            "eis_fmin": 1e-4,
            "eis_fmax": 1e7,
            "eis_vdc": 0.9,
            "eis_vac": 10e-3,
            "eis_nfreq": 64,
            "eis_nwaves": 5,
        }
    )

    text = preview_generated_parameters(values, Path("/tmp/run"))

    assert "applied_voltage = {'impedance'" in text
    assert "stats.ETL = struct(" in text
    assert "stats.HTL = struct(" in text
    assert "reduced_output = true" in text
