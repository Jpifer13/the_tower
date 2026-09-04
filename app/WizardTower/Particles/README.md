# Fire flipbook

Drop a sprite sheet here named **`fire_flipbook.png`** and the hearth uses it
automatically. Without one the particles render as soft dots.

## What RealityKit wants

A **single image containing a grid of frames** — not separate files.
`TowerLighting` sets `image` to the sheet and `imageSequence` to the grid.

Set `flipbookRows` / `flipbookColumns` in `TowerLighting.swift` to match the
sheet. They default to **8×8**.

## Picking a sheet

- **Grid layout**, typically 6×6 or 8×8. Count the frames before setting the grid;
  a mismatch shows as frames sliding rather than animating.
- **Black background.** The emitter uses additive blending, so black is
  transparent. A sheet with an alpha channel also works.
- **Resolution**: 2048×2048 for an 8×8 grid gives 256 px frames, which is ample
  for something a couple of metres away.
- **Licence must allow commercial use** — the project rule, so a generic App Store
  version stays possible. File it in `assets/licenses/` with a manifest row.

## Sources

- **CGHEVEN** — CC0 fire flipbooks in 6×6 and 8×8 grids, no attribution required.
  The closest match to what RealityKit wants. https://cgheven.com/assets/flipbooks
- **Unity's free VFX image sequences** — CC0, but supplied as EXR/TGA sequences,
  so they need assembling into a sheet first.
  https://unity.com/blog/engine-platform/free-vfx-image-sequences-flipbooks

Both were found by search and **not verified first-hand** — check the licence on
the page at download time, as the project rules require.
