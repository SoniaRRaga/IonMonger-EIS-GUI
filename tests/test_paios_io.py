from src.paios_io import classify, classify_series, convert_files, read_paios_all

HEADER = """### PAIOS
# Impedance
# Sweep Offset Light Intensity: From: 0.01  to: 1   |  Steps: 2  |  Transition: Logarithmic
# Offset Voltage: Adjusted to Voc
#
### Colum Quantities:
# Column 1: Sweep 1 - Offset Light Intensity (1)
# Column 2: Sweep 2 - Frequency (Hz)
# Column 3:  ()
# Column 4: Amplitude (Ohm)
# Column 5: Phase (rad)
# Column 6: Frequency (Hz)
# Column 7: Offset Voltage (V)
# Column 8: Offset Current (A)
# Column 9: Impedance Real (Ohm)
# Column 10: Impedance Imag (Ohm)
# Column 11: Capacitance (F)
# Column 12: Light Power (W/m2)
#
"""


def make(path, lights=(9.9999998e-3, 1.0), nf=3):
    rows = []
    for L in lights:
        for i in range(nf):
            f = 4e6 / 10**i
            rows.append("\t".join(map(str, [L, f, 0, 10, 0.9, f, 0.09, 1e-5, 5.0 + i, -2.0 * i, 1e-9, 11.0])))
    path.write_text(HEADER + "\n".join(rows) + "\n")
    return path


def test_native_multi_sweep(tmp_path):
    specs = read_paios_all(make(tmp_path / "55-is-at-different-light-at-voc_1d.txt"))
    assert len(specs) == 2 and all(s.n_points == 3 for s in specs)
    assert specs[0].zre[1] == 6.0 and specs[0].zim[1] == -2.0
    assert specs[1].sweep["light"] == 1.0
    assert classify_series(specs) == "varying illumination"
    assert classify(specs) == ["light=0.0099999998", "light=1.0"]


def test_convert(tmp_path):
    out = convert_files([make(tmp_path / "a.txt")], tmp_path / "out", log=lambda m: None)
    assert len(out) == 2
    assert out[0].name == "a_light=0.0099999998.txt"
    first = out[0].read_text().splitlines()[0].split("\t")
    assert len(first) == 3 and float(first[0]) == 4e6


def test_generic_header(tmp_path):
    p = tmp_path / "g.txt"
    p.write_text("Bias: 0.5 V\nFrequency\tZ'\tZ''\n100\t5\t-1\n10\t6\t-2\n")
    (s,) = read_paios_all(p)
    assert s.n_points == 2 and s.settings["bias"] == 0.5


def test_single_dark_inactive_sweep(tmp_path):
    p = tmp_path / "44-is-dark_1d.txt"
    text = HEADER.replace("# Sweep Offset Light Intensity: From: 0.01  to: 1   |  Steps: 2  |  Transition: Logarithmic",
                          "# Offset Light Intensity: 0").replace("Sweep 1 - Offset Light Intensity (1)", "Sweep 1 - inactive")
    rows = [f"0\t{4e6 / 10**i}\t0\t10\t0.9\t{4e6 / 10**i}\t0.0\t1e-5\t{5 + i}\t{-2 * i}\t1e-9\t0.05" for i in range(3)]
    p.write_text(text + "\n".join(rows) + "\n")
    (s,) = read_paios_all(p)
    assert s.n_points == 3 and s.sweep == {} and s.settings["light"] == 0.0
    out = convert_files([p], tmp_path / "o", log=lambda m: None)
    assert [x.name for x in out] == ["44-is-dark_1d.txt"]
