# RealityKit geometry gotchas

Learned the hard way on 2026-09-03, mostly by shipping broken geometry several
times in a row. Every one of these renders perfectly in `usdrecord` and fails in
RealityKit, which is why offline previews cannot be trusted alone.

## 1. `doubleSided` is ignored — winding decides visibility

Setting `uniform bool doubleSided = 1` does not stop RealityKit culling back
faces. A face wound the wrong way renders as **nothing at all** — not black, not
inside-out, simply absent. It looks like missing geometry rather than a bug.

This bit three times in one session:
- The **skydome** was wound outward, so from inside every face was culled. The
  window showed passthrough, which read as "the sky is missing".
- The **shaft** below the room reused the wall's vertex ordering, but its
  parameter ran downward, silently inverting the winding. The whole tower below
  the window vanished.
- The **floor** was inverted too, and nobody noticed for hours.

`usdrecord` draws both windings happily. **Only the simulator finds these.**

## 2. Normals and winding must agree — and check the normals first

`tools/generate_tower_shell.py` now reorders each face's vertices so its winding
matches its supplied normal, and prints per-mesh counts of what it reordered.

That check is only as good as the normals. The wall's "inward" normal was
`(-sin t, 0, -cos t)`, which is *outward*: for a point
`(R sin t, y, -R cos t - SEAT_Z)` the inward radial is `(-sin t, 0, +cos t)`.
While normals only drove shading this was invisible. The moment the winding pass
started trusting them, it inverted correct geometry to match wrong normals and
culled the walls.

**Watch the per-mesh counts.** A mesh that suddenly starts being flipped is the
tell. The wall should always report zero.

## 3. Textures must be sRGB

`sips` converts HDR to **Display P3** by default. RealityKit silently fails to
load those, so the surface draws as nothing. Every texture needs converting with
`--matchTo` against the sRGB profile.

## 4. `sips -M` silently does nothing

It returns exit code 0 and writes no file. **`--matchTo` is the flag that works.**
This wasted a lot of time twice: skydome textures stayed P3, and a "desaturated"
wall texture was never desaturated — which then invalidated a conclusion drawn
from measuring it.

## 5. `UIImage(named:)` will not find loose bundle files

It is really an asset-catalog lookup. A `.jpg` sitting at the root of the app
bundle is not found, and the failure is silent unless you log it. Resolve the URL
instead:

```swift
Bundle.main.url(forResource: name, withExtension: "jpg")
```

This is how the window's image-based light quietly did nothing while the room was
lit by the directional sun alone, and looked flat as a result.

## 6. `log show` hides info-level messages

Without `--info` you only see errors, so success messages never appear and it
looks like the code never ran:

```
xcrun simctl spawn "Apple Vision Pro" log show --info --last 3m \
    --predicate 'subsystem == "io.confuseddev.wizardtower"'
```

Also: never `assertionFailure` on a missing asset. It traps in debug and kills the
app, turning a cosmetic problem into a crash with no diagnostics.

## 7. Lights cast no shadows until you add a Shadow component

A `DirectionalLightComponent` on its own lights the room and casts nothing. It
needs `DirectionalLightComponent.Shadow`, and the default projection only reaches
**5 m** — less than this room is wide, so the far half stayed shadowless. Use
`.automatic(maximumDistance:)` sized to the room.

**`PointLightComponent` has no shadow support at all** — there is no
`PointLightComponent.Shadow` in the SDK. Candles as point lights can never cast
shadows. `SpotLightComponent.Shadow` does exist, so anything that needs to throw
shadows has to be a spot light.

## 8. Single-sided geometry casts no shadow

Back-face culling applies to the shadow map too, so a surface only blocks light
from the side its faces point at. The conical roof was a single surface facing
into the room: from the sun's side it was back-facing, culled, and sunlight came
straight through the roof.

Anything that should block light needs a surface facing the light — the roof got
an outer skin, exactly as the wall did. Worth checking whenever something is lit
from a direction it should not be.

## 9. A component lands on the entity's origin, not on its vertices

Generated geometry is naturally authored in world space — a mesh whose vertices
are already where they belong needs no transform. That is fine until Swift
attaches a **component** to it.

Every flame's sphere sat correctly above its candle, but each prim had no
transform, so the entity's origin was (0, 0, 0). Attaching a `PointLightComponent`
put all ten lights in a stack **under the chair**, which lit the room from one
point and looked like a lighting bug rather than a positioning one.

Anything Swift will attach a component to, or measure the position of, needs the
position on the **prim** and geometry built around the local origin.

## The pattern worth remembering

Every bug here looked like it had been fixed. An edit that did not apply, a flag
that did nothing, a face that rendered fine offline. **Verify numerically, not by
eye** — dump the geometry and assert on it, measure pixels rather than judging
colour, assert that string replacements matched before trusting them.

## 10. RealityKit does not expand a USD `PointInstancer`

The obvious way to batch ~2,400 repeated village modules is a `PointInstancer`
per module type: one prim carrying `positions`, `orientations` and `protoIndices`,
pointing at a prototype. `usdcat` accepts it, `realitytool compile` accepts it,
and `usdrecord` renders the town correctly.

RealityKit ignores it. Measured on visionOS 26.5 by walking the loaded entity
tree: all 21 instancer prims were present, but they produced only 19 mesh
entities, with combined bounds of ±5.7 m centred on the origin — the prototypes,
loaded once each, with every placement discarded. The whole village would have
collapsed into a heap in the middle of the study.

This is the same trap as `doubleSided` and the Display P3 textures: the offline
tools are more permissive than RealityKit, so *an offline render proves nothing*.
The check that actually settled it was numeric, from inside the running app:

```swift
// count mesh entities under the town prims, and their world bounds
let b = e.visualBounds(relativeTo: nil)
```

Batching therefore has to happen ahead of time. `tools/merge_town.py` joins each
building into a single mesh in Blender — see
[`../decisions/DECISIONS.md`](../decisions/DECISIONS.md) for why it is per
building rather than per module type.

## 11. Blender's glTF importer duplicates materials and UV sets on every import

Importing 20 kit modules separately gives 20 private copies of every shared
material (`MI_Plaster`, `MI_Plaster.001`, …) and UV layers whose names can
differ per import. Joining the objects preserves all of them, so a merged
building ends up with 12 material subsets where 7 would do, plus two identical
UV sets — extra draw calls and file size for nothing.

Fold them together *before* joining: rename every `uv_layers` entry to a single
name, and remap each material slot to the first material sharing its base name
(`re.sub(r"\.\d+$", "", name)`). On this town that cut 12 subsets per house to 7
and the baked output from 72 MB to 63 MB.

## 12. `TextureResource(named:in:)` only reads asset catalogs

The sky images live as loose `.jpg` files in the bundle, so
`TextureResource(named: "sky_night", in: realityKitContentBundle)` fails with
"Could not get asset catalog from supplied bundle" — the same trap as
`UIImage(named:)` in note 4, and it fails at runtime rather than at build time.

Resolve the URL and build the texture from a `CGImage` instead:

```swift
guard let url = Bundle.main.url(forResource: name, withExtension: "jpg"),
      let cg = UIImage(contentsOfFile: url.path)?.cgImage else { return }
let texture = try await TextureResource(image: cg, options: .init(semantic: .color))
```

This surfaced while fixing a related bug: `applySky` set only the *image-based
light*, while the visible skydome kept whatever texture the generator baked into
`TowerShell.usda`. Night therefore relit the room correctly but left a bright
midday sky in the window. The dome is now retextured alongside the IBL in
`LightRig.applySkyDome`.

## 13. A flat emissive disc does not read as a pool of light

The street lamps' light pools started as discs of constant emissive colour. At
distance they read as flat patches of sand, because real light has a falloff and
a constant colour has none.

Two things fixed it: put the falloff in a texture (a 128px radial gradient,
generated by the tool rather than committed as a binary), and set
`diffuseColor = (0, 0, 0)` so the *emission alone* is textured. The disc then
fades to true black at its rim and has no visible edge against the dark ground —
no transparency or blend mode needed, which keeps it a cheap opaque draw.

## 14. `sips -s format jpeg` auto-exposes every HDR independently

The three skies were converted from `.hdr` with `sips -s format jpeg`. That
applies its own tone mapping *per file*, normalising each one to roughly the same
average brightness. Measured on the results:

| sky | mean, auto-exposed | mean, fixed exposure |
|---|---|---|
| day | 106.4 | 106.0 |
| sunset | 106.3 | 79.1 |
| night | **133.1** | 19.1 |

The moonlit night was the *brightest* image of the three, so 2am showed a daylit
horizon through the window. All relative brightness between the skies — the whole
point of having three — had been destroyed at conversion time.

`tools/convert_skies.py` replaces it: Blender loads the linear HDR, applies a
held per-sky exposure, rolls the highlights off with Reinhard rather than
clipping them, and encodes sRGB by hand. `fetch_assets.sh` no longer converts the
skies at all, and says why.

The general trap: a conversion tool that "looks right" on each file separately
can still be wrong across a *set* of files, because it is normalising away
exactly the differences you care about. Compare the set, not each image.

## 15. The same asset in two places will drift

Each sky exists twice: `rkassets/textures/` (baked into the dome's material by
the generator) and `WizardTower/Skies/` (loaded at runtime by `LightRig` to
retexture that dome). Re-exposing only the rkassets copy changed nothing on
screen, because the runtime copy wins — and it silently kept the old bright sky.

`convert_skies.py` now writes both, in a `DESTS` list, rather than leaving it to
whoever runs it next to remember.

## 16. A pixel of an equirectangular sky is a *lot* of sky

The first procedural night sky had stars the size of the moon, and it was not a
bug in the star code — it was resolution. An equirectangular map 1024 pixels wide
covers 360 degrees, so one pixel subtends 0.35 degrees on the dome. The moon
subtends about 0.5. Single-pixel stars were therefore very nearly moon-sized, and
the texture sampler's bilinear filter smeared each one into a soft blob on top.

Anything that should read as a *point* on a sky dome has to be reasoned about in
degrees-per-pixel, not pixels. 2048 wide halves it to 0.18 degrees, and dimming
the stars gives the filter less to smear. The gradient itself would have been
fine at a quarter of that resolution — the stars set the requirement.

The same arithmetic is why the sun disc uses an angular threshold on the angle to
the sun (`gamma < 0.010 rad`) rather than any pixel measure: it stays the right
apparent size whatever the texture resolution.
