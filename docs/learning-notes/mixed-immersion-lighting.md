# Mixed immersion lights your room for you, and you cannot stop it

**Verified in the simulator, 2026-09-03. This is a design decision, not a bug.**

## What happens

In `.mixed` immersion, RealityKit lights virtual content from the surrounding
environment — real passthrough on device, the simulated living room in the
simulator. **`ImageBasedLightComponent` does not override it.**

The room stayed brightly lit at night no matter what:

| Change | Result |
|---|---|
| IBL exponent −2.2 → −5.4 (≈1/50 of open sky) | no visible change |
| IBL exponent −20 (effectively zero) | no visible change |
| Receiver applied to all 56 entities, not just the root | no visible change |
| Moonlight off, candles off, IBL off — *every* light we add removed | **still fully lit** |
| Same build, immersion switched to `.full` | **pitch black** |

The last two rows are the proof. With every one of our lights disabled the room
was still bright in mixed and completely black in full. The light was never ours.

## The trade this forces

The two things the design wants are in direct conflict:

| | `.mixed` | `.full` |
|---|---|---|
| Pace around the room | **Yes** | No — 1.5 m boundary ends the experience |
| Control the lighting | **No** — always lit by the real room | **Yes** |
| Night actually dark | No | Yes |
| Candles and fire read as sources | Barely | Yes |

`.mixed` was chosen to escape the 1.5 m leash documented in
[`immersion-style-and-the-15m-boundary.md`](immersion-style-and-the-15m-boundary.md).
That reasoning still holds — but the cost was not visible until the room had
lighting worth protecting.

## Worth knowing

The receiver fix stays regardless: `ImageBasedLightReceiverComponent` is **not
inherited**, so setting it on the scene root reached exactly one entity out of
56. That was a real bug, just not the one causing the brightness. In `.full` it
matters.
