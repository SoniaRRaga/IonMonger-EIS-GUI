# IonMonger EIS GUI

This repository includes a Python desktop GUI that runs **real IonMonger drift-diffusion simulations** through MATLAB (`master.m` + generated `parameters.m`).

## What the app does

- Runs IonMonger non-interactively with `matlab -batch`
- Supports both protocol modes:
  - **EIS** via `applied_voltage = {'impedance', fmin, fmax, Vdc, Vac, nfreq, nwaves}`
  - **JV/transient** via a generated sweep protocol
- Exposes a schema-driven parameter UI with grouped tabs:
  - Protocol & measurement mode
  - EIS settings
  - Solver/numerics
  - Layer/material/device
  - Statistics model for ETL/HTL
- Lets you search parameters by name
- Imports/exports full parameter sets as JSON
- Plots:
  - JV (J vs V)
  - Nyquist (`-Imag(Z)` vs `Real(Z)`)
  - Bode phase vs frequency
  - Bode capacitance vs frequency

Capacitance is computed as:

`Y = 1/Z`, `C(f) = -imag(Y)/(2*pi*f)`.

## MATLAB prerequisite

- MATLAB must be installed and available on PATH (default command: `matlab`), or provide a custom command in the GUI.
- The GUI requires an **IonMonger root folder** containing `master.m`, `parameters_template.m`, and `Code/`.

Tested path is the beginner-friendly subprocess route (`matlab -batch`) so MATLAB Engine setup is not required.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

## Run

```bash
python src/app.py
```

## Workflow example (impedance)

1. Set **IonMonger root** to the folder containing `master.m`.
2. Keep **Measurement mode = eis**.
3. Configure `fmin`, `fmax`, `Vdc`, `Vac`, `nfreq`, `nwaves`.
4. Click **Run IonMonger**.
5. The status bar reports: `Running MATLAB` → `Parsing output` → `Done`.

For reduced EIS output (`reduced_output = true`), the GUI reads `freqs`, `R`, and `X` from `sol` and builds `Z = R + iX`.

## Plot and export behavior

- JV plot uses `sol.V` and `sol.J`.
- Nyquist/Bode plots use EIS impedance arrays.
- CSV export includes EIS and JV columns in one table.
- Plot export saves the four-panel figure as PNG.

## Troubleshooting

- **`master.m` not found**: verify IonMonger root path.
- **MATLAB command failed**: verify command in settings (default `matlab`).
- **`Unable to meet integration tolerances` / `Need a better guess y0`**:
  - try adjusting `N`, `atol`, `rtol` in Solver/numerics
  - simplify protocol bounds and perturbation settings
- **No EIS curve shown**: ensure EIS mode and valid frequencies (`fmin > 0`, `fmax > fmin`, integer `nfreq`).

## Build/package note

The application remains runnable with `python src/app.py`.
If you maintain Windows executable packaging in your environment, keep using your existing packaging workflow with this same entry point.

## Legacy IonMonger references

See [GUIDE.md](GUIDE.md) for full IonMonger model and protocol details.
