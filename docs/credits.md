# Credits and licensing

This project builds on several independent projects:

- [RockPaperPencil's Cube board-support repository](https://github.com/RockPaperPencil/futurehome-cube2v0eu-boardsupport)
  supplied the Cube device tree, U-Boot hardware description, and boot-mode
  script used as the basis of the Cube target. The device-tree files carry
  `GPL-2.0+ OR MIT` identifiers; the borrowed boot-mode script carries
  `GPL-2.0+`. These identifiers remain in the source files here.
- [RockPaperPencil's unofficial Armbian port](https://github.com/RockPaperPencil/futurehome-cube2v0eu-armbian-unofficial)
  supplied additional hardware and boot-path reference material.
- [Home Assistant Operating System](https://github.com/home-assistant/operating-system)
  supplies the upstream OS and Buildroot integration. This repository
  provides Cube-specific files and a patch for that source tree.
- [Rockchip rkdeveloptool](https://github.com/rockchip-linux/rkdeveloptool)
  provides the developer-mode flashing utility.

Original project documentation and newly written integration code are
offered under Apache License 2.0. Files with their own SPDX headers retain
the licenses stated in those headers. The included HAOS patch modifies
upstream files and remains subject to their upstream license. The license
for the source content does not grant rights to Futurehome trademarks or
third-party binary firmware.

No factory firmware, Rockchip boot blobs, Silicon Labs SDK files, device
backups, or personal configuration are distributed in this repository.
Before distributing a complete OS image, review the licenses and
redistribution terms of all included components.
