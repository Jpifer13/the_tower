# Decision Log

Record every go/no-go verdict and any material scope change. Newest at top of each section. The five pre-planned gates are seeded below — fill them in as you hit them.

Format for ad-hoc decisions:

```
## YYYY-MM-DD — Short title
**Context:** …
**Decision:** …
**Why:** …
```

---

## 2026-09-03 — An immersive space hides all other apps

**Context:** The design assumed The Tower would be a backdrop for real work — other apps
floating over the desk and on the walls, usable during meetings.

**Finding:** Verified on visionOS 26.5 that opening an `ImmersiveSpace` causes the system to
hide every other app, including with `.mixed` immersion. Apple documents this. Third-party
apps cannot publish into the system Environments picker; Disney+ and HBO Max have the same
limitation. Details: [`../learning-notes/immersive-space-hides-other-apps.md`](../learning-notes/immersive-space-hides-other-apps.md).

**Decision:** Resolved 2026-09-03 by changing the goal — see below.

---

## 2026-09-03 — The Tower is a personal tool, not a product

**Context:** The immersive-space constraint made the "office backdrop" premise unsellable, which
forced a choice between reworking the product or rethinking the goal.

**Decision:** Build it for me. An App Store release may follow as a generic version, but it drives
no decisions. Developer Mode plus Allow Mac Virtual Display is an acceptable requirement for an
audience of one, so the office concept works as originally imagined.

**Why:** The point was always to have this room to work in. Optimising it for strangers was
adding constraints (App Review, onboarding, ROI on assets) in service of revenue that was never
the motivation.

**Consequences:**
- Phase 3 unblocked; budget is taste-driven rather than ROI-driven.
- Phase 7 (App Store) becomes optional and deferred.
- Phase 5 must keep the scene data-driven — this needs to stay tweakable for years.
- Still buy commercial-use asset licences, to keep the generic-version option cheap.
- **Owning a Vision Pro moves from "nice for testing" to a hard prerequisite.**

---

## 2026-09-03 — Full immersion, and glaze the window

**Context:** `.mixed` was chosen to escape the 1.5 m safety boundary so the room could be paced
around. Once the room had lighting, it turned out that mixed cannot be lit: RealityKit lights
virtual content from the real surroundings and `ImageBasedLightComponent` does not override it.
Night stayed fully bright with every one of our lights disabled; the same build in `.full` was
pitch black.

**Decision:** Switch to `.full`, and put glass in the window.

**Why:** The glass removes the reason to lean out, and the boundary is a 1.5 m *radius* centred
where you start — roughly two paces back from the desk. That is a small cost against never being
able to have a dark room, candles that read as sources, or a fire worth lighting.

**Consequences:**
- Pacing is limited to about two paces unless you stand and recentre.
- Lighting is now entirely ours, which is what makes Phase 4's atmosphere work possible.
- The glass must not cast shadows or it blocks the window light; handled in `TowerLighting`.
- Worth re-testing on hardware: a dim real study may intrude far less than the simulator's
  bright living room, which might make mixed viable again.

---

## Gate 1 — After Phase 1: Did Reality Composer Pro click?

- **Question:** Was RCP gratifying or frustrating? If frustrating, consider partnering with a 3D artist or drastically simplifying the scene.
- **Date:** —
- **Verdict:** —
- **Notes:** —

## Gate 2 — After Phase 2: Would you use this room daily?

- **Question:** Is the design something *you* want to work in for months? If not, the audience won't either.
- **Date:** —
- **Verdict:** —
- **Notes:** —

## Gate 3 — After Phase 3: Assets good enough at acceptable cost?

- **Question:** If everything felt cheap or too expensive: raise budget, switch theme (alchemist lab?), or commission hero pieces.
- **Date:** —
- **Verdict:** —
- **Total spent on assets:** $—
- **Notes:** —

## Gate 4 — After Phase 4: A place, or a Unity demo? ⭐ MOST IMPORTANT GATE

- **Question:** Does the room feel real from the seat? If not, fix lighting/audio/scale or restart Phase 4. Code will not save it.
- **Date:** —
- **Verdict:** —
- **Notes:** —

## Gate 5 — After Phase 6: Structural rework needed?

- **Question:** Did hardware testing reveal comfort/performance issues requiring rework? If yes, do the rework before submitting.
- **Date:** —
- **Verdict:** —
- **Notes:** —

---

## 2026-09-03 — Batch the town by baking one mesh per building

**Context:** The village is ~2,400 placements of 20 modular kit pieces. That is
~2,400 entities and at least as many draw calls, which is CPU work a faster GPU
does not help with — the first thing to suspect if the frame rate suffers.

**Rejected:** a USD `PointInstancer` per module type. RealityKit does not expand
them; it loads the prototype and throws the placements away, dumping the town at
the origin. Verified numerically in the simulator, not by eye — see
[`../learning-notes/realitykit-geometry-gotchas.md`](../learning-notes/realitykit-geometry-gotchas.md).

**Decision:** Bake ahead of time with `tools/merge_town.py`, joining each
building into one mesh — **per building, not per module type.**

**Why per building:** merging by module type would give ~20 meshes but each would
span the whole 86 m town, so nothing could ever be frustum-culled and the entire
village would be rasterised whenever any part of it was on screen. One mesh per
building keeps a cullable unit per house and still collapses the town to 53
entities and 355 submeshes.

**Cost:** shared kit geometry becomes per-building copies — 19 k unique vertices
become ~990 k, about 63 MB of baked `.usdc`. Triangle count is unchanged; only
the sharing is lost. Acceptable against the 55 MB just saved by dropping the kit
textures to 1K.

**Consequences:**
- `village/merged/` is gitignored — it is regenerated, and would otherwise add
  63 MB to history every time the village layout changes.
- The generator falls back to unbatched references when the bake is absent, and
  prints which mode it used, so a missing bake degrades rather than breaks.
- **Re-run `tools/merge_town.py` after any change to the village layout**, or the
  town silently keeps the old baked geometry.
