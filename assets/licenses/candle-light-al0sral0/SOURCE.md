# "Candle light" — al0sral0

- **Source:** https://sketchfab.com/3d-models/candle-light-d9d5ed5de83b4d899ab93f55bdc3d0bc
- **Author:** al0sral0 (Sketchfab)
- **Retrieved:** 2026-09-04
- **Licence:** CC Attribution 4.0 — *"Author must be credited. Commercial use is allowed."*
- **Used for:** the animated candle flame. `tools/convert_candle_flame.py` keeps a
  single flame mesh and its armature and discards the wax, the other two flames
  and a stray plane.

## Attribution — required

This licence obliges us to credit the author. The credit appears in the app, in
`CreditsView`, reachable from the control panel.

> "Candle light" by al0sral0, licensed CC BY 4.0
> https://sketchfab.com/3d-models/candle-light-d9d5ed5de83b4d899ab93f55bdc3d0bc

## Why this one

No CC0 animated flame exists — a search of every downloadable animated
fire/flame/candle model on Sketchfab returned zero CC0 results. Every option was
CC-BY, so the choice was between accepting attribution or authoring a flame from
scratch. ShareAlike variants were rejected: SA can propagate its terms into the
work built around it.

Its animation is bone-driven, which is the only kind that survives
glTF -> Blender -> USD. A flame animated in a material graph would have exported
as a still.
