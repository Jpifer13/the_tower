# Wizard Tower visionOS App: Zero-to-Shipped Build Plan

## Overview

This is an end-to-end plan for building and shipping a wizard-themed immersive environment app for Apple Vision Pro, starting from zero 3D modeling experience and no familiarity with the visionOS toolchain. The plan assumes you already have an Apple Developer account, a Mac Studio M3 Ultra, and intend to ship to the App Store at $9.99.

The plan is structured in eight phases over an estimated 10–14 weekends of part-time work. Each phase has a clear goal, a list of tasks, the tools you will install or learn, the cost involved, and an exit criterion that tells you it is safe to move to the next phase.

**Total estimated cost:** $150–$400 in 3D assets, plus optional Apple Developer Lab travel and an eventual Vision Pro purchase or rental for final testing. Apple Developer membership you already have.

**Total estimated revenue at $9.99:** $17K–$85K gross over a couple of years for a well-executed niche cozy app, with App Store taking 15% under the Small Business Program.

---

## Phase 0: Foundation (Weekend 1)

**Goal:** Get every tool installed, run the visionOS Simulator, and ship a "Hello World" immersive scene to confirm your environment works before investing time in content.

### Install

- **Xcode 16 or later:** Free from the Mac App Store. ~10GB. Includes the visionOS SDK, Simulator, Reality Composer Pro, and all build tooling.
- **Reality Composer Pro:** Bundled with Xcode. Open it once via Xcode → Open Developer Tool → Reality Composer Pro to confirm it launches.
- **Apple Developer Account:** Already done. Sign in via Xcode → Settings → Accounts so signing works.
- **(Optional) Blender:** Free at blender.org. You won't model in it, but you'll occasionally need it to convert FBX/OBJ assets to USDZ. Install it now to avoid friction later.

### Tasks

1. Open Xcode, create a new project: visionOS → App → SwiftUI + RealityKit, Initial Scene: Volume.
2. Run it in the visionOS Simulator (top toolbar: select "Apple Vision Pro" as the destination, hit play). You should see a default sphere floating in space.
3. Modify Initial Scene to be "Full Space" (in your project's Info.plist, change the preferred default scene). Re-run.
4. Read Apple's "Hello World" visionOS sample project end-to-end. It demonstrates ImmersiveSpace, RealityView, and asset loading patterns you will use directly.

### Exit criterion

You can launch the visionOS Simulator from Xcode, navigate around an immersive scene with the on-screen controls, and you understand what an ImmersiveSpace is at a conceptual level.

---

## Phase 1: Learn Reality Composer Pro (Weekends 2–3)

**Goal:** Get comfortable with Reality Composer Pro (RCP) — Apple's drag-and-drop scene editor — so that when assets arrive in Phase 3 you can actually assemble them.

### Resources (in order)

1. WWDC23: "Meet Reality Composer Pro" — 25 min overview. Watch this first.
2. WWDC24: "Create custom environments for your immersive apps in visionOS" — the canonical guide for exactly what you're building. Watch twice.
3. WWDC24: "Compose interactive 3D content in Reality Composer Pro" — covers entity hierarchy, materials, particle systems.
4. Apple's "Diorama" sample project — open it in RCP, take it apart, see how a real shipped scene is structured.

### Hands-on practice

- Drop a free USDZ asset (Apple has a gallery at developer.apple.com/augmented-reality/quick-look) into a fresh RCP scene.
- Add a point light and an image-based light (IBL) using a free HDRI from Poly Haven.
- Apply a particle system (built-in "Sparks" is a good start) and adjust emission rate, lifetime, color.
- Add a spatial audio source with a free ambient sound from freesound.org. Walk around it in the simulator and hear the falloff.
- Export the RCP package and load it from Swift code in your Phase 0 project.

### Exit criterion

You can take a USDZ asset, place it in an RCP scene, light it convincingly, add a particle effect and ambient audio, and load the result in your visionOS app. You don't need to be fast — you need to be unblocked.

---

## Phase 2: Design the Tower (Weekend 4)

**Goal:** Lock down what you're actually building before you spend money on assets. This is the cheapest phase to change your mind.

### Define the experience

- Single room or multi-room? Recommended: start with one room (a circular tower study) for v1 to keep scope shippable.
- Seated or standing? Vision Pro environments are typically designed for a seated optimal viewing position. Pick one.
- What does the user actually do? Just sit and work with their other apps floating in the room? Tap candles to relight? Toggle the fireplace? Define the interaction surface.

### Sketch the room (literally, on paper)

- Draw a top-down floor plan. Mark where the user sits, where the window is, where the desk is, where shelves go.
- Draw an elevation showing ceiling height. Tower studies want height — 12–15 feet feels right.
- Mark every light source: window (sunlight/moonlight), candles, fireplace, lanterns. Lighting sells the space more than geometry does.
- Mark every audio source: wind through the window, fire crackle, distant owl, occasional book-page-rustle.

### Pinterest / mood board

Spend an hour collecting 20–30 reference images of wizard towers, alchemist studies, and old libraries. Save them. You will reference these constantly when shopping for assets and lighting the scene.

### Define the v1 feature list

- **Must-have:** One fully-realized room. Ambient audio. Time-of-day toggle (day/sunset/night).
- **Should-have:** WeatherKit integration on the window. Candle relight tap interaction.
- **Nice-to-have:** Fireplace toggle. Floating candles with subtle drift. Particle-system fireflies at night.
- **v2 (don't build now):** Additional rooms as IAPs. Pomodoro timer book. Owl flyby. Crystal ball as media player.

### Exit criterion

You have a one-page design doc with floor plan sketch, lighting plan, audio plan, and feature list. You can describe the room to someone in 60 seconds.

---

## Phase 3: Acquire Assets (Weekend 5)

**Goal:** Buy or download every 3D asset, audio file, and HDRI you'll need, with clean commercial licenses.

### Where to shop

- **Fab (fab.com):** Epic's unified marketplace. Combines former Quixel + Unreal Marketplace + Sketchfab partners. Check first — pricing is competitive and licenses are clear.
- **Kitbash3D:** Premium quality fantasy/medieval kits at $150–$400. Their "Forgotten City" or similar packs are gorgeous. Worth it if budget allows.
- **Sketchfab:** Wide range, $5–$100. Filter by "Downloadable" and "Commercial use allowed".
- **Unity Asset Store / Unreal Marketplace:** Lots of fantasy interior packs $20–$100. Most are FBX which converts to USDZ via Blender.
- **CGTrader / TurboSquid:** Older, deeper catalogs. Read reviews carefully.
- **Poly Haven (free):** HDRIs for skybox/IBL lighting and PBR textures. CC0 licensed.
- **Freesound (free):** Ambient audio. Filter for CC0 or attribution-only licenses.

### Shopping list

1. Room shell: walls, floor, ceiling, window frame, door. Often part of a larger "wizard study" or "alchemist room" bundle. Budget: $50–$150.
2. Furniture: desk, chair, bookshelves, fireplace. Sometimes in the same bundle. Budget: $20–$80.
3. Props: books (lots), candles, scrolls, potion bottles, crystal ball, quill, ink pot. Budget: $20–$60.
4. Outside view: HDRI or 3D backdrop visible through the window. Budget: $0–$30 (Poly Haven covers this for free).
5. Audio: fire crackle, wind, distant owl, page rustle, ambient room tone. Budget: $0 (freesound).

### CRITICAL: License hygiene

- For every asset, save a folder with: the asset file, the receipt/download confirmation, a copy of the license terms (PDF or screenshot of the license page on the date of purchase).
- Verify each license explicitly allows: commercial use, embedding in a software product, no per-unit royalty, no attribution required (or you're willing to add a credits screen).
- Reject anything labeled "editorial only", "personal use only", or "rendering only".
- Avoid anything visually derivative of branded IP (Hogwarts, Skyrim, LOTR towers, D&D specific properties). Generic medieval/fantasy is safe.
- Avoid AI-generated 3D assets for this project. License status is murky and quality is generally not there for hero environments yet.

### Exit criterion

Every asset for the room is on disk, licenses are filed in a "licenses" folder per asset, and you can open each USDZ/USD in Reality Composer Pro without errors. FBX/OBJ assets have been converted to USDZ via Blender's File → Export → USDZ option.

---

## Phase 4: Build the Scene (Weekends 6–8)

**Goal:** Assemble the room in Reality Composer Pro until it feels like a place, not a pile of objects.

### Week 1: Block out

- Drop in the room shell. Set scale — measure against a 1.7m human reference cube. Wizard towers can feel wrong fast if scale is off.
- Place furniture in rough positions. Don't worry about polish.
- Add the user's seated viewpoint as an empty entity. Walk around in the simulator from that POV constantly. The room only matters from where the user actually sits.

### Week 2: Light it

- Set up an HDRI for image-based lighting (drives global ambient light from the window).
- Add point lights for each candle and the fireplace. Use warm color temperatures (2000K–2700K range, expressed as orange-yellow tints).
- Add a directional light or spotlight through the window for sun/moon.
- Bake lighting where possible (covered in the WWDC24 environment session) for performance.
- Lighting is 60% of what makes a space feel real. Spend disproportionate time here.

### Week 3: Atmosphere

- Particle systems: dust motes in window light, fireplace embers, optional fireflies for night mode.
- Audio: place spatial audio sources at the fireplace, window (wind), and one ambient room-tone source. Tune falloff distances.
- Materials: bump up roughness on stone, add subtle emissive on candle flames, make the crystal ball actually refract or at least look glassy.

### Performance budget (from WWDC24 guidelines)

- Keep total scene under ~500K triangles for headroom.
- Texture atlases over individual textures wherever possible.
- Bake static lighting to lightmaps; use real-time lights only for things that need to flicker (fire, candles).
- Test on Simulator throughout. Frame drops on the M3 Ultra simulator are a screaming alarm — the device is much weaker.

### Exit criterion

From the user's seated viewpoint, the room feels cozy and inhabited. Lighting reads convincingly. Particles and audio are subtle but present. Scene loads in under 5 seconds in the simulator.

---

## Phase 5: App Code (Weekends 9–10)

**Goal:** Wrap the scene in a real visionOS app with the features from your design doc. This is the easy part for you given your background.

### Architecture

- SwiftUI for all UI.
- RealityKit + RealityView for 3D scene loading and updates.
- ImmersiveSpace for the full-immersion mode that replaces the system Environment.
- ObservableObject or @Observable model holding app state: time-of-day, weather, fire-on/off.
- WeatherKit for live weather (declarative API, ~50–100 lines to integrate).

### Feature implementation order

1. Load the RCP scene into ImmersiveSpace and confirm it renders correctly on-device.
2. Add a simple settings panel (a SwiftUI window floating in the room) for: immersion level, ambient volume, light/dark.
3. Time-of-day system: swap HDRI and adjust light colors/intensities based on a time setting (manual or synced to real time).
4. WeatherKit integration: fetch current conditions for the user's location, swap the window-view HDRI and outdoor particle system (rain/snow/clear) to match.
5. Tap interactions: candles relight on tap (RealityKit gestures), fireplace toggles.

### Required Apple permissions

- Location (for WeatherKit). Add `NSLocationWhenInUseUsageDescription` to Info.plist with a friendly explanation: "Wizard Tower uses your location to match your tower's weather to the real world."
- WeatherKit capability must be enabled in your App ID on developer.apple.com and in Xcode's Signing & Capabilities tab.

### Exit criterion

App launches in the simulator, shows the immersive scene, has a working settings panel, time-of-day toggle works, WeatherKit returns data and the scene responds to it (even if simulated weather), and at least one tap interaction works.

---

## Phase 6: Test on a Real Vision Pro (Weekend 11)

**Goal:** Get the build on actual hardware before shipping. The simulator hides too many problems for a 3D environment app.

### Options for device access

- **Apple Developer Labs (recommended):** Free, in-person sessions at Apple offices in Cupertino, NYC, London, Tokyo, Shanghai, Singapore, Munich. Bring your build, work alongside Apple engineers, get a Vision Pro for the day. Book at developer.apple.com/events.
- **Buy used:** Used Vision Pro units have come down to roughly $2,500–$3,000. If you're committed to shipping, this pays for itself.
- **Borrow:** Any developer or content-creator friend with one. A two-hour session catches the worst issues.

### What to test that the simulator can't show you

- Scale and presence: does the room feel cozy, cavernous, or claustrophobic? Adjust ceiling height and furniture proportions accordingly.
- Comfort: any motion or flicker that causes discomfort? Particle density, candle flicker rate, sudden lighting changes.
- Performance: target 90 FPS, no stutters. The Vision Pro's M2 chip is meaningfully weaker than your M3 Ultra. Reduce poly counts or texture sizes if needed.
- UI ergonomics: are tap targets the right size? Are they where eyes actually land?
- Immersion levels: does the scene look right at 25%, 50%, 75%, 100% immersion?
- Passthrough blending: at partial immersion, does the scene blend cleanly with the user's real room?

### Exit criterion

Tested on real hardware, no critical issues, comfort is good, performance hits target. You have a punch-list of polish items and can prioritize them honestly.

---

## Phase 7: Polish & Submit (Weekends 12–14)

**Goal:** Ship it.

### Polish from device feedback

- Address every comfort/scale/performance issue from Phase 6.
- Tune audio levels — what sounded right in headphones at your desk often needs adjustment in the headset.
- Walk through the app from cold-launch as a new user 10 times. Note every moment of confusion.

### App Store assets

- App name: clear and searchable. "Wizard Tower: Cozy Focus Space" or similar — front-load keywords.
- Subtitle: one line on what it is.
- Description: lead with what makes it different (live weather, time-of-day sync). Don't oversell.
- Screenshots: required for visionOS. Capture from the simulator at the correct resolution; show the room at different times of day, with weather, with windows for other apps floating in it.
- Preview video (highly recommended): 15–30 seconds of the room, transitioning through times of day and weather. Worth its weight in gold for an immersive app.
- Icon: 1024x1024. Hire someone on Fiverr ($50–$150) if design isn't your strength.
- Keywords: visionOS, ambient, focus, cozy, weather, immersive, wizard, fantasy.

### Pricing & business setup

- Set price to $9.99 for launch.
- Enroll in the App Store Small Business Program in App Store Connect. Drops Apple's cut from 30% to 15% if you make under $1M/year in App Store revenue. Trivial paperwork.
- Set up tax and banking info in App Store Connect if not already done for Pixelum.

### App Review preparation

- Demo build: the reviewer will run it on real hardware. Make sure first-launch experience works without any setup.
- Reviewer notes: explain what the app does in 2–3 sentences. Mention WeatherKit usage. Mention that the app is an immersive environment, not a game.
- Privacy nutrition labels: declare location use (WeatherKit), no tracking, no data collection.
- Common rejection reasons to preempt: "minimum functionality" (counter: live WeatherKit, time-of-day, multiple interactions = clearly an app, not a single static asset). Misleading screenshots (counter: take them honestly from the actual app).

### Submit

1. Archive build in Xcode → upload to App Store Connect.
2. Fill in all metadata, upload screenshots and preview video.
3. Submit for review. Typical review time: 24–72 hours for visionOS apps.
4. If rejected, read the rejection carefully, fix, resubmit. Most rejections are minor metadata issues or missing reviewer info.

### Exit criterion

App is live on the App Store. You can buy it on a real Vision Pro from a real account.

---

## Launch & Beyond

### Launch week

- Post on r/VisionPro, r/AppleVisionPro, MacRumors forums, indie game/app communities. Share the preview video, not a wall of text.
- Email the writers covering visionOS at The Verge, 9to5Mac, MacRumors, MacStories, iMore. One paragraph + preview link. Don't pitch — just show. Pick 5 writers, not 50.
- Tweet/post on every social channel with the preview video.
- Submit to App Store editorial via the "Tell us about your app" form in App Store Connect. Feature placement is the single biggest revenue lever on visionOS.

### Post-launch (first month)

- Watch reviews carefully. Respond to every review under 4 stars with a fix or a thank-you.
- Track sales daily for the first two weeks, then weekly.
- Fix any crashes immediately — push 1.0.1 within a week if needed.
- Don't add features yet. Stabilize first.

### v2 roadmap (if v1 sells)

- **Additional rooms as IAPs at $2.99–$4.99:** Library, alchemy lab, observatory tower top. Each is roughly 3–4 weekends with the pipeline you've now built.
- **Pomodoro timer integration:** Focus session tied to a floating tome that turns pages. Useful + thematic.
- **Crystal ball as media widget:** Mirror video from Mac via AirPlay, or surface an ambient slideshow.
- **Seasonal content:** Halloween edition (jack-o-lanterns, fog), winter (snow on the window, holly), free or paid.

### Realistic outcome

If you ship a polished v1 with good screenshots and the WeatherKit integration as the differentiator, expect 2,000–10,000 sales over 18–24 months. At $9.99 with the 15% Small Business Program rate, that's roughly $17K–$85K gross. Not a quit-Pixelum number — but a fun, profitable side project that pays for the headset many times over and serves as a strong portfolio piece if you ever want to do more visionOS work.

The bigger upside is option value: "the wizard tower app" is exactly the kind of thing that gets featured in App Store editorial and written up in tech press, which compounds into reach far beyond direct revenue.

---

## Timeline Summary

| Phase | Weekends | Focus |
|-------|----------|-------|
| Phase 0 — Foundation | 1 | Install tools, run Hello World |
| Phase 1 — Learn Reality Composer Pro | 2–3 | Tutorials and hands-on practice |
| Phase 2 — Design the Tower | 4 | Sketch, mood board, feature list |
| Phase 3 — Acquire Assets | 5 | Buy and license-clear all assets |
| Phase 4 — Build the Scene | 6–8 | Block out, light, atmosphere |
| Phase 5 — App Code | 9–10 | SwiftUI + RealityKit + WeatherKit |
| Phase 6 — Real Device Testing | 11 | Apple Developer Lab or used hardware |
| Phase 7 — Polish & Submit | 12–14 | App Store assets, review, ship |

**Total:** 10–14 weekends part-time. Realistic budget given you're working full-time on Pixelum: assume ~16 weeks elapsed, with some slow weeks and some intense ones.

---

## Key Decision Points

Moments where you should stop and re-evaluate before committing more time:

### After Phase 1

Did Reality Composer Pro click for you? If you found it frustrating and slow rather than gratifying, this project may not be the right shape — consider partnering with a 3D artist or scaling scope down to a much simpler scene.

### After Phase 2

Is the design grounded in something you'll actually want to use? If you can't picture yourself working in this room daily for months while building it, the audience won't either. Adjust the design to something genuinely appealing to you specifically.

### After Phase 3

Did you find assets that are good enough at a price you can stomach? If everything you tried felt cheap or expensive packs were out of budget, consider raising the budget, switching themes (an alchemist's lab might have better asset coverage than a wizard tower), or commissioning specific hero pieces.

### After Phase 4

Does the room feel like a place, or like a Unity demo? If it doesn't feel right at this stage, no amount of code in Phase 5 will save it. Fix lighting, audio, and scale here or restart this phase. This is the single most important quality gate.

### After Phase 6

Did the device test reveal fundamental issues? If comfort or performance is bad enough to require structural rework, do the rework before submitting. A bad first impression on visionOS is hard to recover from given the small audience.
