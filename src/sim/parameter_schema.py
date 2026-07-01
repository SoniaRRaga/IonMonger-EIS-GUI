from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ParameterField:
    key: str
    label: str
    group: str
    field_type: str
    default: object
    tooltip: str
    choices: tuple[str, ...] = ()


SCHEMA: tuple[ParameterField, ...] = (
    ParameterField("ionmonger_root", "IonMonger root", "Protocol & measurement mode", "path", "", "Folder containing master.m and Code/"),
    ParameterField("matlab_command", "MATLAB command", "Protocol & measurement mode", "str", "matlab", "MATLAB executable command used for non-interactive batch runs."),
    ParameterField("measurement_mode", "Measurement mode", "Protocol & measurement mode", "choice", "eis", "Choose impedance spectroscopy or JV/transient protocol.", ("eis", "jv")),
    ParameterField("light_intensity", "Light intensity (Sun eq.)", "Protocol & measurement mode", "float", 1.0, "Constant light intensity used in construct_protocol."),
    ParameterField("time_spacing", "time_spacing", "Protocol & measurement mode", "choice", "lin", "Spacing of section time points ('lin' or 'log').", ("lin", "log")),
    ParameterField("additional_matlab_lines", "Extra MATLAB lines", "Protocol & measurement mode", "multiline", "", "Optional raw MATLAB lines inserted before non-dimensionalisation for extension variables."),
    ParameterField("eis_fmin", "fmin (Hz)", "EIS settings", "float", 1e-4, "Minimum impedance frequency. Must be > 0."),
    ParameterField("eis_fmax", "fmax (Hz)", "EIS settings", "float", 1e7, "Maximum impedance frequency. Must be > fmin."),
    ParameterField("eis_vdc", "Vdc (V)", "EIS settings", "float", 0.9, "DC bias voltage for impedance protocol."),
    ParameterField("eis_vac", "Vac (V)", "EIS settings", "float", 10e-3, "Small-signal AC perturbation amplitude."),
    ParameterField("eis_nfreq", "nfreq", "EIS settings", "int", 64, "Number of sampled frequencies (non-negative integer)."),
    ParameterField("eis_nwaves", "nwaves", "EIS settings", "int", 5, "Number of complete sine waves at each frequency."),
    ParameterField("reduced_output", "reduced_output", "EIS settings", "bool", True, "When true, IS_solver returns compact output with freqs/R/X."),
    ParameterField("jv_v_start", "JV start voltage (V)", "Protocol & measurement mode", "float", 1.2, "Starting voltage for JV sweep protocol."),
    ParameterField("jv_v_end", "JV end voltage (V)", "Protocol & measurement mode", "float", 0.0, "Intermediate JV voltage before return sweep."),
    ParameterField("jv_scan_rate", "JV scan rate (V/s)", "Protocol & measurement mode", "float", 0.1, "Scan rate used to build linear JV sections."),
    ParameterField("N", "N", "Solver / numerics", "int", 400, "Number of finite element sub-intervals."),
    ParameterField("atol", "atol", "Solver / numerics", "float", 1e-10, "Absolute tolerance for ode15s."),
    ParameterField("rtol", "rtol", "Solver / numerics", "float", 1e-6, "Relative tolerance for ode15s."),
    ParameterField("Verbose", "Verbose", "Solver / numerics", "bool", True, "Enable MATLAB progress output and protocol plots."),
    ParameterField("UseSplits", "UseSplits", "Solver / numerics", "bool", True, "Run ode15s split-by-section as recommended in GUIDE."),
    ParameterField("workfolder", "workfolder", "Solver / numerics", "str", "./Data/", "Output folder used by master.m; overwritten to run workspace during execution."),
    ParameterField("T", "T (K)", "Layer / material / device", "float", 298.0, "Temperature."),
    ParameterField("b", "b (m)", "Layer / material / device", "float", 400e-9, "Perovskite layer width."),
    ParameterField("epsp_over_eps0", "epsp / eps0", "Layer / material / device", "float", 24.1, "Perovskite relative permittivity multiplier."),
    ParameterField("alpha", "alpha (m^-1)", "Layer / material / device", "float", 1.3e7, "Absorption coefficient."),
    ParameterField("Ec", "Ec (eV)", "Layer / material / device", "float", -3.7, "Conduction band minimum."),
    ParameterField("Ev", "Ev (eV)", "Layer / material / device", "float", -5.4, "Valence band maximum."),
    ParameterField("Dn", "Dn (m^2/s)", "Layer / material / device", "float", 1.7e-4, "Electron diffusion coefficient in perovskite."),
    ParameterField("Dp", "Dp (m^2/s)", "Layer / material / device", "float", 1.7e-4, "Hole diffusion coefficient in perovskite."),
    ParameterField("N0", "N0 (m^-3)", "Layer / material / device", "float", 1.6e25, "Ion vacancy density."),
    ParameterField("DIinf", "DIinf (m^2/s)", "Layer / material / device", "float", 6.5e-8, "High-temperature vacancy diffusion coefficient."),
    ParameterField("EAI", "EAI (eV)", "Layer / material / device", "float", 0.58, "Iodide vacancy activation energy."),
    ParameterField("inverted", "inverted", "Layer / material / device", "bool", False, "Use inverted architecture (light through HTL)."),
    ParameterField("dE", "dE (m^-3)", "Layer / material / device", "float", 1e24, "Effective ETL doping density."),
    ParameterField("gcE", "gcE (m^-3)", "Layer / material / device", "float", 5e25, "ETL conduction band effective DOS."),
    ParameterField("EcE", "EcE (eV)", "Layer / material / device", "float", -4.0, "ETL conduction band reference energy."),
    ParameterField("bE", "bE (m)", "Layer / material / device", "float", 100e-9, "ETL width."),
    ParameterField("epsE_over_eps0", "epsE / eps0", "Layer / material / device", "float", 10.0, "ETL relative permittivity multiplier."),
    ParameterField("DE", "DE (m^2/s)", "Layer / material / device", "float", 1e-5, "ETL electron diffusion coefficient."),
    ParameterField("dH", "dH (m^-3)", "Layer / material / device", "float", 1e24, "Effective HTL doping density."),
    ParameterField("gvH", "gvH (m^-3)", "Layer / material / device", "float", 5e25, "HTL valence band effective DOS."),
    ParameterField("EvH", "EvH (eV)", "Layer / material / device", "float", -5.1, "HTL valence band reference energy."),
    ParameterField("bH", "bH (m)", "Layer / material / device", "float", 200e-9, "HTL width."),
    ParameterField("epsH_over_eps0", "epsH / eps0", "Layer / material / device", "float", 3.0, "HTL relative permittivity multiplier."),
    ParameterField("DH", "DH (m^2/s)", "Layer / material / device", "float", 1e-6, "HTL hole diffusion coefficient."),
    ParameterField("tn", "tn (s)", "Layer / material / device", "float", 3e-9, "Electron pseudo-lifetime for SRH."),
    ParameterField("tp", "tp (s)", "Layer / material / device", "float", 3e-7, "Hole pseudo-lifetime for SRH."),
    ParameterField("beta", "beta (m^3/s)", "Layer / material / device", "float", 0.0, "Bulk bimolecular recombination rate."),
    ParameterField("betaE", "betaE (m^3/s)", "Layer / material / device", "float", 0.0, "ETL/perovskite interface bimolecular rate."),
    ParameterField("betaH", "betaH (m^3/s)", "Layer / material / device", "float", 0.0, "Perovskite/HTL interface bimolecular rate."),
    ParameterField("vnE", "vnE (m/s)", "Layer / material / device", "float", 1e5, "ETL interface electron SRH velocity."),
    ParameterField("vpE", "vpE (m/s)", "Layer / material / device", "float", 10.0, "ETL interface hole SRH velocity."),
    ParameterField("vnH", "vnH (m/s)", "Layer / material / device", "float", 0.1, "HTL interface electron SRH velocity."),
    ParameterField("vpH", "vpH (m/s)", "Layer / material / device", "float", 1e5, "HTL interface hole SRH velocity."),
    ParameterField("etl_band", "ETL band", "Statistics (ETL/HTL)", "choice", "parabolic", "ETL band model from GUIDE.", ("parabolic", "Gaussian")),
    ParameterField("etl_distribution", "ETL distribution", "Statistics (ETL/HTL)", "choice", "Boltzmann", "ETL carrier distribution.", ("Boltzmann", "FermiDirac")),
    ParameterField("etl_s", "ETL Gaussian s", "Statistics (ETL/HTL)", "float", 0.0, "Gaussian band width for ETL (only if ETL band is Gaussian)."),
    ParameterField("htl_band", "HTL band", "Statistics (ETL/HTL)", "choice", "Gaussian", "HTL band model from GUIDE.", ("parabolic", "Gaussian")),
    ParameterField("htl_distribution", "HTL distribution", "Statistics (ETL/HTL)", "choice", "Boltzmann", "HTL carrier distribution.", ("Boltzmann", "FermiDirac")),
    ParameterField("htl_s", "HTL Gaussian s", "Statistics (ETL/HTL)", "float", 3.0, "Gaussian band width for HTL (only if HTL band is Gaussian)."),
    ParameterField("EfE", "EfE (eV) optional", "Statistics (ETL/HTL)", "float", -4.1, "ETL equilibrium QFL used for degenerate statistics workflows."),
    ParameterField("EfH", "EfH (eV) optional", "Statistics (ETL/HTL)", "float", -4.9, "HTL equilibrium QFL used for degenerate statistics workflows."),
)


def default_values() -> dict[str, object]:
    return {field.key: field.default for field in SCHEMA}


def grouped_schema() -> dict[str, list[ParameterField]]:
    grouped: dict[str, list[ParameterField]] = {}
    for field in SCHEMA:
        grouped.setdefault(field.group, []).append(field)
    return grouped


def field_by_key() -> dict[str, ParameterField]:
    return {field.key: field for field in SCHEMA}
