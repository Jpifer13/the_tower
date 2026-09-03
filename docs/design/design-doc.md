# The Tower — Design Doc (v1)

> Phase 2 deliverable. Decisions locked 2026-09-03; open questions marked **OPEN**.

> ## ⛔ BLOCKED — the premise below does not work on visionOS
>
> This doc was written around the room being "an office with atmosphere": a backdrop your
> real apps float inside. **That is not possible for a third-party app.** When an app opens
> an `ImmersiveSpace`, visionOS hides every other app — verified empirically, see
> [`../learning-notes/immersive-space-hides-other-apps.md`](../learning-notes/immersive-space-hides-other-apps.md).
>
> Everything about the room's *form* below still stands. What's invalid is its *job*:
> "backdrop for my other apps", "walls host the user's app windows", and pacing around during
> a meeting all assume other apps stay visible. They won't.
>
> **One exception, verified:** with Developer Mode and *Allow Mac Virtual Display* enabled, the
> Mac Virtual Display does persist inside a third-party immersive space. So the office concept
> works for you personally — tower plus Mac desktop plus terminal. It can't be sold on, since
> it needs Developer Mode and covers only the Mac screen, not native visionOS apps.
>
> **Shared Space is not a way around this**: volumes are bounded, so you'd get a diorama in a
> box rather than a room you're inside.
>
> **Do not start Phase 3 shopping until the product direction is re-decided.**

## The room in one paragraph

A circular study at the top of a stone tower — a working office, not a museum piece. You sit
at a desk facing a tall window, with a fire going quietly off to one side and bookshelves
around the curve of the wall. Your real apps float over the desk and hang on the walls. The
weather and the light outside the window match the real world, and so does the sound coming
through it. When you need a break you get up and go look out.

## Core decisions

| Decision | Choice | Rationale |
|---|---|---|
| Rooms in v1 | One circular tower study | Smallest shippable scope; extra rooms are v2 IAPs |
| Primary posture | Seated at the desk, window ahead | App windows land naturally over the desk |
| Secondary posture | **Standing — user can walk to the window** | Explicit requirement; see *Consequences* below |
| Room's job | An office with atmosphere | Backdrop for real work first, ambience second |
| Wall usage | Must accommodate user-placed app windows | Requires deliberate negative space |
| Ceiling height | **OPEN** — 12–15 ft proposed | Towers want height; confirm when sketching |
| Time of day | Real-time sync, with manual override | Manual needed for screenshots and for night owls |

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

1. **The outside view can't be a low-res HDRI.** At 3 m a 2K skybox is fine; pressed against
   the glass it reads as a blurry photo and breaks the illusion. Options, cheapest first:
   a 4K/8K HDRI; a 3D backdrop (a few pieces of geometry — rooftops, treeline — sitting outside
   the window with real parallax); or a hybrid, geometry near and HDRI far. **OPEN** — decide
   in Phase 3, because it changes what you shop for.
2. **Window frame geometry gets inspected.** Sill, mullions and glass will be seen from ~30 cm.
   This is the one place to spend polygons and texture resolution.
3. **Scale errors become obvious.** Seated, you forgive a slightly-wrong room. Walking to a
   window that turns out to be 1.4 m tall is immediately wrong. Block out against a 1.7 m
   reference from the first hour of Phase 4.
4. **Passthrough breakthrough.** visionOS fades passthrough in when someone walks beyond a
   safe boundary. The desk→window walk must be short enough to stay inside it — a few steps,
   not a hike. Something to confirm on device in Phase 6.
5. **The floor matters now.** In a seated design the floor is barely seen. Here it's underfoot
   and in view while walking.

## Design tension to hold

A wizard study wants to be *cluttered* — that's the whole charm. An office wants *clean wall
space* for floating app windows. If the room is dressed evenly, the app windows will sit on
top of visual noise and the space will feel cramped in daily use.

Resolution: concentrate the clutter (shelves, bottles, scrolls) on the flanks and behind the
user; keep the window wall and one side wall deliberately quiet. Detail where you look
occasionally, calm where your work lives.

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
