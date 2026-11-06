# hello-motion

A hardware notebook for turning first spin into controlled motion — one degree of freedom at a time.

A bench-scale BLDC actuator built on a moteus r4.11 developer kit: command one axis accurately, understand its limits, and log what actually happened.

This repository is code, docs, and data. Chronological build notes live in `logs/`; durable procedures live in `docs/`; logged telemetry lives in `data/`.

## Status

- ✅ **Software environment documented** — `moteus` + `moteus-gui` in a venv, Windows, Python 3.13. Pinned in `software/requirements.txt`.
- ✅ **First communication and encoder verification** — encoder tracked by hand-rotation with zero commanded torque. See `logs/004-first-comms.md`.
- ✅ **First continuous spin** — velocity mode, direction reversible.
- ✅ **Velocity ceiling measured and cause isolated** — the 8 rev/s plateau was a configured limit, not the motor. See below.
- ✅ **Gear reduction selected** — StepperOnline EG17-G5 5:1 planetary reducer. Vendor model and drawing in `cad/vendor/`.
- ✅ **CAD fixtures designed for the gearbox implementation** — hub, actuator stand, gearbox support, and a faceplate sample. Four STEPs and four print STLs in `cad/r03/`. See below.
- 🔧 **Confirming the prototype 3D-printed parts fit**
- 🔲 **Final fixture machined in aluminum**

## The velocity ceiling that wasn't

Early spin sessions showed speed flattening out well below the commanded value. The working guess, recorded in `logs/005`, was the 24 V bus voltage ceiling.
That guess was wrong.

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

Raising `servo.default_velocity_limit` to 40 and `servo.max_velocity` to 50 removed the wall. The actuator then tracked every commanded step up to 32 rev/s exactly, with torque unchanged at ~0.010 Nm.

→ `logs/006-first-scripted-measurement.md` for the full session, including the failures.

## Geared-axis fit check

The bare MJ5208 actuator runs in both directions on the bench, and the scripted sweep tracked commands through 32 rev/s. The next rung is adding gear reduction: a StepperOnline EG17-G5 5:1 planetary reducer on the moteus developer kit, held by custom fixtures.

### What was designed

Four custom parts, all in `cad/r03/` as STEPs and print STLs, built from the vendor models with a parametric CadQuery script:

- **Companion hub** — connects the motor output to the gearbox input bore.
- **Actuator stand** — mounts the existing dev-kit bracket and holds the motor in place.
- **Gearbox support** — carries the reducer housing independent of the motor shaft, with the faceplate built in.
- **Loose faceplate** — a separate sample of the gearbox joint, for checking the interface on its own. It does not stack into the assembled fixture.

The steel base plate (14 × 12 × 0.5 in) is proposed as the common datum for both supports.

### What changed across the design rounds

The first faceplate opening interfered with the hub flange, so it was enlarged. The stand base opens around the gearbox support, and a pocket clears the motor cable. The gearbox joint is a reversed M3: screw head on the gearbox side, nut captured in a hex pocket on the motor side, sized from a measured nut. The screws that came with the gearbox measured too short for the stack, so M3x10 is the fastener. A straight driver hits the housing at all four screws; a short L-key clears the modeled path.

The design passed 115 fixture checks and 340 vendor-geometry checks in CAD. Dimensions and the full check record are in `logs/007-geared-axis-fit-check.md`.

Printed parts are PETG, for unpowered dimensional checks only. Never power the PETG hub.

## Hardware

| Part | Detail |
| --- | --- |
| Controller | moteus r4.11, factory pre-calibrated, integrated encoder |
| Motor | mj5208, 12N14P, 7 pole-pairs |
| Reducer | StepperOnline EG17-G5, 5:1 planetary, 9 Nm max permissible torque |
| Adapter | mjCanfd-usb-1x, USB ↔ CAN-FD |
| Supply | 24 V 5 A bench supply, XT30 |
| Host | Windows, Python 3.13, venv |

## The build ladder

1. **Bare actuator** — command position, velocity, and torque accurately; understand stiffness, limits, and failure modes for one axis.
2. **Actuator as a joint** (current rung) — add gear reduction; study backlash, effective stiffness, torque change.
3. **Joint does work** — add a link and end effector; move and hold a load.
4. **More than one axis** — coordinate two axes.

Each rung raises cost, energy, and risk. Finish the current one honestly before climbing.

## Repository layout

```
hello-motion/
├── AGENTS.md                      # rules for coding agents working here
├── bom/
│   └── bom_v0.csv                 # actuator kit parts
├── cad/
│   ├── vendor/                    # supplied models: EG17-G5, MJ5208, moteus bracket
│   ├── r03/                       # fit-check candidate: 4 STEPs, 4 STLs, script, checks
│   └── hub-original/              # first hub STL + build script (Slant print)
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

- mjbots/moteus — controller hardware, firmware, and Python library
- moteus documentation
