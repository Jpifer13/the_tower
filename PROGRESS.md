# Progress Tracker

Status: **Phase 0 — not started**
Started: —
Target ship: ~14 weekends from start

Legend: `[ ]` todo · `[x]` done · `[-]` skipped/cut

---

## Phase 0 — Foundation (Weekend 1)

- [ ] Install Xcode 16+ from Mac App Store
- [ ] Launch Reality Composer Pro once (Xcode → Open Developer Tool)
- [ ] Sign in to Apple Developer account in Xcode → Settings → Accounts
- [ ] Install Blender (for FBX/OBJ → USDZ conversion later)
- [ ] Create visionOS project in `app/` (SwiftUI + RealityKit, Volume initial scene)
- [ ] Run default project in visionOS Simulator
- [ ] Switch initial scene to Full Space and re-run
- [ ] Read Apple's "Hello World" visionOS sample end-to-end

**Exit criterion:** Can launch the Simulator, navigate an immersive scene, and explain what an ImmersiveSpace is.

## Phase 1 — Learn Reality Composer Pro (Weekends 2–3)

- [ ] Watch WWDC23 "Meet Reality Composer Pro"
- [ ] Watch WWDC24 "Create custom environments for your immersive apps" (twice)
- [ ] Watch WWDC24 "Compose interactive 3D content in Reality Composer Pro"
- [ ] Take apart Apple's "Diorama" sample in RCP
- [ ] Practice: place a free USDZ asset in a fresh RCP scene
- [ ] Practice: add point light + IBL from a Poly Haven HDRI
- [ ] Practice: particle system (Sparks) — tune emission, lifetime, color
- [ ] Practice: spatial audio source, walk the falloff in the Simulator
- [ ] Practice: export RCP package, load it from Swift in the Phase 0 app
- [ ] Notes captured in `docs/learning-notes/`

**Exit criterion:** Asset → lit RCP scene → particles + audio → loads in app. Unblocked, not fast.
**⚠ DECISION GATE 1** — Did RCP click? Record verdict in `docs/decisions/DECISIONS.md`.

## Phase 2 — Design the Tower (Weekend 4)

- [ ] Decide: single room (recommended) vs multi-room
- [ ] Decide: seated vs standing optimal position
- [ ] Define the interaction surface (what does the user *do*?)
- [ ] Draw top-down floor plan (photo/scan into `docs/design/`)
- [ ] Draw elevation with ceiling height (12–15 ft)
- [ ] Mark every light source on the plan
- [ ] Mark every audio source on the plan
- [ ] Collect 20–30 reference images into `docs/design/mood-board/`
- [ ] Fill out `docs/design/design-doc.md` including v1 feature list
- [ ] 60-second room description test — can you describe it cold?

**Exit criterion:** One-page design doc complete with floor plan, lighting plan, audio plan, feature list.
**⚠ DECISION GATE 2** — Would you use this room daily? Record verdict.

## Phase 3 — Acquire Assets (Weekend 5)

- [ ] Room shell sourced ($50–150 budget)
- [ ] Furniture sourced ($20–80)
- [ ] Props sourced — books, candles, scrolls, bottles, crystal ball, quill ($20–60)
- [ ] Window view HDRI(s) sourced — day / sunset / night ($0–30, Poly Haven first)
- [ ] Audio sourced — fire, wind, owl, page rustle, room tone (freesound, $0)
- [ ] Every asset has a row in `assets/ASSET_MANIFEST.md`
- [ ] Every asset has a license folder in `assets/licenses/`
- [ ] All FBX/OBJ converted to USDZ via Blender, originals kept in `assets/source/`
- [ ] Every USDZ opens clean in Reality Composer Pro

**Exit criterion:** All assets on disk, licenses filed, everything opens in RCP without errors.
**⚠ DECISION GATE 3** — Assets good enough at acceptable cost? Record verdict.

## Phase 4 — Build the Scene (Weekends 6–8)

### Week 1: Block out
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

- [ ] Device access arranged (Developer Lab booked / unit bought or borrowed)
- [ ] Run the full checklist in `testing/device-test-checklist.md`
- [ ] Punch-list written and prioritized in `testing/`

**Exit criterion:** Tested on hardware, no critical issues, honest punch-list.
**⚠ DECISION GATE 5** — Any structural rework needed? Record verdict.

## Phase 7 — Polish & Submit (Weekends 12–14)

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
