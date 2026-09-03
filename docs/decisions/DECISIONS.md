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

**Decision:** **PENDING** — product direction needs re-deciding before Phase 3 spending.

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
