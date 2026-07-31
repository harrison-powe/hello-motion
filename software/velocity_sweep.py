#!/usr/bin/env python3
"""
velocity_sweep.py -- first scripted, logged measurement for hello-motion.

Steps commanded velocity upward and records ACTUAL velocity from the
controller, so the speed ceiling becomes a measured number instead of an
eyeballed observation.

Position is commanded as NaN (no position target), so this is velocity mode
and will not trip the "outside limit" fault-39 path.

BENCH SAFETY / PRECONDITIONS
  - Close tview first. One owner of the COM port at a time, or the serial
    write channel wedges.
  - Hand on the kill path (yellow XT30 at the motor).
  - Stand secured. Tape is fine only for the low steps; clamp or bolt it
    before letting the sweep run past ~6 rev/s.
  - Ctrl-C is safe: the finally block issues a stop.

USAGE
  python velocity_sweep.py                      # default sweep, 1.0 Nm cap
  python velocity_sweep.py --max-vel 8          # stay gentle, validate first
  python velocity_sweep.py --torque 2.0         # re-run at a higher cap

THE DISCRIMINATOR
  Run once at --torque 1.0, then again at --torque 2.0.
    plateau MOVES up          -> torque-cap limited
    plateau STAYS, == config  -> configured velocity limit
    plateau STAYS, config high-> voltage / back-EMF ceiling
"""

import argparse
import asyncio
import csv
import math
import os
import sys
import time
from datetime import datetime

import moteus

DEFAULT_STEPS = [2, 4, 6, 8, 12, 16, 24, 32]

# Codes >= 100 in the fault register are torque-LIMITING indicators reported
# while in position mode, not failures. Verified against mjbots docs.
LIMIT_FLAGS = {
    101: "motor temperature",
    102: "max_torque",
    103: "position_bounds",
    104: "flux_braking",
}

CONFIG_KEYS = [
    "servo.default_velocity_limit",
    "servo.default_accel_limit",
    "servo.max_velocity",
    "servo.max_power_W",
]


async def read_config(stream, timeout):
    """Read config values via the diagnostic stream.

    Every read is bounded by a timeout and printed as it resolves. The
    diagnostic stream is not required for the measurement, so a stream that
    never answers costs a few seconds, not the session.
    """
    found = {}
    for key in CONFIG_KEYS:
        try:
            raw = await asyncio.wait_for(
                stream.command(
                    f"conf get {key}".encode("latin1"), allow_any_response=True
                ),
                timeout=timeout,
            )
            found[key] = raw.decode("latin1").strip()
        except asyncio.TimeoutError:
            found[key] = f"<no response in {timeout}s>"
        except Exception as exc:
            found[key] = f"<unreadable: {type(exc).__name__}>"
        print(f"  {key:34s} = {found[key]}", flush=True)
    return found


async def run(args):
    os.makedirs(args.outdir, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    outpath = os.path.join(args.outdir, f"velocity-sweep-{stamp}.csv")

    transport = None
    controller = moteus.Controller(id=args.id, transport=transport)
    stream = moteus.Stream(controller)

    # Clear any latched fault and start from a known stopped state.
    await controller.set_stop()

    # Preflight: prove the board actually REPLIES before commanding motion.
    # set_stop() above does not wait for a response, so it proves nothing.
    print("Preflight -- checking the controller replies...", flush=True)
    try:
        probe = await asyncio.wait_for(
            controller.query(), timeout=args.reply_timeout
        )
        print(
            f"  reply OK: bus {probe.values[moteus.Register.VOLTAGE]:.2f} V, "
            f"fault {int(probe.values[moteus.Register.FAULT])}, "
            f"mode {int(probe.values[moteus.Register.MODE])}\n",
            flush=True,
        )
    except asyncio.TimeoutError:
        print(
            "  NO REPLY from the controller.\n"
            "  Sends are going out but nothing is coming back.\n"
            "  Check: JST PH-3 CAN cable seated at BOTH ends; controller LED lit;\n"
            "  XT30 seated; tview closed (one COM port owner);\n"
            "  cold-boot the adapter (USB + bus power out, 15-20s).\n"
            "  Known-good check: moteus_tool --target 1 --info\n",
            flush=True,
        )
        return

    print("=" * 62)
    print("STEP 1 -- config read (no motion)")
    print("=" * 62)
    if args.skip_config:
        cfg = {}
        print("  skipped (--skip-config); read it by hand in tview afterward.")
    else:
        cfg = await read_config(stream, args.config_timeout)
    print()
    print("  NOTE: nan or a very large value means effectively unlimited.")
    print("  If default_velocity_limit is a low number, that is very likely")
    print("  the ceiling, and it is a config value rather than physics.")
    print()

    period = 1.0 / args.rate
    rows = []
    summary = []

    print("=" * 62)
    print(f"STEP 2/3 -- sweep, torque cap {args.torque} Nm")
    print("=" * 62)
    print(f"{'cmd rev/s':>10} {'actual':>9} {'ratio':>7} {'torque':>8} {'bus V':>7}")

    fault_code = 0
    limit_flags_seen = set()
    t_zero = time.time()

    try:
        for commanded in args.steps:
            if commanded > args.max_vel:
                break

            step_start = time.time()
            samples = []

            while True:
                elapsed_step = time.time() - step_start
                if elapsed_step > (args.settle + args.dwell):
                    break

                result = await asyncio.wait_for(
                    controller.set_position(
                        position=math.nan,
                        velocity=float(commanded),
                        maximum_torque=args.torque,
                        accel_limit=args.accel_limit,
                        velocity_limit=args.velocity_limit,
                        ignore_position_bounds=not args.respect_position_bounds,
                        query=True,
                    ),
                    timeout=args.reply_timeout,
                )

                v = result.values
                actual = v[moteus.Register.VELOCITY]
                torque = v[moteus.Register.TORQUE]
                bus_v = v[moteus.Register.VOLTAGE]
                fault_code = int(v[moteus.Register.FAULT])
                mode = int(v[moteus.Register.MODE])
                measuring = elapsed_step >= args.settle

                rows.append(
                    {
                        "wall_clock": datetime.now().isoformat(timespec="milliseconds"),
                        "elapsed_s": round(time.time() - t_zero, 4),
                        "commanded_vel_revps": commanded,
                        "actual_vel_revps": round(actual, 4),
                        "position_rev": round(v[moteus.Register.POSITION], 4),
                        "torque_Nm": round(torque, 4),
                        "bus_voltage_V": round(bus_v, 3),
                        "torque_cap_Nm": args.torque,
                        "fault": fault_code,
                        "mode": mode,
                        "phase": "measure" if measuring else "settle",
                    }
                )

                if measuring:
                    samples.append((actual, torque, bus_v))

                if args.live and len(rows) % max(1, int(args.rate * 0.5)) == 0:
                    tag = "meas" if measuring else "sett"
                    print(
                        f"    [{tag}] t={elapsed_step:4.1f}s  cmd={commanded:<5}"
                        f"actual={actual:8.3f}  torque={torque:7.3f}",
                        flush=True,
                    )

                if fault_code >= 100:
                    # 100+ are torque-LIMITING indicators, not failures.
                    # The controller is still running; something is capping
                    # output current. Worth knowing, not worth aborting.
                    if fault_code not in limit_flags_seen:
                        limit_flags_seen.add(fault_code)
                        name = LIMIT_FLAGS.get(fault_code, "unknown limit")
                        print(
                            f"    note: limiting flag {fault_code} ({name}) "
                            f"-- continuing",
                            flush=True,
                        )
                elif fault_code != 0:
                    print(f"\n  !! fault {fault_code} at {commanded} rev/s -- aborting")
                    raise RuntimeError(f"controller fault {fault_code}")

                await asyncio.sleep(period)

            if samples:
                mean_v = sum(s[0] for s in samples) / len(samples)
                mean_t = sum(s[1] for s in samples) / len(samples)
                mean_bus = sum(s[2] for s in samples) / len(samples)
                ratio = mean_v / commanded if commanded else float("nan")
                summary.append((commanded, mean_v, ratio, mean_t, mean_bus))
                print(
                    f"{commanded:>10} {mean_v:>9.2f} {ratio:>7.2f} "
                    f"{mean_t:>8.3f} {mean_bus:>7.2f}"
                )

                if ratio < args.tracking_threshold:
                    tracked_before = any(
                        s[2] >= args.tracking_threshold for s in summary[:-1]
                    )
                    if not tracked_before:
                        print(
                            "\n  Actual never tracked commanded on this step.\n"
                            "  That is NOT a ceiling -- with a configured accel limit the\n"
                            "  internal target ramps, so a short dwell ends before the\n"
                            "  motor gets up to speed. Near-zero torque with no fault is\n"
                            "  the signature. Raise --dwell, or override --accel-limit.\n"
                            "  Continuing the sweep."
                        )
                        continue
                    print(
                        f"\n  Actual stopped tracking commanded "
                        f"(ratio {ratio:.2f} < {args.tracking_threshold}). "
                        f"Ceiling found near {mean_v:.2f} rev/s."
                    )
                    if not args.no_early_stop:
                        print("  Stopping the sweep here.")
                        break

    except KeyboardInterrupt:
        print("\n  Ctrl-C -- stopping.")
    except Exception as exc:
        print(f"\n  Aborted: {exc}")
    finally:
        # Always stop the motor, whatever happened above.
        try:
            await controller.set_stop()
            print("\n  Motor stopped (set_stop issued).")
        except Exception as exc:
            print(f"\n  !! set_stop failed: {exc} -- PULL THE XT30.")

    if rows:
        with open(outpath, "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        print(f"  Wrote {len(rows)} samples -> {outpath}")
    else:
        print("  No samples captured; nothing written.")

    if summary:
        print()
        print("=" * 62)
        print("STEP 4 -- result")
        print("=" * 62)
        print(f"  torque cap        : {args.torque} Nm")
        print(f"  config vel limit  : {cfg.get('servo.default_velocity_limit')}")
        tracked = [s for s in summary if s[2] >= args.tracking_threshold]
        if tracked:
            print(f"  tracked cleanly up to : {tracked[-1][0]} rev/s")
        plateau = max(s[1] for s in summary)
        print(f"  max actual velocity   : {plateau:.2f} rev/s")
        print()
        print("  Re-run at a higher --torque. If the plateau moves, it was the")
        print("  torque cap. If it does not move, it is the config limit or the")
        print("  bus voltage ceiling -- the config read above tells you which.")


def main():
    parser = argparse.ArgumentParser(description="Commanded vs actual velocity sweep.")
    parser.add_argument("--id", type=int, default=1, help="moteus CAN id")
    parser.add_argument("--torque", type=float, default=1.0, help="torque cap, Nm")
    parser.add_argument("--max-vel", type=float, default=32, help="highest rev/s")
    parser.add_argument("--dwell", type=float, default=6.0, help="measure seconds/step")
    parser.add_argument("--settle", type=float, default=2.0, help="discard seconds/step")
    parser.add_argument("--rate", type=float, default=50.0, help="sample Hz")
    parser.add_argument(
        "--tracking-threshold",
        type=float,
        default=0.85,
        help="actual/commanded below this counts as the ceiling",
    )
    parser.add_argument(
        "--respect-position-bounds",
        action="store_true",
        help="enforce servopos position bounds (they always trip when spinning)",
    )
    parser.add_argument(
        "--accel-limit",
        type=float,
        default=None,
        help="per-command accel limit override, rev/s^2 (unset = use config)",
    )
    parser.add_argument(
        "--velocity-limit",
        type=float,
        default=None,
        help="per-command velocity limit override, rev/s (unset = use config)",
    )
    parser.add_argument(
        "--no-live",
        dest="live",
        action="store_false",
        help="suppress live per-sample output",
    )
    parser.add_argument(
        "--reply-timeout",
        type=float,
        default=2.0,
        help="seconds to wait for a controller reply before failing",
    )
    parser.add_argument(
        "--skip-config",
        action="store_true",
        help="skip the diagnostic-stream config read entirely",
    )
    parser.add_argument(
        "--config-timeout",
        type=float,
        default=2.0,
        help="seconds to wait per config key before giving up",
    )
    parser.add_argument(
        "--no-early-stop",
        action="store_true",
        help="keep sweeping past the ceiling instead of stopping",
    )
    parser.add_argument(
        "--steps",
        type=float,
        nargs="+",
        default=DEFAULT_STEPS,
        help="commanded velocities, rev/s",
    )
    parser.add_argument(
        "--outdir",
        default=os.path.join("data", "raw"),
        help="CSV output directory",
    )
    args = parser.parse_args()

    try:
        asyncio.run(run(args))
    except KeyboardInterrupt:
        print("\nInterrupted.")
        sys.exit(1)


if __name__ == "__main__":
    main()
