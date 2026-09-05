"""Pull the flame geometry out of the village pack's lit bonfire.

    python3 tools/extract_flame.py

The candles' flames were spheres -- glowing orbs on sticks. Quaternius' Bonfire_Lit
carries its fire on its own `Fire` material, so the shape can be lifted out and
reused at candle scale. Only the geometry is taken: the pack's Fire material is
flat grey, and the generator already has an emissive flame material worth keeping.

Writes tools/flame_mesh.json, normalised so the flame is centred on x/z, sits on
y=0 and stands exactly 1.0 tall -- the generator then scales it to whatever a
candle needs. Committed, because assets/source/ is not.
"""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "assets/source/Medieval Village Pack - Dec 2020/Props/OBJ/Bonfire_Lit.obj"
OUT = Path(__file__).resolve().parent / "flame_mesh.json"

if not SRC.exists():
    raise SystemExit(f"missing {SRC} — the pack lives in assets/source/, which is gitignored")

verts, faces, current = [], [], None
for line in SRC.read_text().splitlines():
    if line.startswith("v "):
        verts.append([float(v) for v in line.split()[1:4]])
    elif line.startswith("usemtl"):
        current = line.split()[1].strip()
    elif line.startswith("f ") and current == "Fire":
        faces.append([int(tok.split("/")[0]) - 1 for tok in line.split()[1:]])

used = sorted({i for f in faces for i in f})
remap = {old: new for new, old in enumerate(used)}
pts = [verts[i] for i in used]

xs = [p[0] for p in pts]
ys = [p[1] for p in pts]
zs = [p[2] for p in pts]
cx, cz = (min(xs) + max(xs)) / 2.0, (min(zs) + max(zs)) / 2.0
height = max(ys) - min(ys)
pts = [[(p[0] - cx) / height, (p[1] - min(ys)) / height, (p[2] - cz) / height]
       for p in pts]
faces = [[remap[i] for i in f] for f in faces]

# Flat normals from each face's own winding. Passing these through means the
# generator's winding auto-correction leaves the source's winding alone.
normals = []
for f in faces:
    a, b, c = pts[f[0]], pts[f[1]], pts[f[2]]
    e1 = [b[k] - a[k] for k in range(3)]
    e2 = [c[k] - a[k] for k in range(3)]
    n = [e1[1] * e2[2] - e1[2] * e2[1],
         e1[2] * e2[0] - e1[0] * e2[2],
         e1[0] * e2[1] - e1[1] * e2[0]]
    length = math.sqrt(sum(v * v for v in n)) or 1.0
    normals.append([v / length for v in n])

OUT.write_text(json.dumps({"points": pts, "faces": faces, "normals": normals}))
w = (max(xs) - min(xs)) / height
d = (max(zs) - min(zs)) / height
print(f"{len(faces)} faces, {len(pts)} verts -> {OUT.relative_to(ROOT)}")
print(f"normalised to {w:.2f} x {d:.2f} wide per 1.0 of height")
