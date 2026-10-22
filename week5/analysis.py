import csv
import glob
import os
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import curve_fit


HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(HERE, "motor_data")
RESULTS_CSV = os.path.join(HERE, "fit_results.csv")
REPORT = os.path.join(HERE, "report.md")
OMEGA_PLOT = os.path.join(HERE, "omega_vs_voltage.png")
STEP_PLOT = os.path.join(HERE, "step_response.png")


def angle_model(time_s, omega_ss, tau):
    return omega_ss * (
        time_s - tau + tau * np.exp(-time_s / tau)
    )


def load_step(path):
    data = np.loadtxt(path, comments="#", ndmin=2)
    if data.shape[1] != 2 or len(data) < 4:
        raise ValueError("Expected at least four position/time samples: " + path)
    position_deg = data[:, 0]
    time_s = (data[:, 1] - data[0, 1]) / 1000.0
    angle_rad = np.deg2rad(position_deg - position_deg[0])
    if np.any(np.diff(time_s) < 0) or time_s[-1] <= 0:
        raise ValueError("Sample timestamps must be ordered with positive duration: " + path)
    return time_s, angle_rad


def fit_step(path):
    time_s, angle_rad = load_step(path)
    tail_start = int(len(time_s) * 0.6)
    tail_slope = np.polyfit(
        time_s[tail_start:], angle_rad[tail_start:], 1
    )[0]
    initial_speed = tail_slope if abs(tail_slope) > 0.01 else (
        angle_rad[-1] / time_s[-1]
    )
    parameters, _ = curve_fit(
        angle_model,
        time_s,
        angle_rad,
        p0=[initial_speed, 0.15],
        bounds=([-np.inf, 0.005], [np.inf, 2.0]),
        maxfev=30000,
    )
    predicted = angle_model(time_s, *parameters)
    rmse = float(np.sqrt(np.mean((predicted - angle_rad) ** 2)))
    travel_deg = float(np.rad2deg(np.ptp(angle_rad)))
    tau = float(parameters[1])
    quality = (
        "low confidence"
        if tau <= 0.0051 or tau >= 1.95 or travel_deg < 30 or rmse > 0.1
        else "fit"
    )
    return {
        "time_s": time_s,
        "angle_rad": angle_rad,
        "omega_ss_rad_s": float(parameters[0]),
        "tau_s": tau,
        "rmse_rad": rmse,
        "travel_deg": travel_deg,
        "quality": quality,
    }


def battery_voltage(wheel_id):
    path = os.path.join(DATA_DIR, "wheel_%d_battery.txt" % wheel_id)
    with open(path, "r") as battery_file:
        line = battery_file.readline().strip()
    value = float(line.split(":", 1)[1].strip())
    return value


def discover_results():
    results = []
    for path in sorted(glob.glob(os.path.join(DATA_DIR, "wheel_*_v_*.txt"))):
        match = re.fullmatch(r"wheel_(\d+)_v_(-?\d+)\.txt", os.path.basename(path))
        if not match:
            continue
        wheel_id = int(match.group(1))
        pwm = int(match.group(2))
        fitted = fit_step(path)
        results.append({
            "wheel_id": wheel_id,
            "pwm_percent": pwm,
            "voltage_v": pwm * battery_voltage(wheel_id) / 100.0,
            **fitted,
        })
    if not results:
        raise FileNotFoundError("No wheel_*_v_*.txt recordings found in " + DATA_DIR)
    return sorted(results, key=lambda row: (row["wheel_id"], row["pwm_percent"]))


def estimate_motor_constants(results, wheel_id):
    data = [r for r in results if r["wheel_id"] == wheel_id]
    fit_data = [r for r in data if abs(r["pwm_percent"]) >= 25]
    slope, intercept = np.polyfit(
        [r["voltage_v"] for r in fit_data],
        [r["omega_ss_rad_s"] for r in fit_data],
        1,
    )
    dead_zone = {}
    for direction, label in ((-1, "negative"), (1, "positive")):
        points = [
            r for r in data
            if np.sign(r["pwm_percent"]) == direction
        ]
        at_or_below = [
            abs(r["pwm_percent"]) for r in points
            if abs(r["omega_ss_rad_s"]) <= 0.5
        ]
        if at_or_below:
            dead_zone[label] = {
                "pwm": max(at_or_below),
                "upper_bound": False,
            }
        else:
            dead_zone[label] = {
                "pwm": min(abs(r["pwm_percent"]) for r in points),
                "upper_bound": True,
            }
    return {
        "slope": float(slope),
        "intercept": float(intercept),
        "ke": float(1.0 / slope) if slope != 0 else float("inf"),
        "dead_zone_pwm": dead_zone,
    }


def write_csv(results):
    columns = [
        "wheel_id", "pwm_percent", "voltage_v", "omega_ss_rad_s",
        "tau_s", "rmse_rad", "travel_deg", "quality",
    ]
    with open(RESULTS_CSV, "w", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=columns)
        writer.writeheader()
        for row in results:
            writer.writerow({key: row[key] for key in columns})


def make_plots(results, constants):
    wheel_ids = sorted({r["wheel_id"] for r in results})
    colors = plt.get_cmap("tab10")

    fig, ax = plt.subplots(figsize=(9, 5.5))
    for index, wheel_id in enumerate(wheel_ids):
        data = [r for r in results if r["wheel_id"] == wheel_id]
        color = colors(index)
        ax.scatter(
            [r["voltage_v"] for r in data],
            [r["omega_ss_rad_s"] for r in data],
            color=color, s=24, label="Wheel %d data" % wheel_id,
        )
        fit = constants[wheel_id]
        x = np.linspace(
            min(r["voltage_v"] for r in data),
            max(r["voltage_v"] for r in data),
            150,
        )
        ax.plot(
            x, fit["slope"] * x + fit["intercept"], color=color,
            label="Wheel %d: k_e=%.3f V s/rad" % (wheel_id, fit["ke"]),
        )
        battery = battery_voltage(wheel_id)
        dz = fit["dead_zone_pwm"]
        ax.axvspan(
            -dz["negative"]["pwm"] * battery / 100.0,
            dz["positive"]["pwm"] * battery / 100.0,
            color=color, alpha=0.08,
        )
    ax.axhline(0, color="gray", linewidth=0.7)
    ax.axvline(0, color="gray", linewidth=0.7)
    ax.set_xlabel("Applied motor voltage U (V)")
    ax.set_ylabel("Steady angular velocity ω_ss (rad/s)")
    ax.set_title("Steady motor speed versus actual voltage")
    ax.grid(True, alpha=0.25)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(OMEGA_PLOT, dpi=160)
    plt.close(fig)

    step = next((r for r in results if r["wheel_id"] == wheel_ids[0]
                 and r["pwm_percent"] == 50), None)
    if step is None:
        step = next(r for r in results if r["wheel_id"] == wheel_ids[0])
    time_s = step["time_s"]
    measured = step["angle_rad"]
    simulated = angle_model(time_s, step["omega_ss_rad_s"], step["tau_s"])
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(time_s, np.rad2deg(measured), label="Measured θ(t)")
    ax.plot(time_s, np.rad2deg(simulated), "--", label="Fitted model")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Angle θ (deg)")
    ax.set_title(
        "Wheel %d, PWM %+d%% (T_m=%.3f s)" %
        (step["wheel_id"], step["pwm_percent"], step["tau_s"])
    )
    ax.grid(True, alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(STEP_PLOT, dpi=160)
    plt.close(fig)
    return step


def write_report(results, constants, step):
    wheel_ids = sorted(constants)
    low_confidence = sum(
        row["quality"] == "low confidence" for row in results
    )
    lines = [
        "# Lab 5 — Motor parameter identification",
        "",
        "> **Data source:** robot recordings in `motor_data/` "
        "(%d PWM tests per wheel, plus one battery-voltage file per wheel)." %
        (len(results) // len(wheel_ids)),
        "",
        "## Method",
        "",
        "Each measured angle trace was converted to radians and each recorded "
        "timestamp to seconds, then fitted to "
        "`θ(t)=ω_ss[t−T_m+T_m exp(−t/T_m)]`. Actual voltage is "
        "`U=(PWM/100) U_battery`. The straight-line `ω_ss(U)` fit uses "
        "measurements with `|PWM| ≥ 25%`; `k_e=1/slope`.",
        "",
        "## Identified motor constants",
        "",
        "| Wheel | k_e (V·s/rad) | ω/U slope (rad/s/V) | Dead-zone estimate (− / + PWM) |",
        "|---:|---:|---:|---|",
    ]
    for wheel_id in wheel_ids:
        fit = constants[wheel_id]
        dz = fit["dead_zone_pwm"]
        negative = ("≤" if dz["negative"]["upper_bound"] else "") + str(
            dz["negative"]["pwm"]
        ) + "%"
        positive = ("≤" if dz["positive"]["upper_bound"] else "") + str(
            dz["positive"]["pwm"]
        ) + "%"
        lines.append(
            "| %d | %.4f | %.4f | %s / %s |" % (
                wheel_id, fit["ke"], fit["slope"],
                negative, positive,
            )
        )
    lines.extend([
        "",
        "Dead-zone estimates use fitted `|ω_ss| ≤ 0.5 rad/s`; when even the "
        "lowest tested PWM moves the motor, the threshold is reported as "
        "`≤5%`. Since inputs are spaced by 5%, these are interval estimates, "
        "not exact thresholds; shading shows the estimated range.",
        "",
        "%d of %d step fits are flagged low confidence because the trace has "
        "little movement, a large residual, or a fit at a time-constant "
        "bound. Treat these entries as approximate and inspect their raw "
        "traces." % (low_confidence, len(results)),
        "",
        "## Per-step fits",
        "",
        "| Wheel | PWM (%) | U (V) | ω_ss (rad/s) | T_m (s) | RMSE (rad) | Fit quality |",
        "|---:|---:|---:|---:|---:|---:|---|",
    ])
    for row in results:
        lines.append(
            "| %d | %+d | %.3f | %.4f | %.4f | %.4f | %s |" % (
                row["wheel_id"], row["pwm_percent"], row["voltage_v"],
                row["omega_ss_rad_s"], row["tau_s"], row["rmse_rad"],
                row["quality"],
            )
        )
    lines.extend([
        "",
        "## Voltage characteristic",
        "",
        "![Fitted speed versus actual voltage](omega_vs_voltage.png)",
        "",
        "## Example step response",
        "",
        "![Measured and simulated angle](step_response.png)",
        "",
        "## Discussion",
        "",
        "The first-order linear model does not capture the low-PWM dead zone, "
        "friction, encoder quantization, battery variation, or the observed "
        "difference between accelerating and steady motion; the low-confidence "
        "fits above reflect these limitations. In this dataset, "
        "the fitted `k_e` values are %.4f and %.4f V·s/rad for wheels %d and "
        "%d, respectively, so their voltage-to-speed gains are not identical. "
        "Unequal wheel gains make equal motor commands produce unequal wheel "
        "speeds, causing heading drift and accumulating position error in "
        "encoder odometry. Use the wheel-specific fits when predicting or "
        "correcting the robot's motion." % (
            constants[wheel_ids[0]]["ke"], constants[wheel_ids[1]]["ke"],
            wheel_ids[0], wheel_ids[1],
        ),
        "",
        "The measured/simulated step response above is wheel %d at %+d%% PWM." %
        (step["wheel_id"], step["pwm_percent"]),
        "",
    ])
    with open(REPORT, "w", encoding="utf-8") as output:
        output.write("\n".join(lines))


def main():
    results = discover_results()
    wheel_ids = sorted({row["wheel_id"] for row in results})
    constants = {
        wheel_id: estimate_motor_constants(results, wheel_id)
        for wheel_id in wheel_ids
    }
    write_csv(results)
    step = make_plots(results, constants)
    write_report(results, constants, step)
    print("Generated report.md, fit_results.csv, omega_vs_voltage.png, "
          "and step_response.png")


if __name__ == "__main__":
    main()
