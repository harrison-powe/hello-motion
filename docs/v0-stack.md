# v0 stack

## selected path

v0 uses a moteus r4.11 developer-kit style integrated BLDC servo path.

## intent

- one BLDC actuator
- one bench-scale test stand
- one controlled axis
- off-the-shelf motor control hardware
- encoder feedback
- CAN-FD communication
- logging and measurement before revision

## why this path

- reduce early integration variables
- keep power electronics off-the-shelf
- focus v0 work on safe bench motion, fixture design, telemetry, logging, and measurement
- leave custom motor drive work out of scope for v0

## current status

- path selected
- kit received, contents matched
- moteus tooling installed; first communication established
- encoder verified (position tracks hand-rotation, zero commanded torque)
- no motor calibration yet
- no commanded motion, no first spin yet
- no measurements yet

## references

- [mjbots moteus r4.11 developer kit](https://mjbots.com/products/moteus-r4-11-developer-kit)
- [mjbots moteus r4.11 controller](https://mjbots.com/products/moteus-r4-11)
- [mjbots moteus documentation](https://mjbots.github.io/moteus/)
