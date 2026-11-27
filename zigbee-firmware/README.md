# Cube 2v0 Zigbee firmware build inputs

These files rebuild the experimental onboard Zigbee firmware described in
[docs/zigbee.md](../docs/zigbee.md). Prebuilt files are attached to the
project's GitHub releases.

- `cube2v0_zigbee_ncp.yaml`: build manifest for Nabu Casa's
  [silabs-firmware-builder](https://github.com/NabuCasa/silabs-firmware-builder)
  (Gecko SDK 4.5.0, EmberZNet 7.5.1). It was built at builder commit
  `b4e494e` with the container
  `ghcr.io/nabucasa/silabs-firmware-builder:9b8cbea737098b91`.
- `cube2v0_recovery_pin.patch`: Gecko SDK patch that adds the PA4 bootloader
  recovery check to `SystemInit()`.
- `gbl_add_nvm3_wipe.py`: turns a GBL into the factory-migration variant,
  which also erases the NVM3 area at `0xF7000`-`0xFFFFF`.

To build, check out the builder at that commit. Copy the manifest into its
`manifests/` directory and the patch into `src/zigbee_ncp/sdk_patches/`. Then
run:

```sh
mkdir -p artifacts
docker run --rm -v "$PWD:/repo" \
  ghcr.io/nabucasa/silabs-firmware-builder:9b8cbea737098b91 \
  --manifest manifests/cube2v0_zigbee_ncp.yaml \
  --output gbl --output-dir artifacts
python3 gbl_add_nvm3_wipe.py artifacts/cube2v0-zigbee-ncp-7.5.1.0.gbl \
  artifacts/cube2v0-zigbee-ncp-7.5.1.0-factory-migration.gbl
```

Rebuilt files will not be byte-identical to the release files, because
build paths and timestamps differ.
