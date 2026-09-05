"""Extract one animated candle flame from the Sketchfab candle.

Run through Blender:
    /Applications/Blender.app/Contents/MacOS/Blender --background \
        --python tools/convert_candle_flame.py

The source is a whole candle set -- three flames, the wax and a stray plane --
rigged to one armature and authored about 130 units tall, so it arrives forty
metres high. This keeps a single flame and its armature, discards the rest, and
normalises the result so the flame stands on z=0 and is exactly 1.0 tall. The
generator scales it to whatever a candle needs.

The animation is bone-driven, which is the only kind that survives
glTF -> Blender -> USD: a flame animated in a material graph would export as a
still. Verified -- the export carries SkelRoot, Skeleton and SkelAnimation, and
RealityKit reports and plays it.
"""
from pathlib import Path

import bpy
import mathutils

ROOT = Path.cwd()
SRC = ROOT / "assets/source/candle_light/scene.gltf"
OUT = (ROOT / "app/Packages/RealityKitContent/Sources/RealityKitContent/"
              "RealityKitContent.rkassets/flame/CandleFlame.usda")
KEEP = "candleflame001"

if not SRC.exists():
    raise SystemExit(f"missing {SRC}")


def measure(obj):
    """World-space bounds of one object, at the current frame."""
    corners = [obj.matrix_world @ mathutils.Vector(c) for c in obj.bound_box]
    xs = [c.x for c in corners]
    ys = [c.y for c in corners]
    zs = [c.z for c in corners]
    return xs, ys, zs


bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(SRC))

# Keep one flame. The armature stays whole: the bones that drove the other two
# cost nothing, and removing them risks breaking the action that references them.
#
# Match on the mesh *data* name, not the object name. The glTF importer names the
# objects Object_7, Object_9, Object_11 and only the mesh data carries
# candleflame001 -- filtering on the object name silently deletes every mesh.
for obj in [o for o in bpy.data.objects if o.type == "MESH"]:
    if not getattr(obj.data, "name", "").startswith(KEEP):
        bpy.data.objects.remove(obj, do_unlink=True)

flame = next(o for o in bpy.data.objects if o.type == "MESH")
print(f"kept object {flame.name!r} (mesh {flame.data.name!r})")
root = flame
while root.parent is not None:
    root = root.parent

scene = bpy.context.scene
if bpy.data.actions:
    lo, hi = bpy.data.actions[0].frame_range
    scene.frame_start, scene.frame_end = int(lo), int(hi)
    print(f"ACTION {bpy.data.actions[0].name} frames {int(lo)}..{int(hi)}")
scene.frame_set(scene.frame_start)
bpy.context.view_layer.update()

xs, ys, zs = measure(flame)
height = max(zs) - min(zs)
print(f"flame at rest: {max(xs)-min(xs):.1f} x {max(ys)-min(ys):.1f} x {height:.1f} units")

# Normalise on the root so the armature and its animation scale with the mesh.
factor = 1.0 / height
root.scale = tuple(v * factor for v in root.scale)
bpy.context.view_layer.update()

xs, ys, zs = measure(flame)
root.location = (root.location[0] - (min(xs) + max(xs)) / 2.0,
                 root.location[1] - (min(ys) + max(ys)) / 2.0,
                 root.location[2] - min(zs))
bpy.context.view_layer.update()

OUT.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.usd_export(filepath=str(OUT),
                      export_animation=True,
                      export_materials=True,
                      export_textures_mode="NEW",
                      relative_paths=True,
                      selected_objects_only=False)

xs, ys, zs = measure(flame)
print(f"NORMALISED to {max(xs)-min(xs):.3f} x {max(ys)-min(ys):.3f} x "
      f"{max(zs)-min(zs):.3f}, base z {min(zs):+.3f}")
print(f"WROTE {OUT.relative_to(ROOT)}")
