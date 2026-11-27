#!/usr/bin/env python3
"""Add an NVM3-wipe program tag to a Gecko Bootloader v3 (GBL) file.

The Cube radio bootloader erases each 2 KiB flash page before programming it.
A program tag at 0xF7000 holding 0x9000 bytes of 0xFF therefore erases the
whole NVM3 area that the factory firmware filled. The END tag CRC32 is
recomputed. Input and output are files; nothing is sent to a device.
"""

import argparse
import struct
import zlib

TAG_PROG = 0xFD0303FD
TAG_END = 0xFC0404FC
NVM3_START = 0xF7000
NVM3_SIZE = 0x9000


def tags(blob):
    offset = 0
    while offset + 8 <= len(blob):
        tag, length = struct.unpack_from("<II", blob, offset)
        yield offset, tag, blob[offset:offset + 8 + length]
        offset += 8 + length
        if tag == TAG_END:
            return
    raise ValueError("no END tag")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input")
    parser.add_argument("output")
    args = parser.parse_args()

    blob = open(args.input, "rb").read()
    out = bytearray()
    inserted = False
    for _, tag, raw in tags(blob):
        if tag == TAG_END:
            break
        if tag == TAG_PROG:
            start = struct.unpack_from("<I", raw, 8)[0]
            end = start + len(raw) - 12
            if end > NVM3_START:
                raise ValueError("application overlaps NVM3")
        out += raw
        if tag == TAG_PROG and not inserted:
            payload = struct.pack("<I", NVM3_START) + b"\xff" * NVM3_SIZE
            out += struct.pack("<II", TAG_PROG, len(payload)) + payload
            inserted = True
    if not inserted:
        raise ValueError("no program tag found")
    out += struct.pack("<II", TAG_END, 4)
    out += struct.pack("<I", zlib.crc32(bytes(out)))
    open(args.output, "wb").write(out)
    print(f"wrote {args.output}: {len(out)} bytes")


if __name__ == "__main__":
    main()
