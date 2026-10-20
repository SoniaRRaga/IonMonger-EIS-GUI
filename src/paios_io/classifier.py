"""Measurement-type detection from header/sweep settings (filename only as fallback)."""

from __future__ import annotations

import re
from collections.abc import Sequence

from .reader import Spectrum

SINGLE = "single"
BIAS = "varying bias"
LIGHT = "varying illumination"
BIAS_LIGHT = "varying bias and illumination"
UNKNOWN = "unknown"

# Filename fallback profiles: (regex, canonical setting)
FILENAME_PROFILES = [
    (r"(?<![a-z])(-?\d+(?:[.p]\d+)?)\s*m?v(?![a-z])", "bias"),
    (r"(\d+(?:[.p]\d+)?)\s*(?:sun|mw|lux|%)", "light"),
]


def _name_settings(name: str) -> dict:
    out = {}
    for pat, key in FILENAME_PROFILES:
        m = re.search(pat, name.lower())
        if m:
            out[key] = float(m.group(1).replace("p", "."))
    return out


def _settings(s: Spectrum) -> dict:
    d = _name_settings(s.path.stem)
    d.update(s.settings)  # header/sweep wins over filename
    return d


def classify_series(spectra: Sequence[Spectrum]) -> str:
    """Type of a group of spectra that belong to one experiment."""
    if len(spectra) < 2:
        return SINGLE
    sets = [_settings(s) for s in spectra]
    varies = {k: len({d[k] for d in sets if k in d}) > 1 for k in ("bias", "light")}
    # a swept quantity is the real variable; bias that merely drifts (e.g. Voc) is ignored
    swept = {k for s in spectra for k in s.sweep}
    if "light" in swept and "bias" not in swept:
        varies["bias"] = False
    if "bias" in swept and "light" not in swept:
        varies["light"] = False
    if varies["bias"] and varies["light"]:
        return BIAS_LIGHT
    if varies["bias"]:
        return BIAS
    if varies["light"]:
        return LIGHT
    return UNKNOWN


def _fmt(v) -> str:
    return "?" if v is None else f"{v:.4g}"


def classify(spectra: Sequence[Spectrum]) -> list[str]:
    """Per-spectrum label (same order as input), e.g. 'bias=0.8', 'light=0.1'."""
    kind = classify_series(spectra)
    out = []
    for s in spectra:
        d = _settings(s)
        if kind == BIAS:
            out.append(f"bias={_fmt(d.get('bias'))}")
        elif kind == LIGHT:
            out.append(f"light={_fmt(d.get('light'))}")
        elif kind == BIAS_LIGHT:
            out.append(f"bias={_fmt(d.get('bias'))}_light={_fmt(d.get('light'))}")
        else:
            out.append("")
    return out
