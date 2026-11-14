# Requirements and limitations

## Hardware

Use a **CUBE-2V0-EU** Futurehome Smarthub II. The test device has an RK3328,
2 GB RAM, 8 GB eMMC, onboard Z-Wave and Zigbee radios, Ethernet, USB-A, and
a USB-C developer connection. Other Cube models have not been tested.

The built-in Z-Wave controller is exposed at `/dev/ttyS1`. Z-Wave JS reached
`Ready` after the controller's old network was reset on the test hub. This
proves communication with the controller; pairing a new device is still
untested. Resetting a Z-Wave network discards its node associations. Keep a
controller backup if you need to preserve an existing network.

The built-in Zigbee radio is **not usable with ZHA in this version**. The
factory radio application spoke Futurehome's serial protocol. An
experimental firmware flash left the test radio silent. The Cube-specific
firmware experiment remains unverified and is not part of installation.
Use a separate supported USB Zigbee coordinator if you need Zigbee now;
that option has not been validated on this Cube.

## Storage and updates

The internal 8 GB eMMC held the OS, but only 1.3 GB remained free on the data
partition after first boot. Supervisor blocked installing the Z-Wave JS app.
On the test hub, moving the data disk to a 64 GB USB drive succeeded and
the app then installed. A USB hub may be needed if you also attach a USB
Zigbee coordinator. USB hub and coordinator combinations have not yet been
tested.

The Cube target has no official HAOS update feed. The test installation
reported `Board 'cube2v0' not found in version file. No OS updates.`
Home Assistant Core and apps may still update separately, but this project
does not yet provide a tested OS upgrade process. Keep a Home Assistant
backup before replacing an OS image.

The build uses the upstream `qemuarm-64` Supervisor machine as an
experimental compatibility choice. Do not treat this as official Home
Assistant board support. Reboot and recovery-mode reliability have not been
fully tested.
