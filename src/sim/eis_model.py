from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class SimulationParameters:
    rs_ohm: float
    rct_ohm: float
    cdl_f: float
    enable_warburg: bool
    warburg_sigma: float
    f_min_hz: float
    f_max_hz: float
    points_per_decade: int


@dataclass(frozen=True)
class SimulationResult:
    frequency_hz: np.ndarray
    impedance_ohm: np.ndarray

    @property
    def z_real_ohm(self) -> np.ndarray:
        return self.impedance_ohm.real

    @property
    def z_imag_ohm(self) -> np.ndarray:
        return self.impedance_ohm.imag

    @property
    def z_mag_ohm(self) -> np.ndarray:
        return np.abs(self.impedance_ohm)

    @property
    def z_phase_deg(self) -> np.ndarray:
        return np.angle(self.impedance_ohm, deg=True)


def default_parameters() -> SimulationParameters:
    return SimulationParameters(
        rs_ohm=10.0,
        rct_ohm=100.0,
        cdl_f=1e-5,
        enable_warburg=False,
        warburg_sigma=20.0,
        f_min_hz=1.0,
        f_max_hz=1e5,
        points_per_decade=10,
    )


def simulate_eis(params: SimulationParameters) -> SimulationResult:
    _validate_parameters(params)

    decades = np.log10(params.f_max_hz) - np.log10(params.f_min_hz)
    point_count = max(2, int(np.ceil(decades * params.points_per_decade)) + 1)
    frequency_hz = np.logspace(np.log10(params.f_min_hz), np.log10(params.f_max_hz), point_count)
    omega = 2.0 * np.pi * frequency_hz

    capacitor_branch = 1j * omega * params.cdl_f
    parallel_impedance = 1.0 / ((1.0 / params.rct_ohm) + capacitor_branch)
    impedance = params.rs_ohm + parallel_impedance

    if params.enable_warburg:
        impedance = impedance + _warburg_impedance(params.warburg_sigma, omega)

    return SimulationResult(frequency_hz=frequency_hz, impedance_ohm=impedance)


def _validate_parameters(params: SimulationParameters) -> None:
    if params.rs_ohm < 0:
        raise ValueError("Rs must be zero or positive.")
    if params.rct_ohm <= 0:
        raise ValueError("Rct must be greater than zero.")
    if params.cdl_f <= 0:
        raise ValueError("Cdl must be greater than zero.")
    if params.f_min_hz <= 0 or params.f_max_hz <= 0:
        raise ValueError("Frequencies must be greater than zero.")
    if params.f_min_hz >= params.f_max_hz:
        raise ValueError("Minimum frequency must be smaller than maximum frequency.")
    if params.points_per_decade < 2:
        raise ValueError("Points per decade must be at least 2.")
    if params.enable_warburg and params.warburg_sigma <= 0:
        raise ValueError("Warburg sigma must be greater than zero when enabled.")


def _warburg_impedance(sigma: float, omega: np.ndarray) -> np.ndarray:
    return sigma / np.sqrt(1j * omega)
