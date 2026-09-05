# Tools

## `generate_tower_shell.py`

Writes `TowerShell.usda` — the whole room — from a handful of constants. The shell
is a cylinder, a cone and a disc, which no purchased asset would match, so it is
generated rather than modelled. **Edit this, never the USD it produces.**

```bash
python3 tools/generate_tower_shell.py
TOWER_AIDS=1 python3 tools/generate_tower_shell.py         # blockout aids on
TOWER_WALL_TINT=0.5,0.6,0.85 python3 tools/generate_tower_shell.py
```

Constants worth knowing: `DIAMETER`, `WALL_HEIGHT`, `APEX_HEIGHT` (derived, keeps a
45° roof), `WINDOW_*`, `WALL_THICK`, `TOWER_ELEV`, `PROPS`, `CANDLES`, `NEIGHBOURS`.

It prints what it built, including **how many faces it re-wound**. Watch that: a
mesh that suddenly starts being flipped means its normals are wrong. `Wall` should
always report zero.

## `convert_props.py`

Converts Quaternius glTF to USD through Blender headless.

```bash
/Applications/Blender.app/Contents/MacOS/Blender --background \
    --python tools/convert_props.py -- Table_Large Chair_1
```

With no names it converts a default shortlist. Uses glTF rather than FBX (better
material fidelity) and **rotates the geometry −90° about X and bakes it**, because
Blender is Z-up and this scene is Y-up. Do not use the exporter's
`convert_orientation`: it rewrites the `upAxis` metadata without moving the points,
leaving the two disagreeing.

## `fetch_assets.sh`

Re-downloads the free CC0 assets: Poly Haven HDRIs and PBR textures, and the
tone-mapped skydome JPEGs. Idempotent. Purchased assets are not covered — back
those up yourself; only their licences are tracked.

Two traps baked into this script: `sips -M` silently does nothing (use
`--matchTo`), and `sips` converts HDR to **Display P3** by default, which
RealityKit will not load.

## `preview_cameras.usda`

Viewpoints for `usdrecord`, because the simulator's camera cannot be aimed.

```bash
usdrecord --camera RoomWide --imageWidth 1000 tools/preview_cameras.usda out.png
```

Cameras: `Seated`, `AtDesk`, `RoomWide`, `AtWindow`, `WindowWide`, `LeanOut`,
`Eaves`, `AtStand`, `StraightUp`, `UpAtRoof`, `Corner`, `Outside`.

**These renders are not proof of correctness.** Storm draws both face windings and
any colour space happily. RealityKit does not.

## `merge_town.py`

Bakes each village building into a single mesh, cutting the town from ~2,400
entities to 53. Run through Blender, after any change to the village layout:

```
python3 tools/generate_tower_shell.py          # writes build/town_placements.json
/Applications/Blender.app/Contents/MacOS/Blender --background \
    --python tools/merge_town.py
python3 tools/generate_tower_shell.py          # now references the baked meshes
```

The generator prints which mode it used. `village/merged/` is gitignored while the
generated `TowerShell.usda` that references it is not, so **a fresh clone must run
this before building** or the town's houses resolve to nothing. Re-run it after any
change to the village layout too, or the town keeps the old baked geometry.

## `edit_house.py`

Rearrange one house by hand in Reality Composer Pro.

The town ships as one baked mesh per building, so there are no pieces inside
`village/merged/House07.usdc` to move — the modules only exist as placement data.
This writes that data back out as a normal USD scene of individual module
references, and reads your edits back in.

```
python3 tools/edit_house.py list                 # which buildings exist
python3 tools/edit_house.py export House07       # -> app/house-edits/House07.usda
#   open that file in Reality Composer Pro, move the pieces, save
python3 tools/edit_house.py import House07       # -> assets/house_edits/House07.json
python3 tools/generate_tower_shell.py
/Applications/Blender.app/Contents/MacOS/Blender --background \
    --python tools/merge_town.py
```

The override in `assets/house_edits/` wins over the procedural layout on every
regeneration, and is tracked in git. Delete it to go back to the generated house.

Notes:
- Duplicating a piece in RCP works; the importer reads anything that references a
  village module, whatever the prim is called.
- The house is exported **at the origin**, so it is right in front of the camera
  when the file opens; press **F** in the viewport to frame it. Where it stands
  in the town is kept in `app/house-edits/<House>.origin.json` and added back on
  import. Moving the root Xform moves the whole building.
- Scaling a piece is dropped: the placement format carries position and rotation
  only, and the importer warns when it sees a scale.
- Overrides are keyed by building name, and the names come from the procedural
  layout order. Changing the village layout constants can therefore point an old
  edit at a different building.
- The lit window panes are still placed procedurally, so moving a wall a long way
  can leave its pane behind.

## Village style

The houses are whole buildings from the Quaternius Medieval Village Pack, placed
one per plot. There is nothing to assemble and nothing to bake:

```
TOWER_VILLAGE=prebuilt   # default — whole buildings, no bake step
TOWER_VILLAGE=modular    # the old kit-of-parts houses, needs merge_town.py
```

The pack has only three usable house models, so they are chosen in runs of two to
four along a street, which reads as a terrace built in one go rather than a
shuffled deck. `merge_town.py` and `edit_house.py` only apply to the modular
style; in prebuilt there are no modules to bake or rearrange.

## `convert_candle_flame.py`

Extracts the animated candle flame from the Sketchfab candle set (CC BY — see the
manifest; the credit is required and appears in `CreditsView`).

```
/Applications/Blender.app/Contents/MacOS/Blender --background \
    --python tools/convert_candle_flame.py
```

Keeps one flame and its armature, discards the wax and the other two flames, and
normalises the result to stand on 0 and be exactly 1.0 tall, so the generator can
scale it. Without it the generator falls back to the still bonfire-derived shape.

Two traps it exists to handle:
- The glTF importer names the objects `Object_7`, `Object_9`, `Object_11`; only
  the *mesh data* carries `candleflame001`. Filtering on the object name silently
  deletes every mesh.
- The export is `upAxis = "Z"` and the scene is `"Y"`. USD does **not** rotate for
  a differing upAxis — it is advisory metadata, not a transform — so the generator
  applies -90 about X when it references the flame.
