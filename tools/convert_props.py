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
SRC = Path("assets/source/quaternius-fantasy-props/Exports/glTF")
OUT = Path("app/Packages/RealityKitContent/Sources/RealityKitContent/"
           "RealityKitContent.rkassets/props")

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
