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

The root license covers this repository's source and documentation, subject
to those file-level exceptions. It does not grant rights to third-party
trademarks, proprietary factory firmware, or binary blobs downloaded when
building a full OS image.
