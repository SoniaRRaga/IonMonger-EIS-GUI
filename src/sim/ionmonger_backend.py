from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import subprocess
import tempfile

import h5py
import numpy as np
from scipy.io import loadmat

from src.sim.eis_model import SimulationResult, validate_inputs


@dataclass(frozen=True)
class BackendStatus:
    step: str
    detail: str = ""


def run_ionmonger(values: dict[str, object], status_callback=None) -> SimulationResult:
    validate_inputs(values)

    ionmonger_root = Path(str(values["ionmonger_root"])).expanduser().resolve()
    if not (ionmonger_root / "master.m").exists():
        raise ValueError("IonMonger root must contain master.m.")

    with tempfile.TemporaryDirectory(prefix="ionmonger_run_") as tmp:
        workspace = Path(tmp)
        _emit(status_callback, "Preparing", "Generating parameters.m")
        _write_parameters_file(ionmonger_root, workspace, values)
        _write_batch_script(ionmonger_root, workspace)

        _emit(status_callback, "Running MATLAB", "Executing master.m in batch mode")
        command = [str(values["matlab_command"]), "-batch", "run('run_ionmonger_batch.m')"]
        proc = subprocess.run(
            command,
            cwd=workspace,
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            raise RuntimeError(_format_matlab_error(proc.stdout, proc.stderr))

        output_mat = workspace / "simulation.mat"
        if not output_mat.exists():
            raise RuntimeError(
                "MATLAB finished without producing simulation.mat. "
                "Check master.m/parameters.m settings and path configuration."
            )

        _emit(status_callback, "Parsing output", "Loading simulation.mat")
        return _parse_mat_output(output_mat)


def _emit(callback, step: str, detail: str) -> None:
    if callback is not None:
        callback(BackendStatus(step=step, detail=detail))


def _format_matlab_error(stdout: str, stderr: str) -> str:
    text = (stdout or "") + "\n" + (stderr or "")
    guidance = []
    if "Unable to meet integration tolerances" in text or "Need a better guess y0" in text:
        guidance.append("Try adjusting N, atol, and rtol in Solver/numerics.")
    if "master" in text and "Undefined function" in text:
        guidance.append("Verify IonMonger root points to the folder containing master.m.")
    if "matlab" in text.lower() and "not found" in text.lower():
        guidance.append("Verify MATLAB command (default: matlab) in settings.")

    compact = "\n".join(line for line in text.splitlines() if line.strip())
    message = "MATLAB execution failed."
    if compact:
        message += f"\n\n{compact}"
    if guidance:
        message += "\n\nSuggested fixes:\n- " + "\n- ".join(guidance)
    return message


def _write_batch_script(ionmonger_root: Path, workspace: Path) -> None:
    ion = _matlab_quote(str(ionmonger_root).replace("\\", "/"))
    ws = _matlab_quote(str(workspace).replace("\\", "/"))
    script = f"""
warning('off','all');
try
    ion_root = '{ion}';
    workspace = '{ws}';
    addpath(workspace);
    cd(ion_root);
    master;
catch ME
    disp(getReport(ME,'extended','hyperlinks','off'));
    exit(1);
end
exit(0);
""".strip()
    (workspace / "run_ionmonger_batch.m").write_text(script, encoding="utf-8")


def _write_parameters_file(ionmonger_root: Path, workspace: Path, values: dict[str, object]) -> None:
    template_path = ionmonger_root / "parameters_template.m"
    template = template_path.read_text(encoding="utf-8")

    pre_block = _pre_nondim_overrides(values, workspace)
    protocol_block = _protocol_overrides(values)

    marker_pre = "%% Non-dimensionalise model parameters and save all inputs"
    if marker_pre not in template:
        raise RuntimeError("parameters_template.m format not recognized (missing non-dimensionalise marker).")
    template = template.replace(marker_pre, pre_block + "\n\n" + marker_pre, 1)

    marker_protocol = "[light, psi, time, splits, findVoc] = ..."
    if marker_protocol not in template:
        raise RuntimeError("parameters_template.m format not recognized (missing construct_protocol marker).")
    template = template.replace(marker_protocol, protocol_block + "\n\n" + marker_protocol, 1)

    (workspace / "parameters.m").write_text(template, encoding="utf-8")


def _matlab_quote(text: str) -> str:
    return text.replace("'", "''")


def _to_bool(value: object) -> str:
    return "true" if bool(value) else "false"


def _float(value: object) -> float:
    return float(value)


def _pre_nondim_overrides(values: dict[str, object], workspace: Path) -> str:
    workspace_folder = _matlab_quote(str(workspace).replace("\\", "/") + "/")
    extra = str(values.get("additional_matlab_lines", "")).strip()
    lines = [
        "% --- GUI overrides (before nondimensionalise) ---",
        f"workfolder = '{workspace_folder}';",
        f"Verbose = {_to_bool(values['Verbose'])};",
        f"UseSplits = {_to_bool(values['UseSplits'])};",
        f"N = {int(values['N'])};",
        f"atol = {_float(values['atol']):.16g};",
        f"rtol = {_float(values['rtol']):.16g};",
        f"T = {_float(values['T']):.16g};",
        f"b = {_float(values['b']):.16g};",
        f"epsp = {_float(values['epsp_over_eps0']):.16g}*eps0;",
        f"alpha = {_float(values['alpha']):.16g};",
        f"Ec = {_float(values['Ec']):.16g};",
        f"Ev = {_float(values['Ev']):.16g};",
        f"Dn = {_float(values['Dn']):.16g};",
        f"Dp = {_float(values['Dp']):.16g};",
        f"N0 = {_float(values['N0']):.16g};",
        f"DIinf = {_float(values['DIinf']):.16g};",
        f"EAI = {_float(values['EAI']):.16g};",
        f"DI = D(DIinf, EAI);",
        f"inverted = {_to_bool(values['inverted'])};",
        f"dE = {_float(values['dE']):.16g};",
        f"gcE = {_float(values['gcE']):.16g};",
        f"EcE = {_float(values['EcE']):.16g};",
        f"bE = {_float(values['bE']):.16g};",
        f"epsE = {_float(values['epsE_over_eps0']):.16g}*eps0;",
        f"DE = {_float(values['DE']):.16g};",
        f"dH = {_float(values['dH']):.16g};",
        f"gvH = {_float(values['gvH']):.16g};",
        f"EvH = {_float(values['EvH']):.16g};",
        f"bH = {_float(values['bH']):.16g};",
        f"epsH = {_float(values['epsH_over_eps0']):.16g}*eps0;",
        f"DH = {_float(values['DH']):.16g};",
        f"tn = {_float(values['tn']):.16g};",
        f"tp = {_float(values['tp']):.16g};",
        f"beta = {_float(values['beta']):.16g};",
        f"betaE = {_float(values['betaE']):.16g};",
        f"betaH = {_float(values['betaH']):.16g};",
        f"vnE = {_float(values['vnE']):.16g};",
        f"vpE = {_float(values['vpE']):.16g};",
        f"vnH = {_float(values['vnH']):.16g};",
        f"vpH = {_float(values['vpH']):.16g};",
        "stats.ETL = struct('band', '%s', 'distribution', '%s', 's', %.16g);"
        % (
            _matlab_quote(str(values["etl_band"])),
            _matlab_quote(str(values["etl_distribution"])),
            _float(values["etl_s"]),
        ),
        "stats.HTL = struct('band', '%s', 'distribution', '%s', 's', %.16g);"
        % (
            _matlab_quote(str(values["htl_band"])),
            _matlab_quote(str(values["htl_distribution"])),
            _float(values["htl_s"]),
        ),
        f"EfE = {_float(values['EfE']):.16g};",
        f"EfH = {_float(values['EfH']):.16g};",
    ]
    if extra:
        lines.extend(["% User extension lines:", extra])
    return "\n".join(lines)


def _protocol_overrides(values: dict[str, object]) -> str:
    light = _float(values["light_intensity"])
    time_spacing = _matlab_quote(str(values["time_spacing"]))
    reduced_output = _to_bool(values["reduced_output"])

    if str(values["measurement_mode"]) == "eis":
        applied = (
            "applied_voltage = {'impedance', %.16g, %.16g, %.16g, %.16g, %d, %d};"
            % (
                _float(values["eis_fmin"]),
                _float(values["eis_fmax"]),
                _float(values["eis_vdc"]),
                _float(values["eis_vac"]),
                int(values["eis_nfreq"]),
                int(values["eis_nwaves"]),
            )
        )
    else:
        v_start = _float(values["jv_v_start"])
        v_end = _float(values["jv_v_end"])
        rate = _float(values["jv_scan_rate"])
        duration = abs(v_start - v_end) / rate
        applied = (
            "applied_voltage = {Vbi, 'tanh', 5, %.16g, 'linear', %.16g, %.16g, 'linear', %.16g, %.16g};"
            % (v_start, duration, v_end, duration, v_start)
        )

    lines = [
        "% --- GUI protocol overrides (before construct_protocol) ---",
        "light_intensity = {%.16g};" % light,
        applied,
        "reduced_output = %s;" % reduced_output,
        "time_spacing = '%s';" % time_spacing,
    ]
    return "\n".join(lines)


def _parse_mat_output(output_path: Path) -> SimulationResult:
    try:
        data = loadmat(output_path, squeeze_me=True, struct_as_record=False)
        sol = data.get("sol")
    except NotImplementedError:
        return _parse_hdf5_output(output_path)

    if sol is None:
        raise RuntimeError("simulation.mat did not contain 'sol'.")

    freq, impedance = _extract_impedance(sol)
    jv_v, jv_j = _extract_jv(sol)
    return SimulationResult(
        frequency_hz=freq,
        impedance_ohm=impedance,
        jv_voltage_v=jv_v,
        jv_current_ma_cm2=jv_j,
    )


def _parse_hdf5_output(output_path: Path) -> SimulationResult:
    with h5py.File(output_path, "r") as handle:
        if "sol" not in handle:
            raise RuntimeError("simulation.mat did not contain 'sol'.")
        sol = handle["sol"]
        freq = _h5_array(sol, "freqs")
        r = _h5_array(sol, "R")
        x = _h5_array(sol, "X")
        v = _h5_array(sol, "V")
        j = _h5_array(sol, "J")

    impedance = None
    if freq is not None and r is not None and x is not None:
        impedance = r + 1j * x
    return SimulationResult(
        frequency_hz=freq,
        impedance_ohm=impedance,
        jv_voltage_v=v,
        jv_current_ma_cm2=j,
    )


def _h5_array(group, name: str) -> np.ndarray | None:
    if name not in group:
        return None
    return np.asarray(group[name]).squeeze()


def _as_array(value) -> np.ndarray | None:
    if value is None:
        return None
    arr = np.asarray(value)
    if arr.size == 0:
        return None
    return arr.squeeze()


def _extract_impedance(sol) -> tuple[np.ndarray | None, np.ndarray | None]:
    freqs = _mat_field(sol, "freqs")
    r = _mat_field(sol, "R")
    x = _mat_field(sol, "X")
    if freqs is not None and r is not None and x is not None:
        return _as_array(freqs), _as_array(r) + 1j * _as_array(x)

    sol_array = np.ravel(np.asarray(sol, dtype=object))
    if sol_array.size > 1:
        list_freq: list[float] = []
        list_z: list[complex] = []
        for item in sol_array:
            item_r = _mat_field(item, "R")
            item_x = _mat_field(item, "X")
            if item_r is not None and item_x is not None:
                ap = _mat_field(_mat_field(item, "params"), "applied_voltage")
                freq = _extract_freq_from_applied_voltage(ap)
                if freq is not None:
                    list_freq.append(freq)
                    list_z.append(complex(float(np.squeeze(item_r)), float(np.squeeze(item_x))))
        if list_freq and len(list_freq) == len(list_z):
            order = np.argsort(np.asarray(list_freq))
            sorted_freq = np.asarray(list_freq)[order]
            sorted_z = np.asarray(list_z, dtype=np.complex128)[order]
            return sorted_freq, sorted_z

    return None, None


def _extract_freq_from_applied_voltage(applied_voltage) -> float | None:
    if applied_voltage is None:
        return None
    try:
        arr = np.ravel(np.asarray(applied_voltage, dtype=object))
        if arr.size > 1 and not isinstance(arr[1], str):
            period = float(arr[1])
            if period != 0:
                return 1.0 / period
    except (TypeError, ValueError, IndexError):
        return None
    return None


def _extract_jv(sol) -> tuple[np.ndarray | None, np.ndarray | None]:
    v = _mat_field(sol, "V")
    j = _mat_field(sol, "J")
    if v is not None and j is not None:
        return _as_array(v), _as_array(j)

    sol_array = np.ravel(np.asarray(sol, dtype=object))
    if sol_array.size > 0:
        first = sol_array[0]
        return _as_array(_mat_field(first, "V")), _as_array(_mat_field(first, "J"))
    return None, None


def _mat_field(obj, name: str):
    if obj is None:
        return None
    if isinstance(obj, dict):
        return obj.get(name)
    if hasattr(obj, name):
        return getattr(obj, name)
    if isinstance(obj, np.ndarray) and obj.dtype == object and obj.size == 1:
        return _mat_field(obj.item(), name)
    return None


def preview_generated_parameters(values: dict[str, object], workspace: Path) -> str:
    """Expose generated parameters body for tests."""
    return _pre_nondim_overrides(values, workspace) + "\n" + _protocol_overrides(values)
