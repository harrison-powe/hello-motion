# Bench bring-up

Getting from a cold bench to a controller that provably responds, before any
other work starts.

## Why this exists

Several different failures present identically from the host side:

- bus power not connected
- CAN cable not fully seated
- serial port already owned by another process

In all three cases the USB CAN adapter enumerates, Windows shows the device, and
the Python transport is found. The host looks healthy. Nothing comes back from
the controller.

The adapter is powered over USB and enumerates whether or not the controller has
24 V. "The computer sees the adapter" therefore says nothing about whether the
board is alive. Diagnosing from that signal wastes bench time.

## Order of operations

1. Bus power on. Confirm the controller status LED is lit.
2. USB adapter connected.
3. Activate the venv: `cd ~\Projects; moteus-venv\Scripts\activate`
4. Prove the board replies (below) before anything else.

## Step zero: prove the board replies

```powershell
python -c "import asyncio,moteus; c=moteus.Controller(id=1); print(asyncio.run(asyncio.wait_for(c.query(),2)))"
```

Bounded at two seconds, commands no motion. Three outcomes:

- **Register values printed** — board is alive. Note bus voltage and fault.
- **`TimeoutError`** — adapter found, board silent. Power or CAN cable.
- **`Unable to find a default transport`** — host does not see the adapter.
  Replug USB and check Device Manager.

A command that does not wait for a reply proves nothing. `set_stop()` returns
successfully against a completely dark board, because it does not query. Only a
reply proves the link.

## One owner of the serial port

Do not run `tview` and a script or `moteus_tool` against the board at the same
time. Overlapping port ownership wedges the serial write channel: telemetry may
still stream while commands are silently unacknowledged.

Close tview before running any script.

## Bounded commands only

Every read or command against the board should have a timeout. An unbounded read
against a board that is not answering hangs indefinitely and gives no
information. `moteus_tool --target 1 --info` has no timeout and will hang.

## Recovery ladder

Work down this list, re-testing with step zero after each:

1. Confirm bus power and controller LED.
2. Confirm the XT30 is seated at both ends.
3. Reseat the JST PH-3 CAN cable at both ends. A partially seated CAN connector
   produces garbled telemetry and, in tview, `list index out of range`.
4. Check for processes holding the port:
   `Get-Process | Where-Object {$_.ProcessName -match 'python|tview'}`
5. Cold-boot the adapter: USB and bus power both removed, 15 to 20 seconds, bus
   power back first, then USB.
6. Reboot the host.

## Fault codes and limiting flags

Codes reported in the fault register split into two categories:

- **Below 100: faults.** The controller has stopped. Examples: 33 motor driver
  fault (commonly undervoltage), 39 outside position limit.
- **100 and above: torque-limiting indicators.** The controller is still
  running; something is capping output current. 102 `max_torque`, 103
  `position_bounds`, 104 `flux_braking`.

Do not treat a limiting flag as a failure. Aborting on one stops a valid run.

Recovering a fault 39 before commanding position: `d stop`, then `d rezero`.

## Velocity mode

Velocity mode is a position command with position set to NaN.

Position bounds (`servopos.position_min` / `position_max`) are the wrong
constraint for continuous rotation, because the motor always leaves them. Set
`ignore_position_bounds` on the command, or widen the bounds.

## Silent clamps

A commanded velocity above a configured limit is truncated silently. No fault is
raised. If actual velocity plateaus below the command while torque stays well
under the commanded cap and bus voltage holds steady, suspect a configured limit
before suspecting physics.

The limits that clamp velocity:

- `servo.default_velocity_limit`
- `servo.max_velocity` (clamps regardless of the above)
- `servo_stats.motor_max_velocity` (derived from bus voltage and motor constant;
  read, not set)

## Noise floor

`servo_stats.velocity` reads approximately 0.008 to 0.016 rev/s with the motor
stopped. Treat instantaneous velocity below roughly 0.02 rev/s as
indistinguishable from stationary, and average over a window when measuring.
