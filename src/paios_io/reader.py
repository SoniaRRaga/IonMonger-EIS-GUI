"""Reader: raw PAIOS text file -> list of Spectrum (metadata + frequency/Z table).

Native PAIOS exports have no header row; columns are described by comment lines
``# Column N: name``. Columns named ``Sweep k - <quantity>`` are sweep axes; every
distinct value of the non-frequency sweep axes becomes one Spectrum.
A generic fallback handles files with a plain header row (Frequency, Z', Z'').
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

# Column profiles: regexes (lowercased column name) for each required column.
COLUMN_PROFILES = {
    "freq": [r"^freq"],
    "zre": [r"^impedance real", r"^z\s*'(?!')", r"^re\s*\(?z", r"^zre", r"^z_?real", r"^real"],
    "zim": [r"^impedance imag", r"^z\s*''", r"^z\s*\"", r"^im\s*\(?z", r"^zim", r"^z_?imag", r"^imag"],
}
# Setting profiles: canonical key -> regex on lowercased name.
SETTING_PROFILES = {
    "bias": r"(bias|dc\s*(voltage|offset)|vdc|offset voltage)",
    "light": r"(light|illumin|intensity|sun|led)",
}
_NUM = re.compile(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")
_COLDEF = re.compile(r"^\s*#\s*Column\s+(\d+)\s*:\s*(.*?)\s*$", re.I)
_SWEEP = re.compile(r"^sweep\s*\d+\s*-\s*(.*)$", re.I)


@dataclass
class Spectrum:
    path: Path
    freq: np.ndarray
    zre: np.ndarray
    zim: np.ndarray  # signed imaginary part of Z (as stored in the file)
    dc_pot: np.ndarray | None = None  # measured DC voltage (V), if present
    dc_curr: np.ndarray | None = None  # measured DC current (A), if present
    metadata: dict = field(default_factory=dict)
    settings: dict = field(default_factory=dict)  # canonical: bias, light (floats)
    sweep: dict = field(default_factory=dict)  # outer-sweep values for this spectrum

    @property
    def n_points(self) -> int:
        return len(self.freq)


def _split(line: str) -> list[str]:
    for sep in ("\t", ";"):
        if sep in line:
            return [c.strip() for c in line.split(sep)]
    if "," in line:
        return [c.strip() for c in line.split(",")]
    return line.split()


def _to_float(s: str) -> float | None:
    try:
        return float(s.strip())
    except ValueError:
        return None


def _match_columns(names: list[str]) -> dict[str, int] | None:
    found: dict[str, int] = {}
    for i, c in enumerate(names):
        low = c.strip().lower()
        for key, pats in COLUMN_PROFILES.items():
            if key not in found and any(re.search(p, low) for p in pats):
                found[key] = i
    return found if len(found) == 3 else None


def _canon_name(name: str) -> str:
    low = name.lower()
    for canon, pat in SETTING_PROFILES.items():
        if re.search(pat, low):
            return canon
    return re.sub(r"\s*\(.*?\)\s*$", "", name).strip()


def _header_settings(meta: dict) -> dict:
    out: dict = {}
    for key, val in meta.items():
        m = _NUM.match(val)
        if not m:
            continue
        for canon, pat in SETTING_PROFILES.items():
            if canon not in out and re.search(pat, key.lower()) and "sweep" not in key.lower():
                out[canon] = float(m.group())
    return out


def _read_native(path: Path, lines: list[str], meta: dict, coldefs: dict) -> list[Spectrum]:
    ncol = max(coldefs)
    names = [coldefs.get(i + 1, "") for i in range(ncol)]
    stripped = [m.group(1) if (m := _SWEEP.match(n)) else n for n in names]
    cols = _match_columns(stripped)
    if not cols:
        raise ValueError(f"{path.name}: column definitions lack frequency / impedance")
    outer = [
        i for i, n in enumerate(names)
        if _SWEEP.match(n) and not re.match(r"^(freq|inactive)", stripped[i].lower())
    ]
    rows = []
    for line in lines:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        vals = [_to_float(c) for c in _split(line)[:ncol]]
        if len(vals) == ncol and None not in vals:
            rows.append(vals)
    if not rows:
        raise ValueError(f"{path.name}: impedance table is empty")
    arr = np.array(rows, dtype=float)
    groups: dict[tuple, list[int]] = {}
    for r in range(len(arr)):
        groups.setdefault(tuple(arr[r, outer]), []).append(r)
    # failed points are exported as NaN: drop them, and drop spectra that end up empty
    ok = np.isfinite(arr[:, [cols["freq"], cols["zre"], cols["zim"]]]).all(axis=1)
    groups = {k: [r for r in idx if ok[r]] for k, idx in groups.items()}
    groups = {k: idx for k, idx in groups.items() if idx}
    if not groups:
        raise ValueError(f"{path.name}: no valid (non-NaN) impedance data")
    base = _header_settings(meta)
    pot = next((i for i, n in enumerate(names) if re.match(r"^offset voltage", n.lower())), None)
    cur = next((i for i, n in enumerate(names) if re.match(r"^offset current", n.lower())), None)
    out = []
    for key, idx in groups.items():
        a = arr[idx]
        sweep = {_canon_name(stripped[c]): float(v) for c, v in zip(outer, key)}
        settings = {**base, **{k: v for k, v in sweep.items() if k in SETTING_PROFILES}}
        out.append(Spectrum(path, a[:, cols["freq"]], a[:, cols["zre"]], a[:, cols["zim"]],
                            a[:, pot] if pot is not None else None,
                            a[:, cur] if cur is not None else None, meta, settings, sweep))
    return out


def _read_generic(path: Path, lines: list[str]) -> list[Spectrum]:
    meta: dict[str, str] = {}
    cols = None
    start = 0
    for n, line in enumerate(lines):
        if not line.strip():
            continue
        cols = _match_columns(_split(line.lstrip("# ")))
        if cols:
            start = n + 1
            break
        m = re.match(r"^\s*#?\s*([^:=\t;]+?)\s*[:=]\s*(.*)$", line)
        if m:
            meta[m.group(1).strip()] = m.group(2).strip()
    if not cols:
        raise ValueError(f"{path.name}: no PAIOS column definitions or frequency/Z header found")
    need = max(cols.values())
    rows = []
    for line in lines[start:]:
        cells = _split(line)
        if len(cells) <= need:
            continue
        vals = [_to_float(cells[cols[k]]) for k in ("freq", "zre", "zim")]
        if None not in vals:
            rows.append(vals)
    if not rows:
        raise ValueError(f"{path.name}: impedance table is empty")
    a = np.array(rows, dtype=float)
    return [Spectrum(path, a[:, 0], a[:, 1], a[:, 2], metadata=meta, settings=_header_settings(meta))]


def read_paios_all(path: str | Path) -> list[Spectrum]:
    """Parse a PAIOS export into one Spectrum per outer-sweep value."""
    path = Path(path)
    lines = path.read_text(encoding="utf-8-sig", errors="replace").splitlines()
    coldefs = {int(m.group(1)): m.group(2) for l in lines if (m := _COLDEF.match(l))}
    if coldefs:
        meta = {}
        for l in lines:
            m = re.match(r"^\s*#\s*([^:=]+?)\s*:\s*(.+)$", l)
            if m and not _COLDEF.match(l):
                meta[m.group(1).strip()] = m.group(2).strip()
        return _read_native(path, lines, meta, coldefs)
    return _read_generic(path, lines)
