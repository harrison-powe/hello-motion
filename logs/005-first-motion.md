# 005 - first commanded motion, stiffness sweep, first spin

First commanded closed-loop motion achieved: position hold, tunable stiffness, and continuous rotation under command.

Startup readings:
- bus voltage ~24.6 V
- servo_stats.fault 0
- mode stopped

Motor identity:
- confirmed 12N14P by direct count: 12 stator teeth, 14 rotor magnets (7 pole-pairs)
- consistent with the mj5208 line in bom/bom_v0.csv

Position hold and stiffness:
- commanded closed-loop hold via tview diagnostic console (d pos, nan position to hold current position)
- shaft resists manual displacement; torque_Nm and power_W rise when pushed, settle on release
- swept position gain: soft (p0.25) held at ~0.12 Nm, firm (p1) at ~0.5 Nm for a similar hand-applied push
- caveat: displacement was matched by hand, not measured; the firm figure (~0.5 Nm) was at the commanded torque cap and was likely cap-limited rather than a true restoring-torque reading
- this is an observation, not a measurement; a logged, displacement-controlled version belongs in a scripted follow-up

First spin:
- velocity mode (d pos, nan position, nonzero velocity); direction reversible via sign of velocity
- spun smoothly and continuously
- commanded velocities up to 32 rev/s with the torque cap raised to 1.0 Nm, but actual speed was not read from servo_stats.velocity; observed motion above ~4 rev/s did not visibly increase, suggesting the motor was velocity-limited (likely the 24 V bus voltage ceiling) well below the commanded value
- open question: measure actual velocity vs commanded to find the real speed ceiling
- note: high commanded speeds on a tape-secured stand exceeded the intended conservative bench envelope; a rigid mount should precede pushing speed

Troubleshooting (both resolved in-session):
- console commands silently failed (bare prompt, no ack) while telemetry still streamed; root cause was a Windows serial write error on the CAN-FD adapter, triggered by overlapping port ownership between moteus_tool and tview. Fixed by keeping a single owner of the COM port (do not run moteus_tool and tview against the board at the same time); a USB replug clears a wedged port.
- position commands faulted immediately with fault 39 (outside limit) because the shaft position was outside the configured position bounds. Fixed with d stop then d rezero to set a fresh zero inside the limits before commanding.

Not done this session:
- no scripted/Python control yet
- no logged telemetry to data/
- no rigorous stiffness or speed measurement

Next:
- move to the moteus Python library: scripted commands, telemetry logged to data/
- automate the stiffness test with measured displacement so the soft/firm comparison is a real measurement, not a hand-matched observation
- measure actual velocity vs commanded to find the real speed ceiling
- secure the stand rigidly (clamp or bolt) before further high-speed runs
