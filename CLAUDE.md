# The Tower — agent guide

A wizard-tower immersive environment for Apple Vision Pro. **A personal tool, not
a product.** An App Store release may follow as a stripped-down generic version,
but it drives no decisions. See [`docs/decisions/DECISIONS.md`](docs/decisions/DECISIONS.md).

## Start here

| Question | File |
|---|---|
| What am I building? | [`docs/design/design-doc.md`](docs/design/design-doc.md) |
| Where are we? | [`PROGRESS.md`](PROGRESS.md) |
| Why is it like this? | [`docs/decisions/DECISIONS.md`](docs/decisions/DECISIONS.md) |
| Why did that not work? | [`docs/learning-notes/`](docs/learning-notes/) |
| The original plan | [`wizard_tower_build_plan.md`](wizard_tower_build_plan.md) |

## The single most important thing

**Verify numerically, not by eye.** Nearly every bug in this project has been
geometry that *existed but was invisible*, or an edit that *appeared* to apply and
did nothing. Renders looked fine each time.

Concretely:
- Dump the USD and assert on it (`usdcat`, or parse `TowerShell.usda` directly).
- Measure pixels rather than judging colour by eye — `sips -s format bmp` then
  average the channels.
- Assert that string replacements matched **before** trusting them. A silent
  no-op cost several rounds.
- Offline `usdrecord` renders are **not** proof. Storm draws both face windings
  and any colour space happily; RealityKit does not. Only the simulator finds
  those.

Read [`docs/learning-notes/realitykit-geometry-gotchas.md`](docs/learning-notes/realitykit-geometry-gotchas.md)
before touching geometry. It is nine hard-won traps, all of which will recur.

## Layout

```
app/                      visionOS app
  WizardTower/            SwiftUI + RealityKit sources
  Packages/RealityKitContent/
    …/RealityKitContent.rkassets/
      TowerShell.usda     GENERATED — never hand-edit
      Tower.usda          composition root, safe to edit in RCP
      props/              converted Quaternius models
      textures/           CC0 PBR sets
tools/
  generate_tower_shell.py the room, parametrically
  convert_props.py        glTF → USD via Blender headless
  fetch_assets.sh         re-download the free assets
  preview_cameras.usda    offline viewpoints for usdrecord
assets/                   source assets + licences (binaries gitignored)
docs/                     design, decisions, learning notes
reference/                Apple samples, practice assets (gitignored)
```

## Workflow

```bash
# Regenerate the room after editing tools/generate_tower_shell.py
python3 tools/generate_tower_shell.py

# Build and run
cd app && xcodebuild build -scheme WizardTower \
  -destination 'platform=visionOS Simulator,name=Apple Vision Pro'
xcrun simctl install "Apple Vision Pro" <path>/WizardTower.app
xcrun simctl launch "Apple Vision Pro" io.confuseddev.wizardtower

# Logs — note --info, or you only see errors and success looks like silence
xcrun simctl spawn "Apple Vision Pro" log show --info --last 2m \
  --predicate 'subsystem == "io.confuseddev.wizardtower"'

# Offline render from arbitrary viewpoints (the sim camera cannot be aimed)
usdrecord --camera RoomWide --imageWidth 1000 tools/preview_cameras.usda out.png

# Re-bake the town after any change to the village layout (or on a fresh clone,
# or the houses resolve to nothing)
/Applications/Blender.app/Contents/MacOS/Blender --background \
  --python tools/merge_town.py

# Rearrange one house by hand in Reality Composer Pro
python3 tools/edit_house.py export House07     # then edit + save in RCP
python3 tools/edit_house.py import House07     # then regenerate, then re-bake
```

**Blockout aids** (1.7 m figure, walkable envelope, fireplace marker) are off by
default: `TOWER_AIDS=1 python3 tools/generate_tower_shell.py`.

**Wall look:** `TOWER_WALL_TINT=0.5,0.6,0.85`, `TOWER_WALL_TEX=…`, `TOWER_SKY=…`.

## Verifying visually in the simulator

The simulator's camera cannot be aimed and starts at the seat facing a wall 1.26 m
away. To see anything else, either use `usdrecord`, or temporarily:
- add `.task { await toggleImmersiveSpace(open: true) }` to `ControlPanelView`, and
- add a yaw to the `Shell` prim in `Tower.usda` to turn the room.

**Always revert both.** They have been left in by accident before.

## Conventions that matter

- **User-relative space.** Origin is the seat, `-Z` is the desk you face, `+X` is
  your right, window at +55°. visionOS puts the user at the origin looking down −Z.
- **Y-up, metres.** Blender exports Z-up; `convert_props.py` rotates and bakes it.
  `convert_orientation` on the exporter rewrites metadata *without* moving points.
- **Generated vs authored.** `TowerShell.usda` is build output. Edit the generator.
  `Tower.usda` composes it and is safe to hand-edit in Reality Composer Pro.
- **Positions live in one place.** Flames are named `Flame_<candle>_<wick>` and
  Swift finds them by name. Do not reintroduce a parallel list in Swift.

## Hard-won constraints

- **`.full` immersion, deliberately.** `.mixed` cannot be lit — RealityKit lights
  it from the real surroundings and `ImageBasedLightComponent` does not override
  that. Night could never be dark. Cost: a 1.5 m *radius* safety boundary centred
  where you start.
- **A third-party app cannot host other apps.** Opening an `ImmersiveSpace` hides
  every other app. Mac Virtual Display is the one exception, behind Developer Mode.
- **`doubleSided` is ignored.** Winding alone decides visibility, and a wrong-wound
  face renders as *nothing*. The generator auto-corrects winding against the
  supplied normals — so the **normals** must be right.
- **Point lights cannot cast shadows.** No `PointLightComponent.Shadow` exists.
  Use a spot light for anything that must cast.
- **Components land on an entity's origin, not its vertices.** Geometry authored in
  world space needs a transform before Swift attaches a light or measures it.

## Working style

- Commit straight to `main`; no feature branches or PRs unless asked.
- No Claude/AI/Anthropic authorship anywhere — commits, comments, docs.
- Prefer Python for tooling.
- Every asset needs a row in `assets/ASSET_MANIFEST.md` and a folder in
  `assets/licenses/` **before** use. Buy commercial-use licences even though this
  is personal, so a generic version stays cheap.
- Asset failures should degrade and log, never `assertionFailure` — that traps in
  debug and turns a cosmetic problem into a crash with no diagnostics.
