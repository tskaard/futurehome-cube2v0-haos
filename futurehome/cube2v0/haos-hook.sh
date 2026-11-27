#!/bin/bash
# shellcheck disable=SC2155

function haos_pre_image() {
    local BOOT_DATA="$(path_boot_dir)"

    cp "${BINARIES_DIR}/boot.scr" "${BOOT_DATA}/boot.scr"
    cp "${BINARIES_DIR}"/*.dtb "${BOOT_DATA}/"
    mkdir -p "${BOOT_DATA}/overlays"
    cp "${BINARIES_DIR}"/*.dtbo "${BOOT_DATA}/overlays/"

    cp "${BOARD_DIR}/boot-env.txt" "${BOOT_DATA}/haos-config.txt"
    cp "${BOARD_DIR}/cmdline.txt" "${BOOT_DATA}/cmdline.txt"

    cube_zigbee_firmware "${BOOT_DATA}"
}


# Put the onboard Zigbee firmware and installer on the boot partition for
# the opt-in cube-zigbee-firmware service. Files come from the GitHub
# release and must match the hashes pinned in zigbee-firmware.sha256.
function cube_zigbee_firmware() {
    local boot="$1"
    local release="zigbee-ncp-7.5.1.0-r1"
    local base="https://github.com/tskaard/futurehome-cube2v0-haos/releases/download/${release}"
    local cache="${BUILD_DIR}/cube-zigbee-${release}"
    local sums="${cache}/SHA256SUMS"
    local name

    mkdir -p "${cache}"
    grep -v '^#' "${BOARD_DIR}/zigbee-firmware.sha256" > "${sums}"
    for name in $(awk '{print $2}' "${sums}"); do
        [ -f "${cache}/${name}" ] || curl -fsSL -o "${cache}/${name}" "${base}/${name}"
    done
    (cd "${cache}" && sha256sum -c "${sums}")

    mkdir -p "${boot}/cube-zigbee"
    cp "${sums}" "${boot}/cube-zigbee/SHA256SUMS"
    for name in $(awk '{print $2}' "${sums}"); do
        cp "${cache}/${name}" "${boot}/cube-zigbee/"
    done

    # Optional build-time opt-in; otherwise create the file after install.
    if [ -f "${BOARD_DIR}/zigbee-install.txt" ]; then
        cp "${BOARD_DIR}/zigbee-install.txt" "${boot}/zigbee-install.txt"
    fi
}


function haos_post_image() {
    convert_disk_image_xz
}

