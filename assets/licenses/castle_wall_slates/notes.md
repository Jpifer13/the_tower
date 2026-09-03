# castle_wall_slates (T-001) — tower wall
- Source: https://polyhaven.com/a/castle_wall_slates
- Acquired: 2026-09-03. 2K JPG, Diffuse + nor_gl + Rough.
- Licence: **CC0** — commercial use, no attribution, no royalty.
- **Modified:** the diffuse map is desaturated to greyscale after download
  (`tools/fetch_assets.sh`). CC0 permits modification. The original ships warm, and a
  warm albedo cannot be made to read as grey stone by tinting alone.
- Used by: TowerShell Wall material, tiled 9x round the circumference, with a
  darkening/cooling tint on top (WALL_TINT, default 0.58,0.68,0.88).
- Replaced `medieval_blocks_05`, which read too warm and sandy for a stone tower.
