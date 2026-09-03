# The Tower — Design Doc (v1)

> Phase 2 deliverable. Decisions locked 2026-09-03; open questions marked **OPEN**.

> ## ✅ UNBLOCKED — this is a personal tool first
>
> Direction changed 2026-09-03: The Tower is built for Jake to use, not to sell. An App Store
> release may follow as a stripped-down generic version, but it drives no decisions.
>
> This resolves the constraint that blocked the original premise. A third-party immersive space
> hides all other apps — but **Developer Mode → Allow Mac Virtual Display** lets the Mac Virtual
> Display persist inside it, and enabling that is fine for an audience of one. The office concept
> works: the tower, your Mac desktop, Ghostty, and room to pace.
> Background: [`../learning-notes/immersive-space-hides-other-apps.md`](../learning-notes/immersive-space-hides-other-apps.md).

## The room in one paragraph — the 60-second description

> The top floor of a stone tower, gone slightly to seed as a working office. You sit at a desk
> against the curved wall with your Mac floating over it, a tall window on your right, and a fire
> going quietly on your left. The ceiling is a cone of dark beams climbing to a point six metres
> up, with a lantern hanging from it. Behind you the room opens out — bookshelves round the curve,
> a reading chair, and a railed stair opening that reminds you there are floors below. The weather
> and the light through the window are the real ones outside your house, and so is the sound. When
> a call drags, you get up and pace, or go and lean on the sill.

Read it aloud. If it takes much over a minute, cut it, not the room.

## Core decisions

| Decision | Choice | Rationale |
|---|---|---|
| Rooms in v1 | One circular tower study | Smallest shippable scope; extra rooms are v2 IAPs |
| Primary posture | Seated at the desk, window ahead | App windows land naturally over the desk |
| Secondary posture | **Standing — user can walk to the window** | Explicit requirement; see *Consequences* below |
| Room's job | An office with atmosphere | Backdrop for real work first, ambience second |
| Audience | **Me.** Generic App Store version optional, later | No App Review or onboarding pressure on v1 |
| Work surface | **Mac Virtual Display** (Developer Mode) | The one thing that survives inside an immersive space |
| Wall usage | Must accommodate the Mac display + own panels | Requires deliberate negative space |
| Ceiling | **Conical** — top floor of the tower. Eaves **5.49 m (18 ft)**, apex **9.89 m (32.4 ft)** | Reads unmistakably as a tower top |
| Room diameter | **8.8 m (28.9 ft)** | Widened 60% from 5.5 m — 5.5 felt tight |
| Time of day | Real-time sync, with manual override | Manual needed for screenshots and for night owls |
| Immersion style | **`.mixed`**, with a fully enclosing room | `.full` imposes a 1.5 m safety leash that would break pacing |

## Layout

Derived from the real desk and the real clear floor, not chosen for looks. You sit at the desk
against the tower wall, facing it; the window is to your **right**; the room wraps behind you.

**Real-world measurements this is built around**
- Desk 6 ft × 3 ft (1.83 × 0.91 m), against the wall
- ~1.5 ft (0.46 m) clear each side of the desk
- ~10 ft (3.05 m) clear behind you
- Forward is blocked by the real desk and wall — which is why the virtual desk sits against the
  virtual wall. The real obstacle and the virtual one line up.

**Plan** (north at top; you sit at the south, facing the wall)

```
                        shelves along the curve
                 ╭───────────────────────────────╮
             ╭───╯                                ╰───╮
          ╭──╯    ▨ stair opening                     ╰──╮
        ╭─╯         (railed, perimeter)                  ╰─╮
       │                                                    │
       │      ┌ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐             │
  ▯    │      │                                │        ▩   │
  ▯ W  │      │   WALKABLE ENVELOPE            │       fire │  E
  ▯    │      │   2.7 m wide × 3.0 m deep      │            │
window │      │   = your actual clear floor    │            │
       │      └ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘             │
        ╲─╮                [ chair ]                     ╭─╱
          ╰──╮      ▭▭▭▭▭▭ DESK ▭▭▭▭▭▭            ╭─────╯
             ╰───────────────────────────────────╯
                     you sit here, facing the wall
                            ← 8.8 m across →
```

| Element | Position | Notes |
|---|---|---|
| Desk + you | South, against the wall | Mac Virtual Display floats here, over the desk |
| Window | **West — to your right** | Tall, reachable, lean-out-able. The focal point |
| Fireplace | East — to your left | Peripheral warmth when seated; visible while pacing |
| Shelves | North curve, behind you | Where the clutter goes |
| Stair opening | North-west, at the perimeter | Sells "top floor". Railed, and outside the walking path |

## Sizing the walkable envelope to the real room

Because we're on `.mixed` there's no system boundary — nothing stops you walking into real
furniture. The mitigation is layout, not software:

- The **walkable envelope** (2.7 × 3.0 m) matches your real clear floor. Inside it, the virtual
  floor is empty.
- **Virtual furniture fences the real hazards.** Shelves, a reading chair and the railed stair
  opening sit exactly where your real walls and furniture are, so the instinct not to walk
  through them keeps you inside the safe area. Furniture is doing the job the 1.5 m boundary
  would have done, but without ending the experience.
- The tower is 8.8 m across while your envelope is ~3 m. **That's deliberate** — the room reads
  as full-size, but everything beyond the envelope is furnished rather than open floor.

## Elevation — conical roof

```
                    ▲  apex 9.89 m (32.4 ft)
                   ╱ ╲
                  ╱   ╲        planks radiating to the apex
                 ╱     ╲       (hang the lantern here)
                ╱       ╲
               ╱         ╲
   5.49 m ────┌───────────┐──── eaves / top of wall (18 ft)
              │ ▯         │
              │ ▯         │
              │ ▯ window  │     window 0.4 m → 3.6 m
              │ ▯         │
              │ ▯         │
    0.0 m ────└───────────┘──── floor
              ←── 8.8 m ──→
```

**Roof structure (built):** a wall plate ring where the cone lands on the stone, and a boss at
the apex to hang the lantern from.

**Rafters: tried and cut (2026-09-03).** Twelve radiating beams were built and rejected — from
below they read as a busy starburst and fought the calm the room needs for daily work. The cone
is better plain. The generator still has `prism()` if they're ever wanted back.

- **Eaves at 18 ft** — the room is as tall as it is wide, which is what makes it a tower
  rather than a round room.
- **Apex at 32 ft** keeps a 45° pitch: the cone rises by the radius, so widening the room
  raised the apex automatically.
- **Window head raised to 3.6 m** with the wall. At the original 2.6 m it looked stubby
  against an 18 ft wall.
- The cone is mostly seen when you lean back or stand, so it can be relatively low-detail:
  beams, boarding, and shadow. Don't spend the budget up there.
- A high apex is also somewhere to put the one dramatic light (a hanging lantern) without it
  glaring in your eyes while you work.

## Consequences of the standing requirement

This is the decision with the most technical weight, so it's worth being explicit:

1. **The outside view is a hybrid — decided.** See *Outside the window* below.
2. **Window frame geometry gets inspected.** Sill, mullions and glass will be seen from ~30 cm.
   This is the one place to spend polygons and texture resolution.
3. **Scale errors become obvious.** Seated, you forgive a slightly-wrong room. Walking to a
   window that turns out to be 1.4 m tall is immediately wrong. Block out against a 1.7 m
   reference from the first hour of Phase 4.
4. **The 1.5 m boundary — solved by using `.mixed`.** Full immersion ends the experience if your
   head leaves a 1.5 m radius, which would eject you mid-pace. Mixed immersion has no such leash,
   and an enclosing room occludes passthrough anyway. See
   [`../learning-notes/immersion-style-and-the-15m-boundary.md`](../learning-notes/immersion-style-and-the-15m-boundary.md).
   The trade: nothing will stop you walking into real furniture, so the virtual room must be sized
   to your real clear floor space.
5. **The floor matters now.** In a seated design the floor is barely seen. Here it's underfoot
   and in view while walking.

## What "for me" changes

Dropping the sellable-app goal removes most of the constraints that were shaping v1:

- **Developer Mode is fine.** Mac Virtual Display is the primary work surface, not a footnote.
- **No App Review pressure.** No minimum-functionality argument, privacy labels, reviewer notes,
  onboarding, or "does a stranger understand this in 10 seconds".
- **No ROI maths.** Asset budget is whatever the room is worth to you, not what 2,000 sales justify.
- **WeatherKit can be simpler.** Your location can be a hardcoded default; no permission-priming UX.
- **Customisability becomes a real requirement.** You'll want to keep fiddling with this for years,
  so Phase 5 should keep lighting, audio, time-of-day and props **data-driven** — editable in
  RCP or a config file, not hardcoded in Swift. That's the one thing worth over-engineering.

Two things worth *keeping* even though nothing forces them:

- **Clean asset licences.** Buy commercial-use rights anyway. It's usually the same price and it
  preserves the option to ship a generic version without re-buying everything.
- **Separate personal config from defaults.** So a shippable version is a config swap, not a fork.

## Design tension to hold

A wizard study wants to be *cluttered* — that's the whole charm. An office wants *clean wall
space* for floating app windows. If the room is dressed evenly, the app windows will sit on
top of visual noise and the space will feel cramped in daily use.

Resolution: concentrate the clutter (shelves, bottles, scrolls) on the flanks and behind the
user; keep the window wall and one side wall deliberately quiet. Detail where you look
occasionally, calm where your work lives.

## Outside the window (decided 2026-09-03: hybrid)

Geometry near, HDRI far. Both, not either.

| Distance | Approach | Status |
|---|---|---|
| 0–50 m | **Real geometry** — tower wall dropping away, 2–3 neighbouring rooftops, a tree | **Not built yet** — the parallax half |
| Far / sky | **HDRI** on a skydome | **Built.** Tone-mapped to JPG, unlit, dropped 26 m so you look down on it |

**Why not HDRI alone.** An equirectangular HDRI is treated as infinitely distant, so it never
shifts as you move. Walking to the window would change nothing about the view, which reads as a
photo painted on the sky. Resolution compounds it: a 2K HDRI spreads ~2048 px over 360°, about
6 pixels per degree, against roughly 34 that the headset resolves — some 6× short. Fine as a glow
through a small window across the room; mush at the glass. Matching the display would need
something like a 12K panorama, which is impractical to load.

**Why not geometry alone.** The HDRI is doing image-based lighting regardless, and modelling a
believable sky is wasted effort.

**Nice side effect:** the geometry is lit by whatever sky is active, so time-of-day and weather
transitions come along for free instead of needing three baked variants of the exterior.

**Tower elevation:** the skydome is dropped 26 m below the floor, so the room reads as being
up a tower rather than at ground level. One constant, `TOWER_ELEV`.

**Scope control:** only model the roughly 90° cone visible through the window. Everything behind
the user's back outside the tower does not exist.

**Also unlocks looking *down*** — a tower window you can lean out of. An HDRI handles that badly,
since the horizon-level photo stretches and falls apart underfoot.

## Observation from the first render

Seated, you are 1.26 m from a wall of bare stone that fills your entire view. In practice the
Mac Virtual Display covers most of it, but that makes the wall directly ahead **prime real
estate, not background** — it wants a shelf over the desk, a tapestry, or something to break it
up. Bare stone at arm's length for eight hours would be oppressive.

## Lighting plan

| Source | Type | Colour | Day | Sunset | Night |
|---|---|---|---|---|---|
| Window | Directional + IBL | daylight → warm → cool | key light, cool white | low, strong orange | dim blue moonlight |
| Fireplace | Point, flickering | 1900–2200 K | subtle | prominent | primary warm source |
| Candles (desk + shelves) | Point, flickering | 2000–2400 K | mostly unlit | lit | lit, main task light |
| Lantern (optional) | Point | 2200 K | off | on | on |

Window IBL drives global ambience and swaps with time of day and weather. Fire and candles are
the only real-time lights; everything else bakes. (Phase 4 performance budget.)

## Audio plan

Two sources do the heavy lifting: the window and the fire.

| Source | Sound | Position | Behaviour |
|---|---|---|---|
| Window | Wind, rain, birdsong, distant town | At the window, spatial | **Varies with time of day + weather** |
| Fireplace | Light crackle | At the hearth, spatial | Loop; quiet — "light fire", not a bonfire |
| Room tone | Stone-room ambience | Non-spatial bed | Constant, very low |
| Owl | Distant hoot | Outside the window | Night only, occasional |
| Pages / settling | Book rustle, wood creak | Around the room | Rare, randomised |

Window audio matrix — **the differentiator, alongside the visual weather**:

| | Clear | Rain | Snow | Wind |
|---|---|---|---|---|
| **Day** | birdsong, faint town | rain on glass + gutter | muffled hush | gusts round the tower |
| **Sunset** | evening birds, bells | steady rain | hush | moderate gusts |
| **Night** | owl, crickets, wind | rain, no birds | deep silence | strong gusts, shutter rattle |

Needs crossfades, not hard cuts, on both time-of-day and weather transitions.

## v1 feature list

**Must-have**
- [ ] One fully-realised circular study
- [ ] Ambient audio: fire + window + room tone
- [ ] Time-of-day: day / sunset / night, real-time synced with manual override
- [ ] Walkable desk → window, holding up at close range

**Should-have**
- [ ] WeatherKit on the window — visuals *and* audio
- [ ] Candle relight on tap
- [ ] Data-driven scene config so it stays tweakable without code changes

**Nice-to-have**
- [ ] Fireplace toggle
- [ ] Night fireflies / dust motes in window light

**Explicitly NOT v1** — additional rooms (IAP), Pomodoro tome, owl flyby, crystal ball media player.
Leave physical room on the desk for the Pomodoro object so v2 doesn't require a re-layout.

## Still to do (yours)

- [ ] Sketch the floor plan and elevation on paper; photo into this folder as `floor-plan.jpg`
- [ ] Confirm ceiling height against the sketch
- [ ] 20–30 reference images into `mood-board/` — no branded IP
- [ ] The 60-second description test
