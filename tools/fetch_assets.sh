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
fetch_tex wall  medieval_blocks_05
fetch_tex floor dark_wooden_planks
fetch_tex roof  brown_planks_03

echo "Done. Licences: assets/licenses/  Manifest: assets/ASSET_MANIFEST.md"
