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
**inferred** from that binary's request framing. It sends no bootloader or
firmware commands. The version frame and the radio's required handshake have
not yet been confirmed against a working stock radio, so no response would
not establish that the radio is faulty. Review captured bytes before sharing
them publicly; a response could contain device-specific information.
