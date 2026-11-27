# Onboard Zigbee work

## Status

- The onboard Zigbee radio **works experimentally** with ZHA on one hub,
  with a custom EmberZNet firmware.
- Installing HAOS does **not** change the radio. The radio has its own flash
  and keeps Futurehome's firmware until you replace it.
- An experimental firmware and a serial installer (no debugger needed) are
  published; see [Install over serial](#install-over-serial). This was
  tested on one hub only.
- The current experimental firmware includes a **PA4 recovery check**: the
  hub can force the radio into its bootloader, so a later bad image can be
  replaced over serial. This was tested on one hub.
- **Do not flash any other experimental image over serial.** An image without
  the recovery check that hangs at startup can only be recovered with SWD.
- The factory radio firmware speaks Futurehome's own serial protocol, not
  EZSP, so ZHA cannot use it.

## Hardware

- Radio: EFR32MG12P433F1024GM48 (marking MG12P433JG) on a castellated
  sub-board, U9.
- Serial bridge: the radio's UART goes through a CP2102N (U11) USB-UART
  bridge on the Cube's internal USB hub. It appears as `/dev/ttyUSB0`.
- Host control: the RK3328 drives radio power enable (GPIO1_A5), nRESET
  (GPIO1_A0, Linux GPIO 32) and PA4 (GPIO1_A3 via R154, Linux GPIO 35). The
  device tree leaves PA4 as an input without pull.
- Debug lock is not set on the tested radio.

### Edge contact map

Continuity measurements on an unpowered CUBE-2V0-EU mapped the sub-board's
edge contacts to EFR32MG12 QFN48 pins. Orient the board so the chip marking
reads upright.

- Edge away from the CP2102N, counting from the top: 3rd contact = pin 1
  (PF0, SWCLK); 4th = pin 2 (PF1, SWDIO); 8th = pin 12 (RESETn).
- Edge facing the CP2102N, counting from the bottom: 2nd contact = pin 25
  (PA0); 3rd = pin 26 (PA1).
- PA0/PA1 are USART0 location 0, which matches the factory firmware
  ([Silicon Labs pin map](https://docs.silabs.com/mcu/5.6/efr32mg12/group-EFR32MG12P-AF-Pins)).
- The 3 copper pads on a short side go to the antenna matching network.
  They are RF, not SWD.

## Factory firmware and bootloader

Both were confirmed by disassembling an SWD dump.

### Application

- The factory radio app speaks Futurehome's own framed serial protocol, not
  EZSP. Frames are `AA len type cmd payload checksum`; the checksum makes the
  whole frame, including the leading `AA`, sum to zero modulo 256. See the
  probe section below for examples.
- It uses USART0 on PA0/PA1 at 115200 baud, no flow control.
- Its startup declares a 38.4 MHz HFXO with startup CTUNE 160. Steady-state
  CTUNE comes from per-chip calibration, with 282 as fallback.
- Radio firmware versions seen on CUBE-2V0-EU hubs differ: 2.1.7 on the
  second hub, 1.14.2 on the first (later updated to 2.4.2), and 1.12.31 on a
  contributor's hub. The version does not imply different UART wiring.
- Command `aa 00 20 06 30` makes it enter the bootloader.

### Bootloader

- Silicon Labs Gecko Bootloader 1.7.0 (first stage `0x0FE10000`, main stage
  `0x0FE10800`) with a Futurehome UART front end on USART0 PA0/PA1, 115200
  8N1, no flow control.
- It is entered only by a software reset with the standard Gecko
  reset-reason word (0xF00F, BOOTLOAD 0x0202) in RAM, or when the
  application is structurally invalid.
- There is **no GPIO activation pin and no boot-time window** in the
  bootloader itself. An application that hangs during startup can only be
  recovered over serial if the application provides its own early check (see
  [PA4 recovery check](#pa4-recovery-check)).
- EmberZNet NCP's EZSP `launchStandaloneBootloader` also enters it, but only
  with mode 1 (normal); mode 0 is accepted and does nothing.
- It accepts GBL program data anywhere from 0x0 to 0x100000, erasing 2 KiB
  pages before writing. Signatures are not enforced.

Serial protocol (tested end to end on one hub):

1. From the factory app, the host sends `aa 00 20 06 30`; the app replies
   `aa 01 40 06 00 0f` and resets into the bootloader.
2. Bootloader announces "btl ready": `aa 01 80 0a 00 cb`. Host acknowledges
   with `aa 01 40 0a 00 0b`.
3. Host starts upload: `aa 00 20 07 2f`. Transfer is XMODEM-CRC with
   128-byte blocks.
4. On completion the bootloader sends `aa 01 80 08 00 cd`. Host acks with
   `aa 01 40 08 00 0d`. The radio then resets into the new application.

A 274 kB GBL took about 47 seconds. Program data in the GBL may target the
NVM3 area: a second program tag at `0xF7000` with `0x9000` bytes of `0xFF`
(and a recomputed END-tag CRC32) erased the factory firmware's NVM3 data in
the same upload, which the EmberZNet firmware needs (see below).

## Why earlier attempts failed

Two root causes were **confirmed over SWD** on the second hub.

1. **DC-DC startup hang.** The GSDK 4.5 image hung forever in
   `EMU_DCDCInit`, in the DC-DC errata E204 loop that waits for the
   low-noise "running" flag. This happens before UART init, so the radio was
   silent. Requesting low-noise mode on this board sets the NFET
   over-current flag and the converter drops to low-power mode instead.
   The factory firmware runs the same sequence and waits for the same flag.
   It also hung once it started from a state where low-noise mode was not
   already requested. It appeared to work otherwise only because its mode
   setter returns early when low-noise mode is already set. `DCDCCTRL`
   survives both software and pin resets; only a power cut clears it.
   Adding the factory firmware's extra errata write (`EMU+0x1A4 |= 0x7C00`)
   did not help. A test build with a bounded wait timed out and fell back to
   bypass after both a software reset and a pin reset. Whether low-noise mode
   ever starts after a true power-on reset is untested. Fix used: build with
   `SL_DEVICE_INIT_DCDC_BYPASS: 1`, at the cost of somewhat higher power use
   on a mains-powered hub.
2. **NVM3 loop.** With DC-DC bypass, the image looped while opening NVM3.
   The factory firmware had nearly filled the same NVM3 area
   (`0xF7000`-`0xFFFFF`, same format). Erasing it fixed the boot. The
   likely cause is no free space for EmberZNet tokens; this is inferred.

What happened on the hubs:

- Hub 1: a generic TubeZB MGM12P EZSP image built for another board was
  installed with Futurehome's updater. The radio went silent.
- Hub 2: a Cube-specific GSDK 4.5 / EmberZNet 7.5.1 NCP image (PA0/PA1,
  115200, no flow control, CTUNE 282) installed the same way also went
  silent.
- Serial-only bootloader-entry probes found nothing. This is explained by
  the bootloader having no pin activation.
- An earlier image guessed PD14/PD15 from photos. The guess was wrong and
  that image was never flashed.

## Install over serial

**Experimental, tested on one hub.** This replaces Futurehome's radio
firmware. Returning to the factory radio firmware has not been tested.

Do this after HAOS is installed and onboarded, and before adding ZHA. You
need a root shell on the HAOS host, where the `ha` and `docker` commands
work. The add-on terminals do not give this by default. One way is the
developer SSH access on port 22222: put your public key in a file named
`authorized_keys` on a USB stick labelled `CONFIG`, import it under
**Settings → System → Hardware → ⋮ → Import from USB** (or reboot with the
stick attached), then run `ssh root@homeassistant.local -p 22222`. See
[Debugging the Home Assistant Operating System](https://developers.home-assistant.io/docs/operating-system/debugging/).

Release files (GitHub release `zigbee-ncp-7.5.1.0-r1`):

- `zigbee_install.py`: the installer (Python standard library; recovery mode
  also uses `gpiod`, which the Home Assistant image includes).
- `cube2v0-zigbee-ncp-7.5.1.0-r1-factory-migration.gbl`: first install from
  the factory firmware. It also erases the factory NVM3 data.
- `cube2v0-zigbee-ncp-7.5.1.0-r1.gbl`: later updates; keeps the Zigbee network.
- `SHA256SUMS`.

First install, from the host shell:

```sh
mkdir -p /mnt/data/cube-zigbee && cd /mnt/data/cube-zigbee
base=https://github.com/tskaard/futurehome-cube2v0-haos/releases/download/zigbee-ncp-7.5.1.0-r1
for f in zigbee_install.py cube2v0-zigbee-ncp-7.5.1.0-r1-factory-migration.gbl \
         cube2v0-zigbee-ncp-7.5.1.0-r1.gbl SHA256SUMS; do curl -fLO "$base/$f"; done
sha256sum -c SHA256SUMS
ha core stop
image=$(docker inspect -f '{{.Config.Image}}' homeassistant)
docker run --rm -v /mnt/data/cube-zigbee:/w --device /dev/ttyUSB0 \
  --entrypoint python3 "$image" /w/zigbee_install.py --from factory \
  /w/cube2v0-zigbee-ncp-7.5.1.0-r1-factory-migration.gbl
ha core start
```

The upload takes about a minute. The installer stops before writing anything
if the factory firmware does not answer. Then add the **Zigbee Home
Automation** integration with serial port `/dev/ttyUSB0`, radio type EZSP,
115200 baud and no flow control.

Later updates, with Home Assistant Core stopped, use `--from ezsp` and the
non-migration file. If the firmware stops answering, use `--from recovery`
and add `--device /dev/gpiochip1` to the `docker run` command. This holds
PA4 low through a radio reset (see [PA4 recovery check](#pa4-recovery-check)).

Test coverage on the development hub:

- `--from factory` was tested with an otherwise identical build without the
  recovery check.
- `--from ezsp` and `--from recovery` were tested with this release.
- In each case the radio then answered EZSP, and ZHA worked after the update.

### Automatic install from the HAOS image (opt-in)

Images built from this repository put the same release files on the boot
partition (folder `cube-zigbee/`) and include a service,
`cube-zigbee-firmware`, that can install them at boot without a host shell.
It does nothing unless a file named `zigbee-install.txt` exists at the root
of the boot partition. Create it in one of these ways:

- before building: `touch futurehome/cube2v0/zigbee-install.txt` in this
  repository, before copying the board files into the HAOS tree;
- after installing, from the host shell: `touch /mnt/boot/zigbee-install.txt`,
  then reboot.

When enabled, the service runs at every boot, before the Supervisor starts,
so nothing else uses the serial port:

- Factory radio firmware: installs the migration file. This takes about a
  minute and delays Home Assistant's start once.
- Bundled firmware already installed by the service: does nothing and does
  not touch the radio.
- Older firmware installed by the service: updates it through the PA4
  recovery check, keeping the Zigbee network.
- Anything else, for example firmware installed by hand: leaves the radio
  alone and remembers that. Delete `/mnt/data/cube-zigbee-autoinstall` to
  make it check again.
- An interrupted install is retried on the next boot.

Afterwards add ZHA as described above. The service logs to the host journal:
**Settings → System → Logs → Host**, or `journalctl -u cube-zigbee-firmware`
from the host shell.

Test status on the development hub: the image builds with the service
enabled and the files on the boot partition. The service script, run by hand
on the hub, correctly:

- left hand-installed firmware alone;
- finished an interrupted first install from the bootloader;
- did nothing when the bundled firmware was already installed;
- updated through PA4.

ZHA worked afterwards. **Not yet tested:** a migration from factory firmware
by the service itself, and a real first boot of the image with the service
running under systemd.

## Current experimental firmware and SWD procedure

With the DC-DC bypass build flashed over SWD and NVM3 erased:

- the radio answers EZSP (bellows 1.2.1, EZSP protocol 13, EmberZNet 7.5.1);
- ZHA formed a network on `/dev/ttyUSB0` (EZSP, 115200, no flow control);
- a Zigbee light bulb paired and was controlled.

**Untested:** RF range, larger networks, long-term stability, and the power
impact of DC-DC bypass. Build inputs are in
[`zigbee-firmware/`](../zigbee-firmware/).

### PA4 recovery check

The experimental firmware adds a check at the very start of `SystemInit()`,
before C runtime setup and before any clock, DC-DC or radio code. It enables
the internal pull-up on PA4 and reads the pin. If PA4 is low, it writes the
standard Gecko bootloader request (`0xF00F0202`) to the start of RAM and
resets, so the radio enters its bootloader. Normally the hub leaves PA4
undriven and the firmware boots as usual.

To enter the bootloader from the hub (tested on one hub, with Home Assistant
Core stopped so nothing holds the serial port):

```sh
echo 35 > /sys/class/gpio/export 2>/dev/null; echo 32 > /sys/class/gpio/export 2>/dev/null
echo low > /sys/class/gpio/gpio35/direction    # hold PA4 low
echo low > /sys/class/gpio/gpio32/direction    # radio reset
sleep 0.2
echo in > /sys/class/gpio/gpio32/direction     # release reset
sleep 0.3
echo in > /sys/class/gpio/gpio35/direction     # release PA4
```

The bootloader then announces `aa 01 80 0a 00 cb` and answers the ping
`aa 00 20 00 36` with `aa 01 40 00 98 7d`. An upload can follow, or the
command `aa 00 20 09 2d` starts the installed application again. Release PA4
before the upload finishes; otherwise the new application jumps straight
back into the bootloader. Only firmware that contains this check can be
recovered this way.

### SWD procedure (for people with a debugger)

This worked on the second hub. Flashing can brick the radio's serial path;
SWD can always recover it.

- Probe: an ST-Link V2 clone (firmware V2J17), so OpenOCD runs in HLA mode:
  `-f interface/stlink-hla.cfg -f target/efm32.cfg`, adapter speed about
  1000 kHz, `reset_config none`.
- Wiring: SWCLK, SWDIO and GND only. Do **not** connect the probe's 3.3 V.
  Power the hub normally.
- Read first, before writing anything. Use `dump_image` for 0x0 (1 MiB),
  0x0FE10000 (32 KiB bootloader), 0x0FE04000 (lock bits) and 0x0FE00000
  (user data).
- Flash after `reset halt`. Flashing while an application ran failed with
  `corrupted fifo read pointer`. If `reset halt` times out, an erased first
  page leaves the radio idling in its bootloader, where a plain `halt` and
  flash work.
  Use `flash write_image erase <app.bin> 0x0 bin`, then `verify_image`.
- When coming from factory firmware, erase NVM3 with
  `flash erase_address 0xF7000 0x9000`.
- Writing the factory application back over SWD restored a radio running
  the factory image.

**Privacy warning:** on a working EmberZNet radio the NVM3 area holds the
Zigbee network key. Back it up, and do not share dumps publicly.

## Open work

- Optional: test whether DC-DC low-noise mode starts after a true power-on
  reset; bypass works and is the current choice.
- Tests on more hubs, including a first install from the factory firmware
  with this release.
- Recover hub 1, which still holds the silent generic image.
- RF, range and stability tests.

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
using the factory protocol. The contributor's probe sent no host ACK for the
two requests. Query mode sends no bootloader or firmware commands.
The factory protocol still needs a Home Assistant integration, or the radio
needs a verified compatible NCP firmware, before Home Assistant can use it as
a Zigbee coordinator. Review captured bytes before sharing them publicly; a
response could contain device-specific information.

## How to help

- Test reports and questions are welcome in the
  [Zigbee hardware issue](https://github.com/tskaard/futurehome-cube2v0-haos/issues/1).
- Owners of an SWD debug probe can help most: read-only dumps, contact-map
  checks and range tests on other hubs.
- A board schematic would also help.
- Do not post shipping addresses or serial labels publicly. Review captured
  bytes and dumps before sharing them.
