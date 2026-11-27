# Requirements and limitations

## Hardware

Use a **CUBE-2V0-EU** Futurehome Smarthub II. The test device has an RK3328,
2 GB RAM, 8 GB eMMC, onboard Z-Wave and Zigbee radios, Ethernet, USB-A, and
a USB-C developer connection. Other Cube models have not been tested.

The built-in Z-Wave controller is exposed at `/dev/ttyS1`. Z-Wave JS reached
`Ready` after the controller's old network was reset on the test hub. On
2026-11-14, a Popp & Co 05438 wall plug was paired. Home Assistant showed
the node as alive and recorded on/off changes while the plug was controlled.
This verifies basic inclusion and switching on one device; energy metering,
secure inclusion, and a larger network remain untested. Resetting a Z-Wave
network discards its node associations. Keep a controller backup if you need
to preserve an existing network.

The built-in Zigbee radio is **experimental**. Its factory firmware speaks
Futurehome's own serial protocol, which ZHA cannot use. A Cube-specific
EmberZNet firmware works with ZHA on one test hub: a network formed and a
light bulb paired. On that hub it was installed both through the radio's SWD
contacts and over the serial port without a debugger. The installer and
firmware are published as an experimental option, separate from the main
installation; see [Install over serial](zigbee.md#install-over-serial). A
separate supported USB Zigbee coordinator is the conservative choice; that
option has
not been validated on this Cube.

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
