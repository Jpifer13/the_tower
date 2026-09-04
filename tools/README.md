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
