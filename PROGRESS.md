# Progress Tracker

Status: **Phase 1 — learning in progress** (hands-on RCP). **Phase 2 — design agreed.** Phase 3 unblocked.

**Direction (2026-09-03): this is a personal tool, not a product.** App Store is optional and deferred.
Started: 2026-09-03
Target ship: ~14 weekends from start

Legend: `[ ]` todo · `[x]` done · `[-]` skipped/cut

---

## Phase 0 — Foundation (Weekend 1)

- [x] Install Xcode 16+ — **Xcode 26.5** already installed
- [x] Download the visionOS 26.5 simulator runtime (7.3 GB — SDK ships without it)
- [x] Launch Reality Composer Pro — opens `Packages/RealityKitContent/Package.realitycomposerpro`
- [x] Apple Developer signing verified (team `89DJNH7K9F`)
- [x] Install Blender — already installed
- [x] Create visionOS project in `app/` (SwiftUI + RealityKit + RealityKitContent package)
- [x] Run in the visionOS Simulator — control panel window renders
- [x] Full Space verified — immersive space opens and loads `Tower.usda` from the RCP package
- [ ] Read Apple's "Hello World" visionOS sample end-to-end ← *only remaining item, and it's reading*

**Exit criterion:** ✅ Met. App builds, runs, opens a Full Space, and loads Reality Composer Pro content.
Findings recorded in [`docs/learning-notes/visionos-scenes.md`](docs/learning-notes/visionos-scenes.md).

Orientation, links and a Diorama dissection guide: [`docs/learning-notes/phase-1-guide.md`](docs/learning-notes/phase-1-guide.md)

### Prep (staged — run `./reference/fetch.sh` on a fresh clone)
- [x] Diorama sample downloaded → `reference/apple-samples/diorama/`
- [x] Hello World sample downloaded → `reference/apple-samples/hello-world/`
- [x] Practice HDRIs (CC0, day / sunset / moonlit night) → `reference/practice-assets/hdri/`
- [x] Practice USDZ models → `reference/practice-assets/usdz/` (verified they compile via `realitytool`)

### Yours to do
- [ ] Watch [WWDC23 "Meet Reality Composer Pro"](https://developer.apple.com/videos/play/wwdc2023/10083/)
- [ ] Watch [WWDC24 "Create custom environments…"](https://developer.apple.com/videos/play/wwdc2024/10087/) (twice)
- [ ] Watch [WWDC24 "Compose interactive 3D content in RCP"](https://developer.apple.com/videos/play/wwdc2024/10102/)
- [ ] Take apart Diorama in RCP (what to look at: see the guide)
- [ ] Practice: place a USDZ in a fresh RCP scene — check scale against 1.7 m
- [ ] Practice: point light + IBL from an HDRI
- [ ] Practice: particle system — start from a preset, then tune emission + lifetime
- [ ] Practice: spatial audio source, walk the falloff in the Simulator
- [x] Practice: load an RCP scene from Swift — **already proven in Phase 0** (`TowerImmersiveView`)
- [ ] Add your own notes to `docs/learning-notes/`

**Exit criterion:** Asset → lit RCP scene → particles + audio → loads in app. Unblocked, not fast.
**⚠ DECISION GATE 1** — Did RCP click? Record verdict in `docs/decisions/DECISIONS.md`.

Draft: [`docs/design/design-doc.md`](docs/design/design-doc.md)

- [x] Decided: one circular tower study
- [x] Decided: seated at the desk facing the window — **plus standing / walk to the window**
- [x] Interaction surface defined: an office with atmosphere; walls host the user's app windows
- [x] Layout proposal drafted (top-down, in the design doc)
- [x] Lighting plan drafted — window IBL, fire and candles the only real-time lights
- [x] Audio plan drafted — including the time-of-day × weather window matrix
- [x] v1 feature list agreed
- [x] Floor plan + elevation drafted from real measurements (in the design doc)
- [x] Ceiling decided: **conical** — eaves 3.0 m, apex 6.0 m; room 5.5 m across
- [x] Immersion style decided: **`.mixed`** (avoids the 1.5 m full-immersion leash)
- [x] Walkable envelope sized to the real clear floor (2.7 × 3.0 m)
- [x] 60-second description written
- [ ] Sanity-check the plan on paper, and against the real desk — amend anything that feels wrong
- [x] Outside-view approach decided: **hybrid** — geometry near (parallax), HDRI far (sky + lighting)
- [ ] Collect 20–30 reference images into `docs/design/mood-board/`
- [ ] Read the 60-second description aloud — does it describe a room you want to be in?

**Exit criterion:** One-page design doc complete with floor plan, lighting plan, audio plan, feature list.
**⚠ DECISION GATE 2** — Would you use this room daily? Record verdict.

## Phase 3 — Acquire Assets (Weekend 5)

- [ ] Room shell sourced ($50–150 budget)
- [ ] Furniture sourced ($20–80)
- [ ] Props sourced — books, candles, scrolls, bottles, crystal ball, quill ($20–60)
- [ ] Sky HDRIs sourced at **4–8K** — day / sunset / night ($0–30, Poly Haven first)
      *(the 2K ones in `reference/practice-assets/` are for practice and lighting only — too soft at the glass)*
- [ ] **Exterior geometry** sourced — tower wall below the window, 2–3 rooftops, a tree
      *(new, from the hybrid decision; only the ~90° cone visible through the window)* Budget: $20–60
- [ ] Audio sourced — **expanded by the design**: fire, room tone, owl, page rustle, *plus*
      window beds for clear/rain/snow/wind × day/sunset/night (freesound, $0)

- [ ] Every asset has a row in `assets/ASSET_MANIFEST.md`
- [ ] Every asset has a license folder in `assets/licenses/`
- [ ] All FBX/OBJ converted to USDZ via Blender, originals kept in `assets/source/`
- [ ] Every USDZ opens clean in Reality Composer Pro

**Exit criterion:** All assets on disk, licenses filed, everything opens in RCP without errors.
**⚠ DECISION GATE 3** — Assets good enough at acceptable cost? Record verdict.

## Phase 4 — Build the Scene (Weekends 6–8)

> **Started early** — the shell was generated during Phase 3, since it couldn't be bought.

### Week 1: Block out
- [x] Room shell generated (walls, floor, conical roof, rafters, wall plate, apex boss)
- [x] Textured with CC0 PBR sets (grey slate walls, plank floor, plank ceiling)
- [x] 1.7 m reference figure + walkable envelope included in the shell
- [x] Offline preview rendering set up (`usdrecord` + `tools/preview_cameras.usda`)
- [x] Poly budget: **1,178 tris** — 0.24% of the 500K target
- [ ] Room shell placed, scale checked against 1.7 m reference cube
- [ ] Furniture rough-positioned
- [ ] Seated viewpoint entity placed; reviewed from that POV in Simulator

### Week 2: Light it
- [ ] HDRI image-based lighting set up
- [ ] Warm point lights at candles + fireplace (2000–2700 K tints)
- [ ] Directional/spot through window for sun/moon
- [ ] Static lighting baked where possible

### Week 3: Atmosphere
- [ ] Dust motes in window light; fireplace embers; (optional) night fireflies
- [ ] Spatial audio at fireplace, window, room tone — falloffs tuned
- [ ] Materials pass: stone roughness, candle emissives, glassy crystal ball

### Performance budget
- [ ] Scene under ~500K triangles
- [ ] Texture atlases where possible
- [ ] Real-time lights only for flicker sources
- [ ] No frame drops in Simulator on the M3 Ultra (screaming alarm if there are)

**Exit criterion:** From the seat, it feels cozy and inhabited. Loads in < 5 s in Simulator.
**⚠ DECISION GATE 4 (most important)** — A place, or a Unity demo? Record verdict.

## Phase 5 — App Code (Weekends 9–10)

- [ ] RCP scene loads into ImmersiveSpace
- [ ] Settings panel (SwiftUI window): immersion level, ambient volume, light/dark
- [ ] Time-of-day system: HDRI swap + light color/intensity (manual + real-time sync)
- [ ] WeatherKit: fetch conditions, swap window HDRI + weather particles
- [ ] Tap interactions: candle relight, fireplace toggle
- [ ] `NSLocationWhenInUseUsageDescription` in Info.plist
- [ ] WeatherKit capability enabled on App ID + in Signing & Capabilities

**Exit criterion:** Scene + settings + time-of-day + WeatherKit response + one tap interaction, all working in Simulator.

## Phase 6 — Real Device Testing (Weekend 11)

> ⚠ **Now a hard prerequisite, not a test step.** A personal daily-use tool needs a headset you
> own. A Developer Lab visit no longer covers it. Decide early — it changes when this is usable.

- [ ] **Vision Pro acquired** (used ~$2.5–3K) — blocking for daily use
- [ ] Developer Mode + *Allow Mac Virtual Display* enabled (Settings → Privacy & Security, then Developer)
- [ ] Run the full checklist in `testing/device-test-checklist.md`
- [ ] Punch-list written and prioritized in `testing/`

**Exit criterion:** Tested on hardware, no critical issues, honest punch-list.
**⚠ DECISION GATE 5** — Any structural rework needed? Record verdict.

## Phase 7 — Polish & Submit (Weekends 12–14) — **OPTIONAL / DEFERRED**

> No longer the goal. Revisit only if you want a generic version on the App Store.
> Everything below still applies if you do.


- [ ] Every punch-list item addressed or consciously cut
- [ ] Audio levels re-tuned for headset
- [ ] 10 cold-launch walkthroughs; confusion moments fixed
- [ ] App Store metadata finalized (`marketing/app-store/metadata.md`)
- [ ] Screenshots captured (times of day, weather, floating app windows)
- [ ] Preview video produced (15–30 s)
- [ ] Icon done (1024×1024)
- [ ] Price set to $9.99; Small Business Program enrolled; tax/banking confirmed
- [ ] Reviewer notes + privacy labels written
- [ ] Archive → upload → submit
- [ ] **LIVE ON THE APP STORE** 🎉

## Launch week

- [ ] Post to r/VisionPro, r/AppleVisionPro, MacRumors forums (preview video, not text walls)
- [ ] Email 5 visionOS writers — one paragraph + preview link each
- [ ] Social posts with preview video
- [ ] Submit "Tell us about your app" for editorial consideration

## Post-launch (first month)

- [ ] Respond to every review under 4 stars
- [ ] Track sales (daily × 2 weeks, then weekly)
- [ ] Crash fixes shipped within a week if needed
- [ ] No new features until stable
