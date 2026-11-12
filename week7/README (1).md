# Lab 7 — Go-to-goal (student ID ending 45)

The robot drives through a list of points that draw the digits **4** and **5**, using a go-to-goal controller. The same program and gains run in the TRIK Studio simulator and on the real robot, and the results are compared.

## Files

| File | What it is |
|---|---|
| `go_to_goal_sim.qrs` | Program for the simulator (2D model robot) |
| `go_to_goal_real.qrs` | Program for the real robot |
| `odometry_data_sim.txt` | Simulator log: `x,y,time` (cm, cm, ms) |
| `odometry_data_real.txt` | Real robot log: `x,y,time` (cm, cm, ms) |
| `Lab7_go_to_goal.ipynb` | Colab notebook: path plot, miss table, run times, tape measurement, conclusion |

## Waypoints (cm)

Start at (0, 0) facing +x:

```
(0,-20) → (20,-20) → (20,0) → (20,-40) → (40,-40) → (60,-40) → (60,-20) → (40,-20) → (40,0) → (60,0)
```

## Settings (same in both programs)

| Parameter | Value |
|---|---|
| `Kv` (speed gain) | 1.5 |
| `Kθ` (turning gain) | 4 |
| `ε` (acceptance radius) | 2 cm |
| `v_min` / `v_max` | 10 / 15 cm/s |
| `e_drive` | 0.3 rad (turn on the spot if the heading error is larger) |

Only the robot dimensions differ: the simulator uses r = 2.8 cm, B = 15.4 cm; the real robot uses r = 3.75 cm, B = 19.4 cm.

## How it works

At every step the robot updates its position (x, y, heading) from the wheel encoders, then:

1. computes the distance to the next point and the heading error (wrapped to −π…π);
2. sets forward speed `v` proportional to the distance, and turning speed `ω` proportional to the heading error;
3. converts `v` and `ω` to left/right motor power;
4. switches to the next point when the distance is below `ε`.

## Results

| | Simulator | Real robot |
|---|---|---|
| Closest approach to each point | about 1.6 cm | at most 0.8 cm (1.8 cm at the last point) |
| Run time | 27 s | 38 s |
| Last logged position | (58.4, −0.1) | (58.3, 0.3) |

The real-robot numbers come from the robot's own odometry, so they show how well the controller worked, not where the robot really went.

**Measured end point (tape):** _fill in after measuring_ — x = ___ cm, y = ___ cm

## Conclusion

The robot passed through every point to within about 2 cm, both in the simulator and on the real robot. The simulator cuts the corners a little, because the robot moves on to the next point as soon as it is within 2 cm (`ε`). The real robot goes slightly past some corners, for example (60, −40), because it cannot slow down below its minimum speed and its motors react with a delay. The real robot's path stays close to the simulator's, so the controller works the same way in both. Whether the rest of the difference is a *localization* problem depends on the tape measurement: if it is far from what the odometry says, the robot does not know where it really is; if it is close, the remaining error is only from control.
