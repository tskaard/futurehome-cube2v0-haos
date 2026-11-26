# Onboard Zigbee work

The Cube's onboard EFR32MG12 is connected to a CP2102N USB-to-UART bridge,
which appears as `/dev/ttyUSB0` on the test installation. Its factory radio
application did not answer standard EZSP/ASH requests from ZHA. A copy of
Futurehome's original userspace adapter did communicate with the radio after
the Cube's Zigbee reset line was pulsed, and reported firmware 1.14.2. The
factory adapter then successfully updated the radio to its own 2.4.2
firmware through a serial bootloader.

A later experiment installed a generic EFR32MG12 Zigbee NCP image intended
for a different board. The radio has been silent over UART since then,
including after a complete power cycle. The likely causes include different
UART pins or other board-specific settings; the exact cause is **unproven**.
The Cube's USB developer connection does not expose the radio's SWD debug
interface. No reliable serial recovery sequence has yet been found for the
silent radio.

A second CUBE-2V0-EU gave us a working factory-radio reference. Before any
radio update, its onboard radio answered Futurehome ping and version requests
through the CP2102N and reported firmware **2.1.7**. The stock `zigbee-ad`
adapter then commanded the radio into its bootloader and transferred an
experimental Cube-specific NCP image over the same serial bridge. Its log
reported XMODEM transfer progress and update confirmation. The
`SoC image transferred rsp=Success` line is an outbound adapter message,
not a response from the new application. The new image did
not answer EZSP/ASH requests or the factory protocol, including after a cold
power cycle. **Do not flash that experimental image to another Cube.** The
successful transfer shows that the resident bootloader could communicate
through the CP2102N while the factory application was working; it does not
give us a way to enter the bootloader now that the application is silent.
Some Silicon Labs UART bootloaders require a separate menu command to run
after transfer. Offline disassembly of Futurehome's adapter shows that it
sends XMODEM EOT, receives its ACK and a Futurehome update-completion frame,
then sends no separate run command or hardware reset. This same adapter
sequence previously updated the first Cube to stock 2.4.2 firmware, and a
later full power cycle left the second Cube's experimental image silent.
The update-completion frame does not prove that image booted. Its GBL held
application data, not a bootloader replacement; serial reflashing remains
plausible if a working bootloader-entry method is found.

An experimental Cube-specific NCP has been compiled using a plausible
USART0 PD14/PD15 pin mapping, but that mapping, flow control, oscillator
settings, and RF configuration remain unverified. **It is not released as a
working firmware image and must not be used as an installation step.**

Offline disassembly of the unencrypted Futurehome 2.4.2 application image
found a startup serial configuration for USART0 at 115200 baud with TX and RX
route location **0** and no hardware flow-control route enabled. This differs
from the experimental NCP's photo-based location-22 setting. [Silicon Labs'
pin map](https://docs.silabs.com/mcu/5.6/efr32mg12/group-EFR32MG12P-AF-Pins)
maps location 0 to PA0/PA1 and location 22 to PD14/PD15. The code path
has been traced through its serial initializer, but we have not yet verified
on a working board that this is the CP2102N connection or ruled out later
route changes. The experimental image should not be flashed on this evidence
alone. The factory startup path declares 38.4 MHz and initializes the HFXO
with startup CTUNE 160. For steady-state CTUNE it reads a valid per-chip
calibration value when available, with 282 as its fallback. The actual value
on any individual Cube cannot be determined from this application image.
The image inspected here is version **2.4.2**; the second hub was running
**2.1.7** before its update. Both are for the same CUBE-2V0-EU hardware, so
that radio firmware version difference does not imply different physical UART
wiring. We lack a direct continuity measurement of the CP2102N traces, but
the factory route-location finding makes PA0/PA1 a strong lead. The flashed
Cube-specific image was generated with USART0 on PA0/PA1 at 115200 baud,
without hardware flow control, yet remained silent. Its failure may be in
startup or another configuration detail; the cause is not established.

Before HFXO setup, the factory startup path unconditionally calls Silicon
Labs' DC-DC initializer. Its settings structure is byte-for-byte identical to
the one in the flashed Cube-specific image: DC-DC to DVDD, low-noise mode,
1.8 V, 15 mA nominal EM0 load, 200 mA maximum, analog peripherals on the
DC-DC, 160 mA reverse-current threshold, and the 4.7 µF compensator setting.
The flashed image's stack and RAM use fit the 256 kB part. Its code ends
below its NVM3 region, which is at the same flash address (`0xF7000`) as the
factory image's.

## SWD findings (second Cube, 2026-11-27)

An ST-Link V2 clone (firmware V2J17, OpenOCD HLA mode) connected to the radio
through the SWD contacts described below, with the hub powered normally. The
chip identified as an EFR32MG12P433 and **is not debug-locked**. The silent
radio can therefore be read and reflashed through SWD. A read-only dump showed:

- the application area holds the flashed Cube-specific image byte for byte,
  so the serial update itself worked;
- a resident bootloader of about 14.5 kB at `0x0FE10000` with no text strings,
  so it is not Silicon Labs' menu-driven UART XMODEM bootloader.

Halting the CPU repeatedly found it at the same address every time. It sat
in `EMU_DCDCInit`, in the GSDK 4.5 DC-DC_E204 errata loop, which waits without
a timeout for the DC-DC "low-noise running" flag. EMU registers showed
low-noise mode requested (`DCDCCTRL = 0x31`), but the low-noise running flag
was clear. The NFET over-current-limit flag was set (`EMU_IF = 0x20060000`).
The image therefore hangs before it initializes the UART, which explains the
silence. The factory 2.4.2 image waits for the same flag with the same
settings structure and does start. The difference must lie in the DC-DC
register sequence of the newer SDK or in earlier startup state; it has not
been identified yet.

Writing the factory 2.4.2 application back through SWD restored the radio:
it answered the factory ping and reported version 2.4.2. Its live EMU DC-DC
configuration registers matched the hung image's, apart from undocumented
bits that appear to be status.

A rebuild with only `SL_DEVICE_INIT_DCDC_BYPASS: 1` added
(`cube2v0_zigbee_ncp_pa0_pa1_dcdcbypass.yaml`, PA0/PA1, 115200, no flow
control, CTUNE 282) got past DC-DC setup. It then looped while opening NVM3,
which still held the factory firmware's objects. After a backup, erasing the
NVM3 region (`0xF7000`–`0xFFFFF`) let it boot. The radio then answered an ASH
reset with `RSTACK` (`1a c1 02 0b 0a 52 7e`). Home Assistant's bellows 1.2.1
completed the EZSP handshake and reported **EZSP protocol version 13**
(EmberZNet 7.5.1). This is the first onboard-radio EZSP response on a Cube.
Network formation, device pairing, RF range and the bypass mode's effect on
power consumption remain untested. The working sequence currently needs SWD:
flash the application, and erase NVM3 when coming from factory firmware. The
image remains experimental and is not a supported installation step.

The available Futurehome GBL is an application update and contains no
bootloader image. The resident bootloader's UART and GPIO activation settings
cannot be recovered from that file. The factory application could invoke a
serial update while it was responsive; once our test radio became silent,
reset attempts with PA4 held both low and high produced no bootloader response.
These attempts do not rule out another recovery method. [Silicon Labs documents
separate bootloader pin configuration](https://docs.silabs.com/mcu-bootloader/3.2.2/bootloader-user-guide-gsdk-4/07-configuring-the-gecko-bootloader).
The older Futurehome `zigbee-selftest` tool also sends a command to the
running application to start its bootloader. The `red-bee` package is a Huawei
LTE modem controller, not a Zigbee recovery tool. Neither provides a verified
way to enter this bootloader when the radio application is silent.

Continuity measurements on an unpowered CUBE-2V0-EU have since mapped the
radio sub-board's (U9) castellated edge contacts to EFR32MG12 QFN48 pins.
Orient the board so the chip marking reads upright. On the edge away from
the CP2102N, the third contact from the top is pin 1 (PF0, SWCLK), the fourth
is pin 2 (PF1, SWDIO), and the eighth is pin 12 (RESETn). On the edge facing
the CP2102N, the second contact from the bottom is pin 25 (PA0) and the
third from the bottom is pin 26 (PA1). This matches the factory image's
USART0 location 0 and gives a physical SWD access point. The connection from
those PA0/PA1 contacts to the CP2102N, and PA4's contact, are not yet
measured.

Useful contributions would be a board schematic, a tested serial
bootloader-entry and recovery method, or SWD readout results. Do not infer
electrical connections from photos alone.

## Stock-radio serial probe

[`zigbee_serial_probe.py`](../zigbee_serial_probe.py) is a small Linux/Python 3
tool for checking a Cube that still has its factory Zigbee firmware. It uses
only the Python standard library. Stop any service using the CP2102N serial
port before running it, and substitute the correct device path if needed.

Start a passive capture before resetting the radio by the method you have
already used:

```sh
python3 zigbee_serial_probe.py --port /dev/ttyUSB0 --duration 15
```

The default mode opens the port for reading only. It does not reset the radio
or change its firmware. To request a reply, run the optional query mode:

```sh
python3 zigbee_serial_probe.py --port /dev/ttyUSB0 --query --duration 8
```

Query mode sends exactly two frames: the ping `aa 00 20 00 36`, captured from
Futurehome's `zigbee-ad` 3.8.4, and the version request `aa 00 20 02 34`,
originally inferred from that binary. Both received valid replies on a
working stock radio in [issue #1](https://github.com/tskaard/futurehome-cube2v0-haos/issues/1):

```text
TX ping:     aa 00 20 00 36
RX ACK:      aa 03 80 0d 00 00 00 c6
RX ping:     aa 01 40 00 04 11
TX version:  aa 00 20 02 34
RX ACK:      aa 03 80 0d 00 00 02 c4
RX version:  aa 09 40 02 00 02 04 01 0c 1f 06 09 02 c8
```

That contributor's stock radio reported version 1.12.31 and paired a sensor
using the factory protocol. Our test hub previously reported 1.14.2; the
reason for the difference is unknown. The contributor's probe sent no host
ACK for the two requests. Query mode sends no bootloader or firmware commands.
The factory protocol still needs a Home Assistant integration, or the radio
needs a verified compatible NCP firmware, before Home Assistant can use it as
a Zigbee coordinator. Review captured bytes before sharing them publicly; a
response could contain device-specific information.
