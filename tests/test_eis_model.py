import numpy as np
import pytest

from src.io.exporters import export_spectra_csv
from src.sim.eis_model import SimulationParameters, simulate_eis


def test_simulate_eis_matches_parallel_rc_limits() -> None:
    params = SimulationParameters(
        rs_ohm=10.0,
        rct_ohm=100.0,
        cdl_f=1e-5,
        enable_warburg=False,
        warburg_sigma=20.0,
        f_min_hz=1.0,
        f_max_hz=1e5,
        points_per_decade=5,
    )

    result = simulate_eis(params)

    assert len(result.frequency_hz) == 26
    assert result.z_real_ohm[0] > result.z_real_ohm[-1]
    assert pytest.approx(110.0, rel=1e-3) == result.z_real_ohm[0]
    assert pytest.approx(10.0, rel=1e-2) == result.z_real_ohm[-1]
    assert np.all(result.z_mag_ohm > 0)


def test_warburg_adds_more_negative_imaginary_component() -> None:
    base = SimulationParameters(
        rs_ohm=10.0,
        rct_ohm=100.0,
        cdl_f=1e-5,
        enable_warburg=False,
        warburg_sigma=20.0,
        f_min_hz=1.0,
        f_max_hz=1e5,
        points_per_decade=5,
    )
    with_warburg = SimulationParameters(**{**base.__dict__, "enable_warburg": True})

    result_base = simulate_eis(base)
    result_warburg = simulate_eis(with_warburg)

    assert np.allclose(result_base.frequency_hz, result_warburg.frequency_hz)
    assert np.any(result_warburg.z_imag_ohm < result_base.z_imag_ohm)


def test_invalid_frequency_range_raises_helpful_error() -> None:
    params = SimulationParameters(
        rs_ohm=10.0,
        rct_ohm=100.0,
        cdl_f=1e-5,
        enable_warburg=False,
        warburg_sigma=20.0,
        f_min_hz=1000.0,
        f_max_hz=10.0,
        points_per_decade=5,
    )

    with pytest.raises(ValueError, match="Minimum frequency must be smaller"):
        simulate_eis(params)


def test_csv_export_writes_expected_columns(tmp_path) -> None:
    params = SimulationParameters(
        rs_ohm=10.0,
        rct_ohm=100.0,
        cdl_f=1e-5,
        enable_warburg=False,
        warburg_sigma=20.0,
        f_min_hz=1.0,
        f_max_hz=100.0,
        points_per_decade=2,
    )

    result = simulate_eis(params)
    output = tmp_path / "spectrum.csv"
    export_spectra_csv(output, result)

    rows = output.read_text(encoding="utf-8").strip().splitlines()
    assert rows[0] == "frequency_hz,Z_real_ohm,Z_imag_ohm,Z_mag_ohm,Z_phase_deg"
    assert len(rows) == len(result.frequency_hz) + 1
