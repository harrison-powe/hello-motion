# 006 - first scripted control, first logged data, velocity ceiling measured

First Python-scripted control of the actuator, first telemetry logged to `data/`,
and the first measurement with an isolated cause. The speed ceiling observed in
the previous session was a configuration limit, not a physical one.

Startup readings:
- bus voltage 24.50 V
- servo_stats.fault 0
- mode 0 (stopped)

## What was built

`software/velocity_sweep.py`: steps commanded velocity, records actual velocity,
torque, bus voltage, position, fault, and mode at 50 Hz, and writes a CSV to
`data/raw/`. Position is commanded NaN, so this is velocity mode. `set_stop`
runs in a `finally` block so an exception or Ctrl-C cannot leave the motor
running. Commands and queries are bounded by timeouts.

## Measurement: ceiling at the as-configured limit

Sweep at the configuration as it stood, torque cap 1.0 Nm:

| commanded rev/s | actual rev/s | ratio | torque Nm |
| --- | --- | --- | --- |
| 2 | 2.00 | 1.00 | 0.007 |
| 4 | 4.00 | 1.00 | 0.007 |
| 6 | 6.00 | 1.00 | 0.010 |
| 8 | 8.00 | 1.00 | 0.010 |
| 12 | 8.00 | 0.67 | 0.010 |

Ceiling: 8.00 rev/s. 1796 samples, `data/raw/velocity-sweep-20260731-110337.csv`.

Configuration read afterward:

```text
servo.default_velocity_limit = 8
servo.default_accel_limit    = 20
servo.max_velocity           = 10
servo.max_power_W            = nan
```

From `servo_stats`:

```text
motor_max_velocity        = 97.59
motor_base_velocity       = 97.58
effective_max_current_A   = 100.0
max_power_W               = 900.0
```

The measured ceiling matches `servo.default_velocity_limit` exactly. Torque at
the plateau was 0.010 Nm against a 1.0 Nm commanded cap, and bus voltage held at
24.50 V with no sag. The firmware's own computed velocity limit is 97.59 rev/s,
roughly twelve times the observed ceiling. The controller was not straining; the
commanded velocity was being truncated before it reached the motor.

Per the moteus documentation, a commanded velocity exceeding a configured limit
is truncated silently and is not reported through the fault code mechanism. That
is consistent with the plateau appearing with no fault raised.

## Correction to log 005

`logs/005-first-motion.md` recorded the working hypothesis that the observed
speed limit was "likely the 24 V bus voltage ceiling." That hypothesis is wrong.
The cause was `servo.default_velocity_limit = 8`. The evidence above (1% torque
utilisation, steady bus voltage, and a firmware-computed limit of 97.59 rev/s)
rules out a voltage or torque limit at 8 rev/s.

## Configuration change

Raised and persisted with `conf write`:

```text
servo.default_velocity_limit  8 -> 40
servo.max_velocity           10 -> 50
```

Both were raised because `servo.max_velocity` clamps regardless of
`servo.default_velocity_limit`. This change persists across power cycles.

## Second sweep after raising the limits

Torque cap 1.0 Nm, same script:

| commanded rev/s | actual rev/s | ratio | torque Nm |
| --- | --- | --- | --- |
| 2 | 2.00 | 1.00 | 0.007 |
| 4 | 4.00 | 1.00 | 0.007 |
| 6 | 6.00 | 1.00 | 0.010 |
| 8 | 8.00 | 1.00 | 0.010 |
| 12 | 12.00 | 1.00 | 0.011 |
| 16 | 16.00 | 1.00 | 0.009 |
| 24 | 24.00 | 1.00 | 0.011 |
| 32 | 32.00 | 1.00 | 0.010 |

2880 samples, `data/raw/velocity-sweep-20260731-110906.csv`. Tracking was exact
at every step. Torque remained at approximately 0.010 Nm at 32 rev/s, unchanged
from 2 rev/s, and bus voltage held at 24.50 V throughout.

No ceiling was found up to 32 rev/s. The true physical limit was not reached and
remains unmeasured. The stand was held by hand during these runs; nothing moved.

## Troubleshooting

Three failures during this session presented identically: the USB CAN adapter
enumerated, the Python transport was found, and nothing came back from the
controller.

- Bus power was not connected. The adapter is powered over USB and enumerates
  whether or not the controller has 24 V, so the host looked healthy while the
  board was dark. This consumed the first part of the session.
- An unbounded config read over the diagnostic stream hung indefinitely against
  the unpowered board. Reads are now bounded by a timeout.
- Position commands stopped with code 103 shortly after reaching speed. Per the
  moteus documentation, codes at 100 and above reported in the fault register
  during position mode are torque-limiting indicators, not failures. 103 is
  `position_bounds`: position had travelled outside `servopos.position_min` /
  `position_max`, so torque was limited in the direction that would push it
  further out. Continuous rotation always exits position bounds, so the sweep
  sets `ignore_position_bounds`. This is the same underlying cause as the fault
  39 recorded in log 005.

`servo_stats.velocity` reads approximately 0.008 to 0.016 rev/s with the motor
stopped, so instantaneous velocity has a noise floor near 0.01 rev/s.
Instantaneous readings at low commanded speeds vary by a few tenths of a rev/s;
the mean over each measurement window tracked the commanded value exactly.

## Not done this session

- true physical velocity ceiling (not reached at 32 rev/s)
- stiffness measurement with controlled displacement (still a hand observation
  from log 005)
- any load, gearing, or second axis

## Open questions

- Where is the actual velocity ceiling, and what limits it first: bus voltage,
  current, or power?
- tview did not connect during this session: empty config and telemetry trees,
  no acknowledgement to console commands. Cause not isolated. It has now
  interfered with two sessions and deserves a dedicated investigation rather
  than a guess.

## Next

- Automate the stiffness test with measured displacement.
- Investigate tview connection behaviour on its own, not mid-session.
