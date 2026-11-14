# Build the image

The source files in this repository reproduce the Cube target from a
successful local build. Build against Home Assistant OS commit
`c7acf719b948b192ee11dd296f0cdb331e33f0c0`. The board configuration
currently selects Linux 6.18.60, U-Boot 2026.04, and the Rockchip blobs
revision `b4558da0860ca48bf1a571dd33ccba580b9abe23`.

You need Git, Docker with permission to run containers, disk space for the
HAOS build and downloads, and a Linux host. HAOS's own
[build documentation](https://contributors.home-assistant.io/os/operating-system/build/)
describes the general build environment.

```sh
git clone https://github.com/home-assistant/operating-system.git ../haos
git -C ../haos checkout c7acf719b948b192ee11dd296f0cdb331e33f0c0
git -C ../haos submodule update --init --recursive

# Run from this repository's root:
cp -a futurehome ../haos/buildroot-external/board/
cp cube2v0_defconfig ../haos/buildroot-external/configs/
git -C ../haos apply "$PWD/patches/haos-data-partition.patch"

cd ../haos
scripts/enter.sh make cube2v0
```

Docker may need several hours and substantial download space on a first
build. The resulting compressed image should be
`../haos/output/images/haos_cube2v0-19.0.dev0.img.xz` relative to this
repository for
the pinned revision. Check that the build exits successfully before using
the image.

The patch keeps the data filesystem at 1280 MiB in the build image so HAOS
can expand it at first boot. It also accepts an `e2fsck` exit status of 1
when repairs were made. An earlier shrunk image had an invalid journal and
was rejected.

The build downloads upstream components, including Rockchip boot blobs.
Those binaries are **not** stored in this repository. See
[credits and licensing](credits.md) before redistributing a built image.
