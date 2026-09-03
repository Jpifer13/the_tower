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

## The room in one paragraph

A circular study at the top of a stone tower — a working office, not a museum piece. You sit
at a desk facing a tall window, with a fire going quietly off to one side and bookshelves
around the curve of the wall. Your Mac desktop floats over the desk — terminal, editor,
whatever you're working in — with the tower's own panels beside it. The weather and the light
outside the window match the real world, and so does the sound coming through it. When you
need a break, or you're on a call, you get up and pace, or go look out the window.

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
| Ceiling height | **OPEN** — 12–15 ft proposed | Towers want height; confirm when sketching |
| Time of day | Real-time sync, with manual override | Manual needed for screenshots and for night owls |
| Immersion style | **`.mixed`**, with a fully enclosing room | `.full` imposes a 1.5 m safety leash that would break pacing |

## Layout (proposal — amend on paper)

Top-down, desk at the "south" edge, user facing north toward the window:

```
              ╭─────────────────────╮
          ╭───╯      WINDOW         ╰───╮     ← tall, reachable, the focal point
        ╭─╯    (approach + lean on)     ╰─╮
       │                                  │
       │  shelves                shelves  │
       │                                  │
       │            [ open floor ]        │   ← must be walkable, desk→window
       │                                  │
       │  FIREPLACE              clear    │   ← clear wall = app window real estate
       │   (side)                 wall    │
        ╲                                ╱
         ╲───────╮   DESK    ╭──────────╱     ← user seated here, facing window
                 ╰───────────╯
                      door
```

- **Window**: opposite the desk, floor-to-near-ceiling if the geometry allows. Reachable.
- **Fireplace**: to one side, in peripheral vision when seated — warm light without glare.
- **Clear wall**: at least one uncluttered span at seated eye height for app windows.
- **Open floor**: an unobstructed path desk → window. No rug edges or clutter to walk "through".

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

| Distance | Approach | Why |
|---|---|---|
| 0–50 m | **Real geometry** — tower wall dropping away, 2–3 neighbouring rooftops, a tree | Parallax. This is the whole point |
| Far / sky | **HDRI** (4–8K) or a gradient sky | Cheap, and it's the light source anyway |

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

**Scope control:** only model the roughly 90° cone visible through the window. Everything behind
the user's back outside the tower does not exist.

**Also unlocks looking *down*** — a tower window you can lean out of. An HDRI handles that badly,
since the horizon-level photo stretches and falls apart underfoot.

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
