"""Bake each village building into a single mesh.

Run through Blender:
    /Applications/Blender.app/Contents/MacOS/Blender --background \
        --python tools/merge_town.py -- [House00 House01 ...]

The town is assembled from ~2400 placements of 20 modular kit pieces. As
individual references that is ~2400 entities and as many draw calls, which is
CPU work the GPU cannot help with. RealityKit will not do this for us: a USD
PointInstancer is *not* expanded -- measured on visionOS 26.5, it loads the
prototype and discards the placements, dumping the whole town at the origin.

So the joining is done here, ahead of time, one mesh per building. That keeps a
frustum-cullable entity per house while cutting draw calls by ~40x. The cost is
duplicated vertices: shared kit meshes become per-building copies.

Reads build/town_placements.json, written by tools/generate_tower_shell.py.
"""
import json
import math
import re
import os
import subprocess
import sys
from pathlib import Path

import bpy

ROOT = Path.cwd()
SRC = ROOT / "assets/source/Medieval Village MegaKit[Standard]/glTF"
RK = (ROOT / "app/Packages/RealityKitContent/Sources/RealityKitContent/"
             "RealityKitContent.rkassets/village")
OUT = RK / "merged"
TMP = Path(os.environ.get("TOWER_TMP", "/tmp")) / "town_merge"

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
placements = json.loads((ROOT / "build/town_placements.json").read_text())
groups = argv or sorted(placements)

OUT.mkdir(parents=True, exist_ok=True)
TMP.mkdir(parents=True, exist_ok=True)


def import_module(name):
    """Import one kit module, rotated Z-up -> Y-up, and return its objects."""
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(SRC / f"{name}.gltf"))
    fresh = [o for o in set(bpy.data.objects) - before if o.type == "MESH"]
    for o in fresh:
        o.parent = None
    return fresh


ok, failed = [], []
for group in groups:
    rows = placements.get(group)
    if not rows:
        failed.append((group, "no placements"))
        continue
    bpy.ops.wm.read_factory_settings(use_empty=True)

    # Import each distinct module once, then duplicate it per placement.
    cache = {}
    built = []
    try:
        for name, x, y, z, yaw in rows:
            if name not in cache:
                cache[name] = import_module(name)
                for o in cache[name]:
                    o.hide_set(True)
            for proto in cache[name]:
                dup = proto.copy()
                dup.data = proto.data.copy()
                dup.hide_set(False)
                bpy.context.collection.objects.link(dup)
                # Stay in Blender's native Z-up while assembling: the scene's
                # +Y maps to Blender +Z, so the placement yaw about scene Y is
                # a yaw about Blender Z, and (x, y, z) lands at (x, -z, y).
                # The single Z-up -> Y-up bake happens once, after the join.
                dup.rotation_mode = "XYZ"
                dup.rotation_euler = (0.0, 0.0, math.radians(yaw))
                dup.location = (x, -z, y)
                built.append(dup)

        for o in cache.values():
            for proto in o:
                bpy.data.objects.remove(proto, do_unlink=True)

        # Importing each glTF separately gives Blender a fresh copy of every
        # shared material (MI_Plaster, MI_Plaster.001, ...) and a UV layer whose
        # name may differ per import. Both survive the join as extra material
        # subsets and a duplicate UV set, which costs draw calls and file size.
        # Fold them back together first.
        canon = {}
        for o in built:
            for uv in o.data.uv_layers:
                uv.name = "UVMap"
            for slot in o.material_slots:
                if not slot.material:
                    continue
                base = re.sub(r"\.\d+$", "", slot.material.name)
                slot.material = canon.setdefault(base, slot.material)

        bpy.ops.object.select_all(action="DESELECT")
        for o in built:
            o.select_set(True)
        bpy.context.view_layer.objects.active = built[0]
        bpy.ops.object.join()
        joined = bpy.context.view_layer.objects.active

        # Bake the Z-up correction into the points, matching convert_props.py.
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        bpy.ops.transform.rotate(value=-math.pi / 2.0, orient_axis="X",
                                 orient_type="GLOBAL")
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
        joined.name = group

        # Export ASCII so the texture paths can be repointed at the shared,
        # already-downscaled texture folder rather than 53 private copies.
        stage = TMP / f"{group}.usda"
        bpy.ops.wm.usd_export(filepath=str(stage),
                              export_textures_mode="KEEP",
                              export_materials=True,
                              relative_paths=False,
                              selected_objects_only=False)
        text = stage.read_text()
        out_lines = []
        for line in text.splitlines(True):
            if "asset inputs:file" in line and "@" in line:
                head, _, rest = line.partition("@")
                path, _, tail = rest.rpartition("@")
                out_lines.append(f"{head}@../textures/{Path(path).name}@{tail}")
            else:
                out_lines.append(line)
        stage.write_text("".join(out_lines))

        subprocess.run(["/usr/bin/usdcat", "-o", str(OUT / f"{group}.usdc"),
                        str(stage)], check=True)
        ok.append((group, len(rows), len(joined.data.vertices)))
    except Exception as exc:                     # noqa: BLE001
        failed.append((group, str(exc)[:90]))

print(f"\nMERGED {len(ok)} buildings")
for g, n, v in ok:
    print(f"  {g}: {n} modules -> 1 mesh, {v} verts")
if failed:
    print("FAILED:")
    for g, why in failed:
        print(f"  {g}: {why}")
