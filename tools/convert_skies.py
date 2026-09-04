"""Convert the HDRI skies to LDR with *controlled* exposure.

Run through Blender:
    /Applications/Blender.app/Contents/MacOS/Blender --background \
        --python tools/convert_skies.py

fetch_assets.sh used `sips -s format jpeg` on the .hdr files, which applies its
own auto-exposure per file. That normalises every sky to roughly the same average
brightness, so the moonlit night came out *brighter* than midday (mean 133 vs
106) and the window showed a daylit horizon at 2am.

Exposure has to be set per sky and held, so the relative levels survive. The
numbers below are photographic rather than physical:real moonlight is ~1/100000 of
daylight and would render as pure black, so night is exposed up to the point
where the sky reads dark blue with stars and the horizon is only just legible.
"""
import array
import math
import os
import subprocess
import sys
from pathlib import Path

import bpy

ROOT = Path.cwd()
# The skies live in two places and both matter: the generator bakes the rkassets
# copy into the dome's material, and LightRig re-textures that dome at runtime
# from the app-bundle copy. Updating only one leaves the runtime showing the old
# sky, which is exactly what happened the first time round.
DESTS = [
    ROOT / ("app/Packages/RealityKitContent/Sources/RealityKitContent/"
            "RealityKitContent.rkassets/textures"),
    ROOT / "app/WizardTower/Skies",
]
TMP = Path("/tmp/sky_convert")
TMP.mkdir(parents=True, exist_ok=True)

# source stem, output name, linear exposure multiplier
SKIES = [
    ("kloofendal_38d_partly_cloudy", "sky_day", 1.30),
    ("rogland_sunset", "sky_sunset", 0.62),
    ("rogland_moonlit_night", "sky_night", 0.028),
]
if len(sys.argv) > sys.argv.index("--") + 1 if "--" in sys.argv else False:
    picked = sys.argv[sys.argv.index("--") + 1:]
    SKIES = [s for s in SKIES if s[1] in picked or s[0] in picked]

W, H = 2048, 1024


def encode_srgb(c):
    if c <= 0.0031308:
        return 12.92 * c
    return 1.055 * (c ** (1.0 / 2.4)) - 0.055


# A lookup table keeps the per-pixel cost down; the curve is smooth enough that
# 4096 steps are indistinguishable from evaluating it per pixel.
STEPS = 4096
LUT = [encode_srgb(i / (STEPS - 1)) for i in range(STEPS)]

for stem, out_name, exposure in SKIES:
    src = ROOT / "assets/hdri" / f"{stem}-4k.hdr"
    if not src.exists():
        print(f"SKIP {out_name}: {src} missing")
        continue

    image = bpy.data.images.load(str(src))
    image.scale(W, H)
    buf = array.array("f", [0.0]) * (W * H * 4)
    image.pixels.foreach_get(buf)

    out = bytearray(W * H * 3)
    for i in range(W * H):
        for ch in range(3):
            v = buf[i * 4 + ch] * exposure
            # Reinhard: rolls highlights off instead of clipping the sun to a
            # flat white disc, which is what makes a clipped sky look fake.
            v = v / (1.0 + v)
            out[i * 3 + ch] = int(LUT[min(STEPS - 1, max(0, int(v * (STEPS - 1))))] * 255.0 + 0.5)

    # Blender's image origin is bottom-left; PNG rows run top-down.
    flipped = bytearray(W * H * 3)
    for y in range(H):
        s = (H - 1 - y) * W * 3
        flipped[y * W * 3:(y + 1) * W * 3] = out[s:s + W * 3]

    import binascii
    import struct
    import zlib
    raw = bytearray()
    for y in range(H):
        raw.append(0)
        raw += flipped[y * W * 3:(y + 1) * W * 3]

    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", binascii.crc32(tag + data) & 0xFFFFFFFF))

    png = (b"\x89PNG\r\n\x1a\n"
           + chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
           + chunk(b"IDAT", zlib.compress(bytes(raw), 6))
           + chunk(b"IEND", b""))
    stage = TMP / f"{out_name}.png"
    stage.write_bytes(png)

    srgb = "/System/Library/ColorSync/Profiles/sRGB Profile.icc"
    for dest in DESTS:
        dst = dest / f"{out_name}.jpg"
        subprocess.run(["sips", "-s", "format", "jpeg", str(stage),
                        "--out", str(dst)], capture_output=True)
        # RealityKit will not load Display P3; force sRGB as fetch_assets.sh does.
        subprocess.run(["sips", "--matchTo", srgb, str(dst), "--out", str(dst)],
                       capture_output=True)
    print(f"WROTE {out_name}.jpg at exposure {exposure} "
          f"into {len(DESTS)} locations")
    bpy.data.images.remove(image)
