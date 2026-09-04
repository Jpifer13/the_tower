"""Convert Quaternius glTF props to USD for Reality Composer Pro.

Run through Blender, not python:
    /Applications/Blender.app/Contents/MacOS/Blender --background \
        --python tools/convert_props.py -- Table_Large Chair_1 ...

With no names it converts the default shortlist. glTF is used rather than FBX
because it carries material and texture bindings more reliably.
"""
import math

import bpy, sys, os
from pathlib import Path

ROOT = Path(bpy.path.abspath("//")) if bpy.data.filepath else Path.cwd()
# Two kits so far: the fantasy props, and the modular village used for the view
# through the window. TOWER_KIT picks which.
KITS = {
    "props": ("assets/source/quaternius-fantasy-props/Exports/glTF", "props"),
    "village": ("assets/source/Medieval Village MegaKit[Standard]/glTF", "village"),
}
KIT = os.environ.get("TOWER_KIT", "props")
SRC = Path(KITS[KIT][0])
OUT = Path("app/Packages/RealityKitContent/Sources/RealityKitContent/"
           "RealityKitContent.rkassets") / KITS[KIT][1]

SHORTLIST = [
    "Table_Large", "Chair_1", "Stool", "Bookcase_2", "Shelf_Arch",
    "Book_Stack_1", "BookGroup_Medium_1", "Candle_1", "CandleStick_Triple",
    "Chandelier", "Potion_1", "Scroll_1", "Chest_Wood",
]

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
names = argv or SHORTLIST

OUT.mkdir(parents=True, exist_ok=True)
ok, failed = [], []
for name in names:
    src = SRC / f"{name}.gltf"
    if not src.exists():
        failed.append((name, "missing")); continue
    bpy.ops.wm.read_factory_settings(use_empty=True)
    try:
        bpy.ops.import_scene.gltf(filepath=str(src))

        # A roof is placed by its footprint centre, so its origin has to *be*
        # that centre. Roof_RoundTiles_6x4 ships with its origin 2.36 m off,
        # which hangs the roof clean off the back of every house using it.
        # Normalise all of them rather than special-casing the one that is wrong.
        #
        # This has to happen *before* the rotation below: after it, y is the up
        # axis, and recentring on y drops the roof through the roofline instead.
        if name.startswith("Roof_RoundTiles"):
            meshes = [o for o in bpy.data.objects if o.type == "MESH"]
            pts = [o.matrix_world @ v.co for o in meshes for v in o.data.vertices]
            if pts:
                dx = (min(p.x for p in pts) + max(p.x for p in pts)) / 2.0
                dy = (min(p.y for p in pts) + max(p.y for p in pts)) / 2.0
                if abs(dx) > 0.01 or abs(dy) > 0.01:
                    bpy.ops.object.select_all(action='SELECT')
                    bpy.ops.transform.translate(value=(-dx, -dy, 0.0))
                    bpy.ops.object.transform_apply(location=True, rotation=False,
                                                   scale=False)
                    print(f"  recentred {name} by {-dx:+.2f}, {-dy:+.2f}")

        # Blender is Z-up; the tower scene is Y-up. convert_orientation on the
        # exporter rewrites the upAxis metadata without rotating the points, which
        # leaves the two disagreeing. Rotate the geometry instead and bake it in:
        # -90 about X maps (x, y, z) -> (x, z, -y), so height moves Z to Y.
        bpy.ops.object.select_all(action='SELECT')
        if bpy.context.selected_objects:
            bpy.context.view_layer.objects.active = bpy.context.selected_objects[0]
            bpy.ops.transform.rotate(value=-math.pi / 2.0, orient_axis='X',
                                     orient_type='GLOBAL')
            bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
        dst = OUT / f"{name}.usdc"
        bpy.ops.wm.usd_export(filepath=str(dst),
                              export_textures_mode='NEW',
                              export_materials=True,
                              relative_paths=True,
                              selected_objects_only=False)
        ok.append(name)
    except Exception as exc:                     # noqa: BLE001
        failed.append((name, str(exc)[:70]))

print(f"\nCONVERTED {len(ok)}: {', '.join(ok)}")
if failed:
    print("FAILED:")
    for n, why in failed:
        print(f"  {n}: {why}")
