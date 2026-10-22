# Lab 5 — Motor parameter identification

## Task

Apply step inputs to both drive motors, record encoder angle and actual sample time at each PWM level from `-100%` to `+100%` in `5%` steps (excluding zero), and record battery voltage. Fit

```text
T_m * dω/dt + ω = U/k_e
dθ/dt = ω
```

to each step response. The report must give `T_m` and `ω_ss` at every level, compare `ω_ss` with actual voltage for both wheels, show a measured/simulated step response, and discuss model limitations and odometry effects.

## Contents and data provenance

- `Lab5_Motor_Identification.ipynb` is the main, student-friendly report. It explains the method, shows the fit tables and plots, and ends with a discussion based on the measurements.
- `motor_data/` contains the robot recordings: 40 PWM step files and one battery-voltage file for each wheel. Both wheels have complete `-100%` to `+100%` data (excluding zero). The recorded battery voltage is about 11.804 V.
- `motor_identification.py` is the TRIK-side Python collector used for the measurements. Its configured ports are M3/E3 and M4/E4; verify these against the robot wiring if you run it again.
- `analysis.py` fits every step and generates `report.md`, `fit_results.csv`, `omega_vs_voltage.png`, and `step_response.png` as an alternate report and analysis output.
- The source package does not contain a valid two-wheel TRIK Studio `.qrs` project. Load `motor_identification.py` into the TRIK Studio Python editor, verify the ports, and save/export the native `.qrs` project for the required deliverable.

## Run the analysis

From this folder, install `numpy`, `scipy`, and `matplotlib`, then run:

```text
python analysis.py
```

Open the notebook in Jupyter or Google Colab with its `motor_data/` folder beside it, then run all cells from top to bottom. The nonlinear fits use radians, seconds, and volts. Fits with a time constant at either search bound, very little angle travel, or a large residual are marked low confidence; inspect those traces before interpreting them.
