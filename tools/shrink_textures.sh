#!/usr/bin/env bash
# Downscale a kit's textures in place. Blender exports whatever the kit shipped,
# which for the village kit is 2K — far more than scenery 40 m away behind glass
# needs, and the largest thing in the project.
#
#   ./tools/shrink_textures.sh village 1024
set -euo pipefail
cd "$(dirname "$0")/.."
KIT="${1:-village}"
SIZE="${2:-1024}"
DIR="app/Packages/RealityKitContent/Sources/RealityKitContent/RealityKitContent.rkassets/$KIT/textures"
[ -d "$DIR" ] || { echo "no such kit: $DIR"; exit 1; }

before=$(du -sk "$DIR" | cut -f1)
for f in "$DIR"/*.png "$DIR"/*.jpg; do
  [ -f "$f" ] || continue
  w=$(sips -g pixelWidth "$f" 2>/dev/null | awk '/pixelWidth/{print $2}')
  [ -n "$w" ] && [ "$w" -gt "$SIZE" ] || continue
  sips -Z "$SIZE" "$f" --out "$f" >/dev/null 2>&1
done
after=$(du -sk "$DIR" | cut -f1)
echo "$KIT textures: ${before}K -> ${after}K at ${SIZE}px"
