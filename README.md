# hello-motion

A hardware notebook for turning first spin into controlled motion — one degree of freedom at a time.

A bench-scale BLDC actuator built on a moteus r4.11 developer kit: command one axis accurately, understand its limits, and log what actually happened.

This repository is code, docs, and data. Chronological build notes live in `logs/`; durable procedures live in `docs/`; logged telemetry lives in `data/`.

## Status

- ✅ **Kit received and inspected** — moteus r4.11 developer kit, contents checked against `bom/bom_v0.csv`. See `logs/003-kit-received.md`.
- ✅ **Software environment documented** — `moteus` + `moteus-gui` in a venv, Windows, Python 3.13. Pinned in `software/requirements.txt`.
- ✅ **First communication and encoder verification** — encoder tracked by hand-rotation with zero commanded torque. See `logs/004-first-comms.md`.
- ✅ **Motor confirmed 12N14P** — 12 stator teeth, 14 rotor magnets, 7 pole-pairs, by direct count.
- ✅ **Closed-loop position hold with tunable stiffness** — the shaft resists displacement, and gain scaling changes how hard. Recorded as an observation, not a measurement. See `logs/005-first-motion.md`.
- ✅ **First continuous spin** — velocity mode, direction reversible.
- ✅ **First scripted control and logged telemetry** — `software/velocity_sweep.py` writes commanded-vs-actual velocity to `data/raw/`.
- ✅ **Velocity ceiling measured and cause isolated** — see below.
- 🔧 **Stiffness** — still a hand-matched observation. The displacement-controlled measurement has not been done.
- 🔲 **True velocity ceiling** — not reached; no strain at 32 rev/s.
- 🔲 **CAD, gear reduction, load, second axis** — not started.

Anything not marked ✅ has no evidence in this repository and is not claimed.

## The velocity ceiling that wasn't

Early spin sessions showed speed flattening out well below the commanded value. The working guess, recorded in `logs/005`, was the 24 V bus voltage ceiling. That guess was wrong.

Scripting the sweep and logging actual velocity answered it in one run:

| commanded rev/s | actual rev/s | ratio | torque Nm |
| --- | --- | --- | --- |
| 2 | 2.00 | 1.00 | 0.007 |
| 4 | 4.00 | 1.00 | 0.007 |
| 6 | 6.00 | 1.00 | 0.010 |
| 8 | 8.00 | 1.00 | 0.010 |
| 12 | 8.00 | 0.67 | 0.010 |

The plateau sat at exactly 8.00 rev/s, matching `servo.default_velocity_limit = 8`. Torque there was 0.010 Nm against a 1.0 Nm cap — one percent. The bus held steady at 24.50 V, and the firmware's own computed limit (`servo_stats.motor_max_velocity`) was 97.59 rev/s, roughly twelve times the observed ceiling.

The controller was never straining. The command was being truncated before it reached the motor, and a commanded velocity above a configured limit is truncated silently, with no fault raised.

Raising `servo.default_velocity_limit` to 40 and `servo.max_velocity` to 50 removed the wall. The actuator then tracked every commanded step up to 32 rev/s exactly, with torque unchanged at ~0.010 Nm. The real ceiling is still unmeasured.

→ `logs/006-first-scripted-measurement.md` for the full session, including the failures.

## Hardware

| Part | Detail |
| --- | --- |
| Controller | moteus r4.11, factory pre-calibrated, integrated encoder |
| Motor | mj5208, 12N14P, 7 pole-pairs |
| Adapter | mjCanfd-usb-1x, USB ↔ CAN-FD |
| Supply | 24 V 5 A bench supply, XT30 |
| Host | Windows, Python 3.13, venv |

## The build ladder

1. **Bare actuator** (current rung) — command position, velocity, and torque accurately; understand stiffness, limits, and failure modes for one axis.
2. **Actuator as a joint** — add gear reduction; study backlash, effective stiffness, torque change.
3. **Joint does work** — add a link and end effector; move and hold a load.
4. **More than one axis** — coordinate two axes.

Each rung raises cost, energy, and risk. Finish the current one honestly before climbing.

## Repository layout

```text
hello-motion/
├── AGENTS.md                      # rules for coding agents working here
├── bom/
│   └── bom_v0.csv                 # actuator kit parts
├── cad/
├── data/
│   ├── raw/                       # logged telemetry, one CSV per run
│   └── processed/
├── docs/
│   ├── architecture.md
│   ├── bench-bringup.md           # cold bench -> controller that provably replies
│   ├── first-power-checklist.md
│   ├── receiving-checklist.md
│   ├── requirements.md
│   ├── safety.md
│   └── v0-stack.md
├── electronics/
│   └── wiring.md
├── logs/                          # chronological build notes, 000 onward
├── media/
└── software/
    ├── requirements.txt           # pinned environment
    └── velocity_sweep.py          # commanded vs actual velocity, logs to data/raw/
```

## Upstream

- [mjbots/moteus](https://github.com/mjbots/moteus) — controller hardware, firmware, and Python library
- [moteus documentation](https://mjbots.github.io/moteus/)
