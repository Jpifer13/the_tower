"""Open one village house as movable pieces, and read your edits back.

    python3 tools/edit_house.py list
    python3 tools/edit_house.py export House07
    # ...rearrange it in Reality Composer Pro, save...
    python3 tools/edit_house.py import House07
    python3 tools/generate_tower_shell.py
    /Applications/Blender.app/Contents/MacOS/Blender --background \
        --python tools/merge_town.py

The town ships as one baked mesh per building, so there are no pieces in
`village/merged/House07.usdc` to move -- the modules only exist in the
generator's placement data. This writes that data back out as a normal USD
scene of individual module references, which Reality Composer Pro can open and
rearrange, and then reads the result back into an override the generator honours.

Edits live in `assets/house_edits/<House>.json` and survive regeneration. Delete
that file to go back to the procedural house.
"""
import json
import math
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLACEMENTS = ROOT / "build/town_placements.json"
VILLAGE = ("app/Packages/RealityKitContent/Sources/RealityKitContent/"
           "RealityKitContent.rkassets/village")
EDIT_DIR = ROOT / "app/house-edits"
OVERRIDE_DIR = ROOT / "assets/house_edits"


def load_placements():
    if not PLACEMENTS.exists():
        sys.exit("No build/town_placements.json — run tools/generate_tower_shell.py first.")
    return json.loads(PLACEMENTS.read_text())


def cmd_list():
    houses = load_placements()
    edited = {f.stem for f in OVERRIDE_DIR.glob("*.json")}
    print(f"{len(houses)} buildings:")
    for name in sorted(houses):
        mark = "  (edited)" if name in edited else ""
        print(f"  {name}  {len(houses[name]):3d} pieces{mark}")


def cmd_export(name):
    houses = load_placements()
    if name not in houses:
        sys.exit(f"No such building: {name}. Try `list`.")
    rows = houses[name]

    # Put the house at the origin of the edit file and carry its position on the
    # root, so it opens somewhere you can actually see rather than 40 m out.
    cx = sum(r[1] for r in rows) / len(rows)
    cy = min(r[2] for r in rows)
    cz = sum(r[3] for r in rows) / len(rows)

    # Relative to the edit file, not to the repo root: hand-assembling this
    # silently produced app/app/... and every reference failed to resolve.
    rel = os.path.relpath(ROOT / VILLAGE, EDIT_DIR)
    body = []
    for i, (mod, x, y, z, rx, ry, rz) in enumerate(rows):
        body.append(f'''    def "P{i:03d}" (
        prepend references = @{rel}/{mod}.usdc@
    )
    {{
        double3 xformOp:translate = ({x - cx:.4f}, {y - cy:.4f}, {z - cz:.4f})
        float3 xformOp:rotateXYZ = ({rx:.2f}, {ry:.2f}, {rz:.2f})
        uniform token[] xformOpOrder = ["xformOp:translate", "xformOp:rotateXYZ"]
    }}
''')

    EDIT_DIR.mkdir(parents=True, exist_ok=True)
    out = EDIT_DIR / f"{name}.usda"
    out.write_text(f'''#usda 1.0
(
    defaultPrim = "{name}"
    metersPerUnit = 1
    upAxis = "Y"
)

# Exported by tools/edit_house.py — rearrange the pieces, save, then:
#     python3 tools/edit_house.py import {name}
#
# The root's translate is where the house stands in the town; leave it alone
# unless you mean to move the whole building. Duplicating a piece is fine — the
# importer reads whatever references a village module.

def Xform "{name}"
{{
    double3 xformOp:translate = ({cx:.4f}, {cy:.4f}, {cz:.4f})
    uniform token[] xformOpOrder = ["xformOp:translate"]

{"".join(body)}}}
''')
    print(f"wrote {out.relative_to(ROOT)}  ({len(rows)} pieces)")
    print("open it in Reality Composer Pro, rearrange, save, then:")
    print(f"    python3 tools/edit_house.py import {name}")


def quat_to_euler_xyz(w, x, y, z):
    """USD rotateXYZ is Rz*Ry*Rx; Reality Composer Pro writes a quaternion."""
    n = math.sqrt(w * w + x * x + y * y + z * z) or 1.0
    w, x, y, z = w / n, x / n, y / n, z / n
    r00 = 1 - 2 * (y * y + z * z)
    r10 = 2 * (x * y + w * z)
    r20 = 2 * (x * z - w * y)
    r21 = 2 * (y * z + w * x)
    r22 = 1 - 2 * (x * x + y * y)
    beta = math.asin(max(-1.0, min(1.0, -r20)))
    alpha = math.atan2(r21, r22)
    gamma = math.atan2(r10, r00)
    return (math.degrees(alpha), math.degrees(beta), math.degrees(gamma))


VEC = r"\(\s*([-\d.eE]+)\s*,\s*([-\d.eE]+)\s*,\s*([-\d.eE]+)\s*\)"
QUAT = r"\(\s*([-\d.eE]+)\s*,\s*([-\d.eE]+)\s*,\s*([-\d.eE]+)\s*,\s*([-\d.eE]+)\s*\)"


def cmd_import(name):
    src = EDIT_DIR / f"{name}.usda"
    if not src.exists():
        sys.exit(f"No {src.relative_to(ROOT)} — export it first.")
    text = src.read_text()

    root = re.search(r'def Xform "' + re.escape(name) + r'"\s*\{(.*?)\n    def ',
                     text, re.S)
    rt = re.search(r"xformOp:translate\s*=\s*" + VEC, root.group(1)) if root else None
    ox, oy, oz = (float(rt.group(1)), float(rt.group(2)), float(rt.group(3))) if rt \
        else (0.0, 0.0, 0.0)

    rows, warned = [], set()
    # Every prim that references a village module counts, whatever it is named,
    # so pieces duplicated in RCP come through too.
    for block in re.finditer(
            r'def\s+\w*\s*"([^"]+)"[^{]*?references\s*=\s*@[^@]*?/([A-Za-z0-9_]+)\.usdc@'
            r'[^{]*\{(.*?)\n    \}', text, re.S):
        mod, body = block.group(2), block.group(3)
        t = re.search(r"xformOp:translate\s*=\s*" + VEC, body)
        x, y, z = (float(t.group(1)), float(t.group(2)), float(t.group(3))) if t \
            else (0.0, 0.0, 0.0)

        e = re.search(r"xformOp:rotateXYZ\s*=\s*" + VEC, body)
        q = re.search(r"xformOp:orient\s*=\s*" + QUAT, body)
        if e:
            rx, ry, rz = float(e.group(1)), float(e.group(2)), float(e.group(3))
        elif q:
            rx, ry, rz = quat_to_euler_xyz(*[float(q.group(i)) for i in (1, 2, 3, 4)])
        else:
            rx = ry = rz = 0.0

        sc = re.search(r"xformOp:scale\s*=\s*" + VEC, body)
        if sc and any(abs(float(sc.group(i)) - 1.0) > 0.01 for i in (1, 2, 3)):
            if mod not in warned:
                print(f"  ! {mod} is scaled; the town's placement format has no "
                      f"scale, so it will be dropped")
                warned.add(mod)

        rows.append([mod, round(ox + x, 4), round(oy + y, 4), round(oz + z, 4),
                     round(rx, 2), round(ry, 2), round(rz, 2)])

    if not rows:
        sys.exit("Found no pieces referencing village modules — is this the right file?")

    OVERRIDE_DIR.mkdir(parents=True, exist_ok=True)
    dst = OVERRIDE_DIR / f"{name}.json"
    dst.write_text(json.dumps(rows, indent=1))
    print(f"wrote {dst.relative_to(ROOT)}  ({len(rows)} pieces)")
    print("now rebuild the town:")
    print("    python3 tools/generate_tower_shell.py")
    print("    /Applications/Blender.app/Contents/MacOS/Blender --background "
          "--python tools/merge_town.py")


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or args[0] not in ("list", "export", "import"):
        sys.exit(__doc__)
    if args[0] == "list":
        cmd_list()
    elif len(args) < 2:
        sys.exit(f"{args[0]} needs a building name — try `list`.")
    elif args[0] == "export":
        cmd_export(args[1])
    else:
        cmd_import(args[1])
