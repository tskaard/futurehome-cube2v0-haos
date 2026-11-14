# Install on the Cube

These steps overwrite the Cube's internal eMMC. They have been exercised on
one CUBE-2V0-EU only. Confirm the exact model and understand the
[limitations](status.md) first.

## Prepare the image and tools

Build the image using [the pinned source](build.md). From the Cube repository
root, test the compressed file and decompress a working copy:

```sh
xz --test ../haos/output/images/haos_cube2v0-19.0.dev0.img.xz
xz -dk ../haos/output/images/haos_cube2v0-19.0.dev0.img.xz
sha256sum ../haos/output/images/haos_cube2v0-19.0.dev0.img
```

For the first successful build, the **raw** image SHA-256 was
`9c65472a62334aeea6ec989046c6a2935af8e1089d71853cff1abd9a87b17c7c`.
Rebuilds may differ; record your own hash and do not use this hash as a
universal release checksum.

Build or install [Rockchip's rkdeveloptool](https://github.com/rockchip-linux/rkdeveloptool).
Use the Cube's USB-C developer connection to enter Rockchip Loader mode;
[RockPaperPencil's board-support guide](https://github.com/RockPaperPencil/futurehome-cube2v0eu-boardsupport)
describes the Cube boot modes. Check that `rkdeveloptool ld` identifies
exactly the Cube before writing.

## Write and verify

With the Cube in Loader mode, write the raw image to eMMC starting at LBA 0:

```sh
rkdeveloptool ld
rkdeveloptool wl 0 ../haos/output/images/haos_cube2v0-19.0.dev0.img
```

The write command overwrites the factory partitions. A successful exit
alone is not a full verification. On our Cube, RockUSB reads beyond 32 MiB
returned `0xCC` filler even though the write succeeded. A later USB mass
storage (UMS) read matched all read-only image regions. If you can enter
the Cube's UMS mode, compare those regions before relying on the install;
do not interpret a RockUSB `rl` readback as a full eMMC backup or proof of
failure.

Disconnect the developer cable, connect Ethernet, and power the Cube
normally. First boot downloads Home Assistant Core and can take 20 minutes
or more. Find `homeassistant.local` on your network, or check your router
for the Cube's IP address. Complete Home Assistant onboarding in the
browser.

## Move the data disk and start Z-Wave

Attach a spare USB drive **larger than the internal 8 GB eMMC**. In Home
Assistant, open **Settings → System → Storage → Move data disk** and select
the USB drive. This erases the chosen drive and reboots the Cube. Keep power
connected and leave the drive attached afterward.

Install the **Z-Wave JS** app, select `/dev/ttyS1` as its serial device,
and set the radio region appropriate for your country. The test controller
connected and reached `Ready`. A new device inclusion remains to be
tested. If the controller contains an existing network, back it up before
resetting or replacing anything.
