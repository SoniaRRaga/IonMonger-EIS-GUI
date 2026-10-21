"""ZView text export and batch conversion."""

from __future__ import annotations

import re
from collections.abc import Iterable
from pathlib import Path

import numpy as np

from .classifier import classify, classify_series
from .reader import Spectrum, read_paios_all


ZVIEW_HEADER = (
    "ZView Calculated Data File: Version 1.1\n"
    "Raw Data\n"
    "Sweep Frequency: Control Voltage\n"
    'Date: 04-10-2019     "Time: 04:24:42\n'
    "Zahner Zennium/IM6\n"
    "\n"
    "c:\\data\\asonia\\boer lightsoak 20190408\\8%_a\\8a_islight_101.ism\n"
    "Frequency\n"
    "0,2,0,1,4.00000E-01,2.00000E+06\n"
    "{n}\n"
    "Freq (Hz)\tDC-Curr(A)\tDC-Pot(V)\tTime(Sec)\tZ'(Ohm)\tZ''(Ohm)\tGD\tX\tY\n"
)


def export_zview(spec: Spectrum, out_path: str | Path, *, negate_imag: bool = False) -> Path:
    """Write a ZView file: fixed header, then 9 tab-separated columns, increasing frequency."""
    out_path = Path(out_path)
    order = spec.freq.argsort()
    sign = -1.0 if negate_imag else 1.0
    zeros = np.zeros(spec.n_points)
    pot = spec.dc_pot if spec.dc_pot is not None else zeros
    cur = spec.dc_curr if spec.dc_curr is not None else zeros
    lines = []
    for i in order:
        vals = [spec.freq[i], cur[i], pot[i], 0.0, spec.zre[i], sign * spec.zim[i], 0.0, 0.0, 0.0]
        lines.append("\t".join(f"{v:.8E}" for v in vals))
    with out_path.open("w", encoding="utf-8", newline="\n") as f:
        f.write(ZVIEW_HEADER.format(n=spec.n_points))
        f.write("\n".join(lines) + "\n")
    return out_path


def _safe(label: str) -> str:
    return re.sub(r"[^\w.=\-]+", "_", label).strip("_")


def convert_files(paths: Iterable[str | Path], out_dir: str | Path, *,
                  negate_imag: bool = False, log=print) -> list[Path]:
    """Read, classify and export all files. Errors per file are logged, not raised."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    specs: list[Spectrum] = []
    for p in paths:
        try:
            specs.extend(read_paios_all(p))
        except (ValueError, OSError) as e:
            log(f"SKIP {Path(p).name}: {e}")
    if not specs:
        return []
    log(f"Detected measurement type: {classify_series(specs)}")
    written = []
    for n, (s, label) in enumerate(zip(specs, classify(specs)), start=1):
        label = _safe(label)
        name = f"{n}_{label}.txt" if label else f"{n}_{s.path.stem}.txt"
        written.append(export_zview(s, out_dir / name, negate_imag=negate_imag))
        log(f"OK   {s.path.name} -> {name} ({s.n_points} points)")
    return written
