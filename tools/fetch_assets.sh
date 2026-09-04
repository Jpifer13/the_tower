#!/usr/bin/env bash
# Re-download the free (CC0) assets. Purchased assets are not covered — keep those
# backed up yourself; only their licences are tracked in git.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p assets/hdri
for id in kloofendal_38d_partly_cloudy rogland_sunset rogland_moonlit_night; do
  out="assets/hdri/$id-4k.hdr"
  [ -f "$out" ] && { echo "$id already present"; continue; }
  url=$(curl -sS --fail "https://api.polyhaven.com/files/$id" \
    | /usr/bin/python3 -c "import json,sys; print(json.load(sys.stdin)['hdri']['4k']['hdr']['url'])")
  curl -L --fail -o "$out" "$url"
  echo "$id"
done
echo "==> PBR texture sets (CC0, 2K) for the generated shell"
RK="app/Packages/RealityKitContent/Sources/RealityKitContent/RealityKitContent.rkassets/textures"
mkdir -p "$RK"
fetch_tex() {  # role, polyhaven id
  for pair in "Diffuse:diff" "nor_gl:nor" "Rough:rough"; do
    m="${pair%%:*}"; short="${pair##*:}"
    out="$RK/$1_$short.jpg"
    [ -f "$out" ] && continue
    url=$(curl -sS --fail "https://api.polyhaven.com/files/$2" \
      | /usr/bin/python3 -c "import json,sys; print(json.load(sys.stdin)['$m']['2k']['jpg']['url'])")
    curl -L --fail -o "$out" "$url"
  done
  echo "    $1 ($2)"
}
fetch_tex wall  castle_wall_slates

# The slate ships warm, and no amount of tinting makes a warm albedo read as grey
# stone. Desaturate the diffuse so the stone itself is neutral and the lighting is
# free to do whatever it likes on top. Idempotent: greyscale twice is still grey.
GRAY="/System/Library/ColorSync/Profiles/Generic Gray Gamma 2.2 Profile.icc"
SRGB=$(ls /System/Library/ColorSync/Profiles/sRGB*.icc 2>/dev/null | head -1)
if [ -f "$RK/wall_diff.jpg" ] && [ -f "$GRAY" ] && [ -n "$SRGB" ]; then
  # NB: sips -M silently does nothing here. --matchTo is the flag that works.
  sips --matchTo "$GRAY" "$RK/wall_diff.jpg" --out /tmp/_wall_g.jpg >/dev/null 2>&1
  sips --matchTo "$SRGB" /tmp/_wall_g.jpg --out "$RK/wall_diff.jpg" >/dev/null 2>&1
  rm -f /tmp/_wall_g.jpg
  echo "    wall diffuse desaturated"
fi
fetch_tex floor dark_wooden_planks
fetch_tex roof  brown_planks_03

echo "==> Skydome textures"
# Deliberately NOT done here. `sips -s format jpeg` auto-exposes each HDR on its
# own, which normalises every sky to the same average brightness -- the moonlit
# night came out brighter than midday (mean 133 vs 106) and the window showed a
# daylit horizon at 2am. Exposure has to be set per sky and held, which needs
# real pixel maths:
#
#     /Applications/Blender.app/Contents/MacOS/Blender --background \
#         --python tools/convert_skies.py
#
echo "    run tools/convert_skies.py through Blender (see the note above)"

echo "Done. Licences: assets/licenses/  Manifest: assets/ASSET_MANIFEST.md"
