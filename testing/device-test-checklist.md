# Phase 6 — Real Device Test Checklist

**Device source:** ☐ Apple Developer Lab (book at developer.apple.com/events) · ☐ Bought used (~$2.5–3K) · ☐ Borrowed
**Date tested:** —
**Build tested:** —

> The Simulator hides all of this. Test every section; write findings inline. Vision Pro's M2 is much weaker than the M3 Ultra — expect surprises.

## 1. Scale & presence

- [ ] Room feels cozy — not cavernous, not claustrophobic
- [ ] Ceiling height reads right from the seat
- [ ] Furniture proportions correct at arm's length
- Findings:

## 2. Comfort

- [ ] No motion/flicker discomfort over a 15-minute sit
- [ ] Particle density comfortable (dust, embers, fireflies)
- [ ] Candle flicker rate not distracting or strobing
- [ ] No sudden lighting changes on time-of-day/weather transitions
- Findings:

## 3. Performance

- [ ] Steady 90 FPS, no stutters (worst case: night + fire + weather particles)
- [ ] Scene loads in < 5 s on device
- [ ] No thermal issues over a longer session
- Findings / reductions needed (poly counts, texture sizes):

## 4. UI ergonomics

- [ ] Tap targets big enough and where eyes naturally land
- [ ] Candle relight and fireplace toggle register reliably
- [ ] Settings panel readable and reachable from the seat
- Findings:

## 5. Immersion levels

- [ ] Looks right at 25% / 50% / 75% / 100%
- [ ] Passthrough blend at partial immersion is clean against a real room
- Findings:

## 6. Audio

- [ ] Spatial falloffs feel natural in the headset (not just headphones-at-desk)
- [ ] Ambient mix level comfortable for long sessions
- Findings:

---

## Punch list (prioritized)

| # | Issue | Severity (blocker / should-fix / polish) | Fix plan |
|---|---|---|---|
| 1 | | | |

**Gate 5 verdict → record in `docs/decisions/DECISIONS.md`.**
