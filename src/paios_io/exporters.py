"""ZView text export and batch conversion."""

from __future__ import annotations

import re
from collections.abc import Iterable
from pathlib import Path

from .classifier import classify, classify_series
from .reader import Spectrum, read_paios_all


def export_zview(spec: Spectrum, out_path: str | Path, *, negate_imag: bool = False) -> Path:
    """Write freq, Z', Z'' as tab-separated text, sorted by decreasing frequency."""
    out_path = Path(out_path)
    order = spec.freq.argsort()[::-1]
    sign = -1.0 if negate_imag else 1.0
    lines = [f"{spec.freq[i]:.8e}\t{spec.zre[i]:.8e}\t{sign * spec.zim[i]:.8e}" for i in order]
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
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
    written, used = [], set()
    for s, label in zip(specs, classify(specs)):
        label = _safe(label)
        stem = f"{s.path.stem}_{label}" if label and sum(x.path == s.path for x in specs) > 1 else (label or s.path.stem)
        name, k = f"{stem}.txt", 1
        while name in used:
            k += 1
            name = f"{stem}_{k}.txt"
        used.add(name)
        written.append(export_zview(s, out_dir / name, negate_imag=negate_imag))
        log(f"OK   {s.path.name} -> {name} ({s.n_points} points)")
    return written
