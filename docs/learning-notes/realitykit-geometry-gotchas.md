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

## The pattern worth remembering

Every bug here looked like it had been fixed. An edit that did not apply, a flag
that did nothing, a face that rendered fine offline. **Verify numerically, not by
eye** — dump the geometry and assert on it, measure pixels rather than judging
colour, assert that string replacements matched before trusting them.
