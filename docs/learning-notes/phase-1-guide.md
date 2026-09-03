# Phase 1 — Reality Composer Pro: orientation

Everything below is prep. The actual learning is yours: RCP is a direct-manipulation
tool and the skill lives in your hands, not in a doc. Decision Gate 1 asks whether RCP
*clicked* for you — that only means something if you drove it.

## What's already staged

| Thing | Where | Notes |
|---|---|---|
| Diorama sample | `reference/apple-samples/diorama/` | The canonical "real shipped RCP scene" |
| Hello World sample | `reference/apple-samples/hello-world/` | Phase 0's remaining reading task |
| Day HDRI | `reference/practice-assets/hdri/kloofendal_38d_partly_cloudy.hdr` | CC0, Poly Haven, 2K |
| Sunset HDRI | `reference/practice-assets/hdri/rogland_sunset.hdr` | CC0, Poly Haven, 2K |
| Night HDRI | `reference/practice-assets/hdri/rogland_moonlit_night.hdr` | CC0 — moonlit, ideal for the tower window |
| Practice USDZ | `reference/practice-assets/usdz/` | teapot, stratocaster, robot — Apple gallery |

The USDZ files are verified to compile through `realitytool`, so if one fails to load in
RCP the problem is the scene, not the asset.

`reference/apple-samples/` is ~1 GB and is gitignored. The practice assets are small and
CC0, so they're committed.

## Watch order

1. [Meet Reality Composer Pro (WWDC23)](https://developer.apple.com/videos/play/wwdc2023/10083/) — 25 min orientation. Watch first.
2. [Create custom environments for your immersive apps in visionOS (WWDC24)](https://developer.apple.com/videos/play/wwdc2024/10087/) — **the** session for this project. Covers the Blender → RCP export path, lighting and texture baking, and keeping assets light. Watch twice.
3. [Compose interactive 3D content in Reality Composer Pro (WWDC24)](https://developer.apple.com/videos/play/wwdc2024/10102/) — Timelines, entity hierarchy, environment authoring and lighting.

Two the plan doesn't list but that map directly onto later phases:

- [Enhance your spatial computing app with RealityKit audio (WWDC24)](https://developer.apple.com/videos/play/wwdc2024/111801/) — Phase 4's audio work is exactly this.
- [Optimize your 3D assets for spatial computing (WWDC24)](https://developer.apple.com/videos/play/wwdc2024/10186/) — how to actually hit the ~500K triangle budget.

## Taking Diorama apart

Open `reference/apple-samples/diorama/Packages/RealityKitContent/Package.realitycomposerpro`
in Reality Composer Pro. The scene is `DioramaAssembled.usda` (~1000 lines).

Worth finding in the RCP hierarchy, because each is a technique you need:

- **`OceanAudioEmitter` / `ForestAudioEmitter`** — `RealityKit.AmbientAudio` components paired
  with `RealityKitAudioFile` prims pointing at `.wav` files. This is the pattern for your
  fireplace, wind, and room tone.
- **`Birds`** — spatial (not ambient) audio: `RealityKit.SpatialAudio` with a `directivityFocus`,
  plus an audio *group* so it can pick between several bird calls. Your owl wants this.
- **`Clouds`** — how multiple instances of one asset get placed and varied.
- **`Materials.usda`** (~1250 lines) — a MaterialX shader graph. Don't try to read it as text;
  open it in RCP's node editor. This is what "make the crystal ball look glassy" turns into.
- **Custom components** in `Packages/RealityKitContent/Sources/RealityKitContent/*.swift`
  (`PointOfInterestComponent`, `TrailComponent`, `BillboardSystem`) — how Swift-side components
  attach to RCP entities. Phase 5 uses this for candle-tap and fireplace state.

## The practice tasks, and where they live in RCP

The plan's five hands-on tasks, with the part that isn't obvious:

1. **Drop a USDZ into a scene** — drag from Finder into the RCP hierarchy. Check the scale
   against a 1.7 m reference immediately; Apple gallery models are real-world scale but
   purchased assets very often aren't.
2. **Point light + IBL** — lights are added via the **+** button in the hierarchy, not the
   inspector. For IBL you need an `ImageBasedLight` component and an HDRI; use the moonlit
   night one to see it clearly, since a bright day HDRI hides everything else.
3. **Particle system** — add an emitter, then start with the *presets* (Sparks, Impact, Magic)
   before touching individual values. Emission rate and lifetime are the two that matter first.
4. **Spatial audio** — add the audio file to the project, then an audio component on an entity.
   The falloff only makes sense in the simulator with headphones; the RCP preview won't sell it.
5. **Export and load from Swift** — **already proven in Phase 0.** `TowerImmersiveView` loads
   `Tower.usda` from the package, so anything you save into `RealityKitContent.rkassets` shows
   up by changing the name in `Entity(named:)`.

## One thing I checked so you don't have to

I searched both Apple samples for text-authored lights, image-based lighting, and particle
emitters: there are none. Diorama's lighting is baked into its materials. So these are
genuinely GUI-authored in RCP, and there's no reference USDA to copy from — which is why
this phase is hands-on-the-tool rather than something that can be scaffolded in code.

Audio is the exception, and `Bird_With_Audio.usda` is a clean, short example if you want to
see what RCP writes.
