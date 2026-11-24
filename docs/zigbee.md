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

The available Futurehome GBL is an application update and contains no
bootloader image. The resident bootloader's UART and GPIO activation settings
cannot be recovered from that file. The factory application could invoke a
serial update while it was responsive; once our test radio became silent,
reset attempts with PA4 held both low and high produced no bootloader response.
These attempts do not rule out another recovery method. [Silicon Labs documents
separate bootloader pin configuration](https://docs.silabs.com/mcu-bootloader/3.2.2/bootloader-user-guide-gsdk-4/07-configuring-the-gecko-bootloader).

Useful contributions would be a board schematic, continuity measurements
of the radio UART and SWD signals, or a tested serial bootloader-entry and
recovery method. The EFR32MG12 uses PF0 for SWCLK and PF1 for SWDIO, but
their locations on the Cube's module edge are not yet mapped. Do not infer
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
