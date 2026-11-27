# File-level licenses

The root [LICENSE](LICENSE) is Apache 2.0 for original documentation and
integration work in this repository. It does **not** replace the license
headers on files adapted from other projects.

| Files | License and origin |
| --- | --- |
| `README.md`, `docs/`, `cube2v0_defconfig`, and Cube integration files without another SPDX header | Apache-2.0, original work in this project |
| `futurehome/cube2v0/uboot-boot.ush` | GPL-2.0-or-later portion based on [RockPaperPencil's boot-mode script](https://github.com/RockPaperPencil/futurehome-cube2v0eu-boardsupport) |
| `futurehome/cube2v0/kernel-dts/rockchip/*.dts`, `*.dtso` | GPL-2.0-or-later OR MIT, as declared in the files; main DTS based on [RockPaperPencil's board support](https://github.com/RockPaperPencil/futurehome-cube2v0eu-boardsupport) |
| `futurehome/cube2v0/patches/uboot/*.patch` | Contains additions adapted from the same board support; embedded files retain their individual SPDX headers, including GPL-2.0-or-later and GPL-2.0-or-later OR MIT |
| `patches/haos-data-partition.patch` | Modifies [Home Assistant OS](https://github.com/home-assistant/operating-system) source; subject to that project's Apache-2.0 license |
| `zigbee_install.py`, `zigbee_serial_probe.py`, `zigbee-firmware/gbl_add_nvm3_wipe.py`, `zigbee-firmware/README.md` | Apache-2.0, original work in this project |
| `zigbee-firmware/cube2v0_recovery_pin.patch` | Modifies Silicon Labs Gecko SDK `system_efr32mg12p.c`; subject to that file's Zlib license |
| `zigbee-firmware/cube2v0_zigbee_ncp.yaml` | Apache-2.0; a manifest for Nabu Casa's [silabs-firmware-builder](https://github.com/NabuCasa/silabs-firmware-builder) (Apache-2.0) |

The root license covers this repository's source and documentation, subject
to those file-level exceptions. It does not grant rights to third-party
trademarks, proprietary factory firmware, or binary blobs downloaded when
building a full OS image. Zigbee firmware files attached to GitHub releases
are built from the Silicon Labs Gecko SDK and EmberZNet and are subject to
Silicon Labs' license terms for those components. Images built from this
repository include those files on the boot partition.
