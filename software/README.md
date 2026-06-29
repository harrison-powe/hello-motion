# software

Control, logging, and plotting code will live here as it is written.
For now this documents the bench software environment used to talk to the moteus controller.

## environment

- OS: Windows
- Python: 3.13
- isolated virtual environment (venv), kept outside the repo

## tooling

- `moteus` 1.0.0 — controller library and `moteus_tool` command-line utility
- `moteus-gui` 1.0.0 — `tview` telemetry/config GUI

Exact pinned dependencies are in `requirements.txt`.

## setup

```
python -m venv moteus-venv
moteus-venv\Scripts\activate
pip install moteus moteus-gui
```

To reproduce the exact environment instead:

```
pip install -r software/requirements.txt
```

## use

Query a connected controller (device id 1):

```
python -m moteus.moteus_tool --target 1 --info
```

Launch the telemetry GUI:

```
python -m moteus_gui.tview
```

The mjcanfd-usb-1x CAN-FD adapter is auto-detected over its serial interface; no device path is normally required.

## notes

- The controller must have bus power before it will respond.
- See `logs/` for what has actually been run on hardware.
