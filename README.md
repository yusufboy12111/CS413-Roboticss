# Lab 3 – Line Following (test setup)

Two light sensors look at the black line, and a controller turns the difference between them into a steering correction. On the real robot I use a full PID, and the robot also slows down when the error is large, so it takes turns carefully instead of running off the line. In the simulator I tested P, PI, PD, PID and a nonlinear controller. The nonlinear one did best: it oscillated less and lost the line less often. When the line has a gap, the robot turns gently toward the side where it last saw the line until it finds it again.

## Test setup

This folder is a test copy of `Lab3`. The controllers, gains, base speed and timings are the same. Only the simulator world is different:

- The whole track is moved to a new place on the field (now in the upper-right area of the field, right of the vertical axis and above the horizontal one). The track shape, including the gap, is unchanged.
- The robot starts at the **beginning of the line**, at the end of the bottom diagonal next to the gap, heading along it toward the bottom-left corner. It drives the loop clockwise and crosses the gap last.
- The robot is placed next to the line the same way as in the original (A3 on the outer edge of the line, A4 on the white, about 35° toward the line), so the startup calibration gives the same values.

## Simulator program – `line_sim.qrs`

The nonlinear controller is PID plus a cubic term. You can also read it as a P gain that grows with the error, `gain = kP + kN·e²`. Small errors get a soft correction, so the robot doesn't zig-zag on straights. Large errors get a sharp one, so it stays on the line in turns. Setting `kN = 0` gives the linear controllers (P / PI / PD / PID, depending on which of `kI` and `kD` are non-zero).

Init block (runs once; calibration is read at the start position):

```
calL = sensorA3;
calR = sensorA4;
lostLvl = 5;
speed = 20;
kP = 0.5;
kI = 0;
kD = 0;
kN = 0.0005;
turnG = 4;
lastSide = -1;
sumE = 0;
prevE = 0;
```

Control loop (every 30 ms):

```
delta = (sensorA4 - calR) - (sensorA3 - calL);
sumE = sumE + delta;
gain = kP + kN * delta * delta;
u = gain * delta + kI * sumE + kD * (delta - prevE);
prevE = delta;

if (sensorA3 < lostLvl and sensorA4 < lostLvl) {   // line lost
    sumE = 0;
    motor M3 = speed + lastSide * turnG;
    motor M4 = speed - lastSide * turnG;
} else {
    if (sensorA4 > lostLvl) { lastSide = 1; } else { lastSide = -1; }
    motor M3 = speed + u;
    motor M4 = speed - u;
}
wait 30 ms;
```

## Real robot program – `line_real.qrs`

On the real robot the sensors are mounted the other way round (A4 on the left, A3 on the right). The integral is clamped to ±`iLim` to prevent windup, and the forward speed drops in proportion to `|error|`.

Init block (runs once):

```
calL = sensorA4;
calR = sensorA3;
base = 30;
kP = 1.3;
kI = 0.01;
kD = 15;
kS = 0.35;
iLim = 200;
acc = 0;
prevE = 0;
speed = base;
```

Control loop (every 1 ms):

```
delta = (sensorA4 - calL) - (sensorA3 - calR);
acc = max(-iLim, min(iLim, acc + delta * 0.01));
dE = (delta - prevE) / 10;
u = kP * delta + kI * acc + kD * dE;
prevE = delta;
speed = base - kS * abs(delta);

motor M3 = speed + u;
motor M4 = speed - u;
wait 1 ms;
```
