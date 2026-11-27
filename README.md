# Home Assistant OS for Futurehome Cube 2v0

An **unofficial, experimental** Home Assistant OS (HAOS) port for the
**Futurehome Smarthub II, model CUBE-2V0-EU**. This repository contains the
Cube-specific source files and instructions needed to build the image. It is
independent of Futurehome and the Home Assistant project.

This repository currently contains **source and instructions only**. There
is no published installation image or tested automatic OS update feed yet.

## Current status

| Feature | Status |
| --- | --- |
| HAOS boot and Home Assistant onboarding | HAOS boot tested on two CUBE-2V0-EU hubs; onboarding tested on one |
| Ethernet and USB | Working on the test hub |
| Onboard Z-Wave | Z-Wave JS connects on `/dev/ttyS1`; a Popp & Co wall plug was paired, reported alive, and responded to on/off control |
| Onboard Zigbee | **Experimental**: works with ZHA on one hub after an SWD-flashed custom firmware; no end-user install path yet, see [Zigbee findings](docs/zigbee.md) |
| External USB Zigbee adapter | Possible USB option, not tested as part of this port |
| OS updates | Official HAOS OS updates are unavailable for this custom board |

The Cube has 8 GB of internal eMMC. On the test hub, Home Assistant's data
partition had only about 1.3 GB free after first boot and Supervisor blocked
installation of the Z-Wave JS app. Moving the data disk to a 64 GB USB drive
allowed the app to install. **Plan on a separate USB data drive for this
version.** The data-disk move erases the selected drive.

## Help with onboard Zigbee

The onboard Zigbee radio now works with ZHA on one development hub. A
Cube-specific EmberZNet firmware was flashed through the radio's SWD debug
contacts; ZHA formed a network and a light bulb paired and responded.
A serial install that needs no debugger has also worked on that hub, from
the factory radio firmware. The installer and firmware are not published
yet, so this is **not** an installation step. See the [onboard Zigbee findings](docs/zigbee.md)
for details and the radio contact map. Please do not flash any experimental
Zigbee image over serial: earlier attempts left two radios silent, and a
bad image cannot be recovered over serial. Questions and test reports are welcome in the
[Zigbee hardware issue](https://github.com/tskaard/futurehome-cube2v0-haos/issues/1).
Do not post shipping addresses or serial labels publicly.

## Start here

1. Read [requirements and limitations](docs/status.md).
2. [Build the image](docs/build.md) from the pinned HAOS revision.
3. [Install it on the Cube](docs/install.md), then move the data disk to USB.
4. Select `/dev/ttyS1` when configuring the Z-Wave JS app.

Installing an image overwrites the Cube's internal eMMC. The original
Futurehome installation will be lost. Our original RockUSB backup was only
valid for its first 32 MiB and **cannot** restore the factory installation.
Make your own recovery plan before flashing.

The detailed private development log is kept separately from these
installation instructions. The build in this repository has been run
successfully once; HAOS booted on two hubs, and installation, onboarding,
and basic Z-Wave device control were tested on one hub.

## Project layout

- `futurehome/cube2v0/`: Cube board files, boot script, kernel device tree,
  and radio power overlays, copied by the build instructions into HAOS.
- `cube2v0_defconfig`: HAOS Buildroot target configuration.
- `patches/haos-data-partition.patch`: change needed to build a valid data
  filesystem on this small eMMC target.
- `docs/`: status, build, installation, and attribution.

No device backups, user data, secret keys, factory firmware packages, or
Rockchip binary blobs are included.

## Credits and licenses

The hardware description and boot-mode work build on
[RockPaperPencil's Cube board support](https://github.com/RockPaperPencil/futurehome-cube2v0eu-boardsupport)
and [unofficial Armbian port](https://github.com/RockPaperPencil/futurehome-cube2v0eu-armbian-unofficial).
This port is based on [Home Assistant OS](https://github.com/home-assistant/operating-system).
See [credits and licensing](docs/credits.md) for details.

The root Apache 2.0 license covers the original material in this repository.
Some Cube board files contain upstream material with different SPDX headers;
see [the file-level license map](LICENSES.md) before reusing them.

Futurehome, Home Assistant, and Z-Wave are trademarks of their respective
owners. This project is community maintained and is not an official image.
