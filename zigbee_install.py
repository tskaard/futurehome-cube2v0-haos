#!/usr/bin/env python3
"""Install firmware on the Futurehome Cube 2v0 onboard Zigbee radio over serial.

EXPERIMENTAL. Read docs/zigbee.md first. Tested on one CUBE-2V0-EU hub.

The radio (EFR32MG12, behind a CP2102N at /dev/ttyUSB0) has a resident Gecko
Bootloader 1.7.0 with a Futurehome UART front end: framed commands
(AA len type cmd payload checksum) plus XMODEM-CRC with 128-byte blocks, on
USART0 at 115200 8N1 without flow control. This tool enters that bootloader
and uploads a GBL file.

How the bootloader is entered (--from):
  factory    radio runs Futurehome's original firmware (command 0x06)
  ezsp       radio runs EmberZNet firmware (EZSP launchStandaloneBootloader;
             needs bellows, e.g. run inside the Home Assistant image)
  recovery   hold radio PA4 low through a reset; works only with firmware
             that contains the Cube PA4 recovery check (needs python gpiod
             and access to /dev/gpiochip1)
  bootloader radio already waits in its bootloader

Home Assistant must not be using the serial port (stop Core or ZHA first).
When coming from the factory firmware, use a GBL that also erases the NVM3
area (0xF7000-0xFFFFF); EmberZNet does not start on the factory NVM3 data.
"""

import argparse
import os
import select
import struct
import sys
import termios
import time
import zlib

ACK, NAK, EOT, CAN, CRC_C = 0x06, 0x15, 0x04, 0x18, 0x43
GBL_HEADER, GBL_PROG, GBL_END = 0x03A617EB, 0xFD0303FD, 0xFC0404FC
NVM3_START = 0xF7000


def frame(ftype, cmd, payload=b""):
    head = bytes([0xAA, len(payload), ftype, cmd]) + payload
    return head + bytes([(-sum(head)) & 0xFF])  # whole frame sums to 0


PING = frame(0x20, 0x00)
BTL_START_APP = frame(0x20, 0x06)       # factory app: reboot into bootloader
BTL_UPLOAD = frame(0x20, 0x07)          # bootloader: start XMODEM upload
ACK_READY = frame(0x40, 0x0A, b"\x00")  # host ack of "btl ready" event
ACK_DONE = frame(0x40, 0x08, b"\x00")   # host ack of "upload done" event


def check_gbl(image):
    """Validate a GBL v3 file; return True if it writes the NVM3 area."""
    if struct.unpack_from("<I", image, 0)[0] != GBL_HEADER:
        raise ValueError("not a GBL file")
    offset, wipes_nvm3 = 0, False
    while offset + 8 <= len(image):
        tag, length = struct.unpack_from("<II", image, offset)
        if tag == GBL_PROG and struct.unpack_from("<I", image, offset + 8)[0] >= NVM3_START:
            wipes_nvm3 = True
        if tag == GBL_END:
            crc = struct.unpack_from("<I", image, offset + 8)[0]
            if zlib.crc32(image[:offset + 8]) != crc:
                raise ValueError("GBL checksum mismatch")
            return wipes_nvm3
        offset += 8 + length
    raise ValueError("GBL has no END tag")


def recovery_reset(chip="/dev/gpiochip1"):
    """Hold radio PA4 low through a reset pulse, then release both lines."""
    import gpiod
    from gpiod.line import Direction, Value

    names = {"reset": "EFR32MG12 nRESET [GPIO1_A0]", "pa4": "EFR32MG12 PA4 [GPIO1_A3]"}
    with gpiod.Chip(chip) as c:
        lines = {key: c.line_offset_from_id(name) for key, name in names.items()}
    low = gpiod.LineSettings(direction=Direction.OUTPUT, output_value=Value.INACTIVE)
    released = gpiod.LineSettings(direction=Direction.INPUT)
    with gpiod.request_lines(chip, consumer="cube-zigbee-recovery",
                             config={lines["pa4"]: low}) as pa4:
        with gpiod.request_lines(chip, consumer="cube-zigbee-recovery",
                                 config={lines["reset"]: low}) as reset:
            time.sleep(0.2)
            reset.reconfigure_lines({lines["reset"]: released})
        time.sleep(0.3)
        pa4.reconfigure_lines({lines["pa4"]: released})


class Port:
    def __init__(self, path):
        self.fd = os.open(path, os.O_RDWR | os.O_NOCTTY)
        attrs = termios.tcgetattr(self.fd)
        attrs[0] = 0
        attrs[1] = 0
        attrs[2] = termios.CS8 | termios.CREAD | termios.CLOCAL
        attrs[3] = 0
        attrs[4] = attrs[5] = termios.B115200
        attrs[6][termios.VMIN] = 0
        attrs[6][termios.VTIME] = 0
        termios.tcsetattr(self.fd, termios.TCSANOW, attrs)
        termios.tcflush(self.fd, termios.TCIOFLUSH)
        self.buf = bytearray()

    def write(self, data):
        os.write(self.fd, data)

    def fill(self, timeout):
        ready, _, _ = select.select([self.fd], [], [], timeout)
        if ready:
            self.buf += os.read(self.fd, 4096)

    def read_byte(self, timeout):
        end = time.monotonic() + timeout
        while not self.buf:
            left = end - time.monotonic()
            if left <= 0:
                return None
            self.fill(left)
        return self.buf.pop(0)

    def wait_frame(self, ftype, cmd, timeout, log):
        """Return payload of the first matching AA frame, skipping others."""
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            self.fill(0.05)
            while True:
                start = self.buf.find(0xAA)
                if start < 0:
                    self.buf.clear()
                    break
                del self.buf[:start]
                if len(self.buf) < 5 or len(self.buf) < self.buf[1] + 5:
                    break
                size = self.buf[1] + 5
                raw = bytes(self.buf[:size])
                if sum(raw) & 0xFF:
                    del self.buf[:1]
                    continue
                del self.buf[:size]
                log(f"RX {raw.hex(' ')}")
                if raw[2] == ftype and raw[3] == cmd:
                    return raw[4:-1]
        return None


def crc16(data):
    crc = 0
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) if crc & 0x8000 else crc << 1
            crc &= 0xFFFF
    return crc


def xmodem_send(port, image, log):
    log("waiting for XMODEM 'C'")
    end = time.monotonic() + 65
    while True:
        byte = port.read_byte(max(0.0, end - time.monotonic()))
        if byte == CRC_C:
            break
        if byte is None:
            raise RuntimeError("no XMODEM start from bootloader")
    blocks = [image[i:i + 128].ljust(128, b"\xff") for i in range(0, len(image), 128)]
    for number, data in enumerate(blocks, start=1):
        packet = bytes([0x01, number & 0xFF, 0xFF - (number & 0xFF)]) + data
        packet += crc16(data).to_bytes(2, "big")
        for attempt in range(10):
            port.write(packet)
            reply = port.read_byte(5)
            if reply == ACK:
                break
            if reply == CAN:
                raise RuntimeError(f"bootloader cancelled at block {number}")
            log(f"block {number}: reply {reply!r}, retry {attempt + 1}")
        else:
            raise RuntimeError(f"block {number} not acknowledged")
        if number % 200 == 0 or number == len(blocks):
            log(f"sent block {number}/{len(blocks)}")
    port.write(bytes([EOT]))
    if port.read_byte(5) != ACK:
        raise RuntimeError("EOT not acknowledged")


def ezsp_launch_bootloader(path):
    import asyncio
    from bellows.ezsp import EZSP
    import zigpy.config

    async def run():
        ezsp = EZSP(zigpy.config.SCHEMA_DEVICE(
            {"path": path, "baudrate": 115200, "flow_control": None}))
        await ezsp.connect()
        try:
            await ezsp.startup_reset()
            await ezsp.launchStandaloneBootloader(1)  # 1 = normal mode; 0 does nothing
        finally:
            await ezsp.disconnect()

    asyncio.run(asyncio.wait_for(run(), 30))


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("gbl", help="firmware file (.gbl)")
    parser.add_argument("--port", default="/dev/ttyUSB0")
    parser.add_argument("--from", dest="source", required=True,
                        choices=["factory", "ezsp", "recovery", "bootloader"],
                        help="what the radio runs now (see above)")
    parser.add_argument("--allow-keep-nvm3", action="store_true",
                        help="allow a GBL without NVM3 erase when coming from factory firmware")
    args = parser.parse_args()

    image = open(args.gbl, "rb").read()
    wipes_nvm3 = check_gbl(image)
    if args.source == "factory" and not wipes_nvm3 and not args.allow_keep_nvm3:
        sys.exit("this GBL keeps the factory NVM3 data, which EmberZNet cannot use; "
                 "use the factory-migration GBL")
    if args.source != "factory" and wipes_nvm3:
        print("note: this GBL erases NVM3, including any existing Zigbee network",
              flush=True)
    started = time.monotonic()

    def log(msg):
        print(f"{time.monotonic() - started:7.2f}s {msg}", flush=True)

    if args.source == "ezsp":
        log("asking the EmberZNet firmware to start the bootloader")
        ezsp_launch_bootloader(args.port)
    port = Port(args.port)
    if args.source == "recovery":
        log("holding PA4 low through a radio reset")
        recovery_reset()
    elif args.source == "factory":
        log("pinging factory firmware")
        port.write(PING)
        if port.wait_frame(0x40, 0x00, 2, log) is None:
            sys.exit("no reply to ping; is the factory firmware running?")
        log("requesting bootloader")
        port.write(BTL_START_APP)
        if port.wait_frame(0x40, 0x06, 3, log) is None:
            sys.exit("factory firmware did not acknowledge bootloader request")

    log("waiting for bootloader ready event")
    if port.wait_frame(0x80, 0x0A, 5, log) is not None:
        port.write(ACK_READY)
        time.sleep(0.2)
    else:
        log("no ready event; pinging bootloader")
        port.write(PING)
        if port.wait_frame(0x40, 0x00, 2, log) is None:
            sys.exit("bootloader not responding")
    port.write(BTL_UPLOAD)
    reply = port.wait_frame(0x40, 0x07, 3, log)
    if reply != b"\x00":
        sys.exit(f"upload request rejected: {reply!r}")

    xmodem_send(port, image, log)
    result = port.wait_frame(0x80, 0x08, 20, log)
    port.write(ACK_DONE)
    if result != b"\x00":
        sys.exit(f"bootloader reported failure: {result!r}")
    log("upload accepted; radio is resetting into the new firmware")


if __name__ == "__main__":
    main()
