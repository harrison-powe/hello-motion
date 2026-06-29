# 004 - first comms

First communication with the moteus r4.11 controller established.

Current state:
- moteus and moteus-gui installed (tview, moteus_tool); Windows, Python 3.13
- data chain: laptop -> USB -> mjCanfd-usb-1x -> JST PH-3 CAN -> moteus
- 24V supply connected; controller and adapter status LEDs lit
- moteus_tool --target 1 --info returned a clean response; firmware confirmed, git_dirty false
- tview connected; full telemetry schema read from board
- encoder verified: servo_stats.position tracked hand-rotation of the shaft with zero commanded torque

Not done this session:
- no motor calibration
- no commanded motion, no first spin

Not recorded this session:
- bus voltage
- servo_stats.fault

Next:
- record bus voltage and servo_stats.fault at session start
- motor calibration in a dedicated session (spins motor hard in both directions; secure stand, clear shaft, kill path ready)
