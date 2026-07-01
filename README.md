# IonMonger EIS GUI

This repository now includes a beginner-friendly Python desktop application for running simple electrochemical impedance spectroscopy (EIS) simulations with manual parameter entry, interactive plots, and CSV/PNG export.

The GUI is intentionally lightweight and self-contained so that it can run even when direct integration with the full MATLAB-based IonMonger workflow is not available.

## What the app does

The desktop app lets you:

- enter EIS parameters manually
- run a simple equivalent-circuit simulation
- view Nyquist and Bode plots
- export the simulated spectrum to CSV
- save the current plots as a PNG image

The first version uses a standard demonstration circuit:

- `Rs + (Rct || Cdl)`
- optional Warburg diffusion element

## Project layout

- `/src/app.py` - main entry point
- `/src/gui/` - PySide6 GUI code
- `/src/sim/` - simulation logic
- `/src/io/` - CSV export helpers
- `/tests/` - lightweight simulation tests

## Installation

From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

On Windows PowerShell, activate the environment with:

```powershell
.venv\Scripts\Activate.ps1
```

## Run the desktop app

Recommended:

```bash
python src/app.py
```

You can also run:

```bash
python -m src.app
```

## Parameters

- **Rs (Ω)** - series resistance
- **Rct (Ω)** - charge-transfer resistance
- **Cdl (F)** - double-layer capacitance
- **Enable Warburg element** - adds a simple diffusion tail
- **Warburg σ** - diffusion strength used when Warburg is enabled
- **f min (Hz)** - lowest frequency in the sweep
- **f max (Hz)** - highest frequency in the sweep
- **Points / decade** - number of simulated frequencies per decade

The default values are chosen so a beginner can press **Run simulation** immediately and see a valid spectrum.

## Exported output

CSV export includes these columns:

- `frequency_hz`
- `Z_real_ohm`
- `Z_imag_ohm`
- `Z_mag_ohm`
- `Z_phase_deg`

Plot export saves the currently displayed figure as a PNG image.

## Running tests

The repository now includes lightweight Python tests for the simulation core:

```bash
pytest
```

## Troubleshooting

- **`No module named PySide6`**: activate your virtual environment and run `pip install -r requirements.txt`.
- **The window does not open on Linux**: make sure a desktop session is available; GUI apps usually do not open in headless terminals.
- **Invalid input message**: check that all numeric fields contain numbers and that `f min` is smaller than `f max`.
- **MATLAB files are still in the repo**: they are kept for the original IonMonger codebase and documentation.

## Legacy IonMonger MATLAB code

This repository also contains the original MATLAB-based IonMonger code for perovskite solar-cell simulations.

Requirements: MATLAB (version R2021a).

Please read the [GUIDE](GUIDE.md) for the MATLAB workflow. The main legacy entry points are:

- `master.m` for running a single simulation
- `parameters.m` for setting the inputs to the simulation
- `reset_path.m` for adding subfunctions to the MATLAB path
- `IonMongerLite.mlx` for the original MATLAB-friendly interface

If you encounter a MATLAB-specific problem, please create an issue with details including the error message and MATLAB version number.
