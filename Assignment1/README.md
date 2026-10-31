# CS413 Robotics – Lab 5: Motor identification (TRIK M3 and M4)

Notebook: `robotics_lab5_STUDENTID.ipynb` (runs top to bottom on `motor_data/`).

## Programs (TRIK Studio visual programs)
| Program | File in `qrs_files/` | Data file in `motor_data/` |
|---|---|---|
| Steps, M4 | `1_steps_M4.qrs` (= `motor_steps.qrs`) | `steps_M4.txt` |
| Steps, M4 repeat | `2_steps_M4_repeat.qrs` | `steps_M4_repeat.txt` |
| Steps, M3 | `3_steps_M3.qrs` | `steps_M3.txt` |
| Square wave, M4 | `4_square_M4.qrs` (= `motor_signal.qrs`) | `square_M4.txt` |
| Square wave, M3 | `5_square_M3.qrs` | `square_M3.txt` |
| Chirp, M4 | `6_chirp_M4.qrs` | `chirp_M4.txt` |
| Chirp, M3 | `7_chirp_M3.qrs` | `chirp_M3.txt` |
| Dead-zone run (PWM -9…+9 %, 1 % steps), M4 | `8_deadzone_M4.qrs` | `deadzone_M4.txt` |
| Dead-zone run (PWM -9…+9 %, 1 % steps), M3 | `9_deadzone_M3.qrs` | `deadzone_M3.txt` |

Raw files are exactly as the robot wrote them (columns: angle [deg], time [ms], PWM [%]); only the file names were shortened.
`battery.txt` holds the battery voltage used to convert PWM to volts.
