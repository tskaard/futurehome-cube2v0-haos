#!/usr/bin/env python3
"""Log the Cube's Zigbee UART, optionally sending only two status queries.

This tool does not access GPIO, firmware files, or Home Assistant. Its default
mode only reads the serial port. --query sends a ping and an inferred version
request; it cannot enter the bootloader or upload firmware.
"""

import argparse
import os
import select
import sys
import termios
import time


PING = bytes.fromhex("aa 00 20 00 36")  # Captured from Futurehome zigbee-ad 3.8.4.
VERSION = bytes.fromhex("aa 00 20 02 34")  # Inferred from zigbee-ad 3.8.4 code.


def configure_serial(fd: int) -> None:
    settings = termios.tcgetattr(fd)
    settings[0] = 0  # No input translations or XON/XOFF flow control.
    settings[1] = 0
    settings[2] &= ~(termios.PARENB | termios.CSTOPB | termios.CSIZE)
    settings[2] &= ~getattr(termios, "CRTSCTS", 0)
    settings[2] |= termios.CS8 | termios.CREAD | termios.CLOCAL
    settings[3] = 0
    settings[4] = termios.B115200
    settings[5] = termios.B115200
    settings[6][termios.VMIN] = 0
    settings[6][termios.VTIME] = 0
    termios.tcsetattr(fd, termios.TCSANOW, settings)


def run(port: str, duration: float, query: bool) -> None:
    flags = (os.O_RDWR if query else os.O_RDONLY) | os.O_NOCTTY | os.O_NONBLOCK
    fd = os.open(port, flags)
    try:
        configure_serial(fd)
        start = time.monotonic()
        pending = [(1.0, "ping", PING), (3.0, "version (inferred)", VERSION)] if query else []
        print(f"Listening on {port} at 115200 8N1, flow control off", flush=True)
        while True:
            elapsed = time.monotonic() - start
            if elapsed >= duration:
                break
            if pending and elapsed >= pending[0][0]:
                _, label, frame = pending.pop(0)
                written = os.write(fd, frame)
                if written != len(frame):
                    raise OSError(f"short serial write: {written}/{len(frame)} bytes")
                print(f"{elapsed:7.3f}s TX {label}: {frame.hex(' ')}", flush=True)
                continue
            timeout = min(0.25, duration - elapsed)
            if pending:
                timeout = min(timeout, max(0.0, pending[0][0] - elapsed))
            readable, _, _ = select.select([fd], [], [], timeout)
            if readable:
                chunk = os.read(fd, 4096)
                if chunk:
                    print(f"{time.monotonic() - start:7.3f}s RX: {chunk.hex(' ')}", flush=True)
    finally:
        os.close(fd)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", required=True, help="Cube CP2102N serial path, e.g. /dev/ttyUSB0")
    parser.add_argument("--duration", type=float, default=8.0, help="Capture seconds (default: 8)")
    parser.add_argument("--query", action="store_true", help="Send only ping and inferred version query")
    args = parser.parse_args()
    if args.duration <= 0 or (args.query and args.duration < 4):
        parser.error("duration must be positive, and at least 4 seconds with --query")
    try:
        run(args.port, args.duration, args.query)
    except (OSError, termios.error) as error:
        print(f"Serial probe failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
