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
echo "Done. Licences: assets/licenses/  Manifest: assets/ASSET_MANIFEST.md"
