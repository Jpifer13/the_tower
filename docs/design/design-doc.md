# The Tower — Design Doc (v1)

> Phase 2 deliverable. Keep this to one page. If you can't describe the room in 60 seconds from this doc, it's not done.

## The room in one paragraph

_(Write this last. What is it, who sits in it, why does it feel good to be there?)_

## Core decisions

| Decision | Choice | Rationale |
|---|---|---|
| Rooms in v1 | 1 — circular tower study _(recommended)_ | Shippable scope |
| Posture | Seated / Standing | |
| Optimal viewing position | | |
| Ceiling height | 12–15 ft target: ___ | Towers want height |
| Interaction surface | | What does the user actually *do*? |

## Floor plan

_(Photo or scan of the paper sketch goes here — save as `floor-plan.jpg` in this folder.)_

- User seat position:
- Window position:
- Desk position:
- Shelves:
- Fireplace:
- Door:

## Lighting plan

> Lighting is 60% of what makes the space feel real.

| Source | Type | Color/temp | Day | Sunset | Night |
|---|---|---|---|---|---|
| Window | Directional + IBL | | sun | golden | moon |
| Fireplace | Point, flicker | 2000–2700 K | | | |
| Candles (×__) | Point, flicker | 2000–2700 K | | | |
| Lanterns | | | | | |

## Audio plan

| Source | Sound | Position | Loop/one-shot | Falloff notes |
|---|---|---|---|---|
| Window | Wind | | loop | |
| Fireplace | Crackle | | loop | |
| Ambient | Room tone | non-spatial? | loop | |
| Owl | Distant hoot | outside window | occasional | |
| Books | Page rustle | | occasional | |

## v1 feature list

**Must-have**
- [ ] One fully-realized room
- [ ] Ambient audio
- [ ] Time-of-day toggle (day / sunset / night)

**Should-have**
- [ ] WeatherKit on the window
- [ ] Candle relight tap

**Nice-to-have**
- [ ] Fireplace toggle
- [ ] Floating candles with drift
- [ ] Night fireflies

**Explicitly NOT in v1** (v2 candidates — do not build now)
- Additional rooms (IAPs), Pomodoro tome, owl flyby, crystal ball media player

## Mood board

20–30 reference images in [`mood-board/`](mood-board/). Themes: wizard towers, alchemist studies, old libraries. **Nothing derivative of branded IP** (Hogwarts, Skyrim, LOTR, D&D).
