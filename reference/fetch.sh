#!/usr/bin/env bash
# Downloads the Phase 1 reference material. Everything here is regenerable, so the
# binaries are gitignored and this script is the record of where they came from.
set -euo pipefail
cd "$(dirname "$0")"

echo "==> Apple sample projects (~1 GB)"
mkdir -p apple-samples/diorama apple-samples/hello-world
if [ ! -e apple-samples/diorama/README.md ]; then
  curl -L --fail -o /tmp/Diorama.zip https://docs-assets.developer.apple.com/published/f60567d1cc7d/Diorama.zip
  unzip -q -o /tmp/Diorama.zip -d apple-samples/diorama && rm -f /tmp/Diorama.zip
else echo "    diorama already present"; fi
if [ ! -e apple-samples/hello-world/README.md ]; then
  curl -L --fail -o /tmp/HelloWorld.zip https://docs-assets.developer.apple.com/published/eb5d7fb6e0b9/HelloWorld.zip
  unzip -q -o /tmp/HelloWorld.zip -d apple-samples/hello-world && rm -f /tmp/HelloWorld.zip
else echo "    hello-world already present"; fi

echo "==> Poly Haven HDRIs (CC0, 2K)"
mkdir -p practice-assets/hdri
for id in kloofendal_38d_partly_cloudy rogland_sunset rogland_moonlit_night; do
  [ -f "practice-assets/hdri/$id.hdr" ] && { echo "    $id already present"; continue; }
  url=$(curl -sS --fail "https://api.polyhaven.com/files/$id" \
    | /usr/bin/python3 -c "import json,sys; print(json.load(sys.stdin)['hdri']['2k']['hdr']['url'])")
  curl -L --fail -o "practice-assets/hdri/$id.hdr" "$url"
  echo "    $id"
done

echo "==> Apple Quick Look models (practice only — do not ship)"
mkdir -p practice-assets/usdz
for m in teapot/teapot stratocaster/fender_stratocaster vintagerobot2k/robot; do
  f="practice-assets/usdz/$(basename "$m").usdz"
  [ -f "$f" ] && { echo "    $(basename "$m") already present"; continue; }
  curl -L --fail -o "$f" "https://developer.apple.com/quick-look-gallery/models/$m.usdz"
  echo "    $(basename "$m")"
done

echo "Done."
