# Asset Manifest

Every 3D model, audio file, and HDRI that enters this project gets a row here **before** it gets used in a scene. No row + no license folder = the asset doesn't exist.

## License acceptance checklist (per asset)

An asset is ✅ only if its license explicitly allows ALL of:
- Commercial use
- Embedding in a software product
- No per-unit royalty
- No attribution required (or you accept adding a credits screen — note it)

Auto-reject: "editorial only", "personal use only", "rendering only", AI-generated 3D, anything visually derivative of branded IP (Hogwarts, Skyrim, LOTR, D&D).

## Models

| ID | Asset | Category | Source | Price | Format | Converted to USDZ | License | License folder | Status |
|---|---|---|---|---|---|---|---|---|---|
| M-001 | **Tower shell — generated, not bought** | room-shell | `tools/generate_tower_shell.py` | $0 | USD | n/a — ours | n/a | ✅ |

## Textures (PBR sets — "skins" for the generated shell)

| ID | Texture | Use | Source | Price | License | License folder | Status |
|---|---|---|---|---|---|---|---|
| T-001 | medieval_blocks_05 2K | tower wall | Poly Haven | $0 | CC0 | `licenses/medieval_blocks_05/` | ✅ |
| T-002 | dark_wooden_planks 2K | floor | Poly Haven | $0 | CC0 | `licenses/dark_wooden_planks/` | ✅ |
| T-003 | brown_planks_03 2K | conical ceiling | Poly Haven | $0 | CC0 | `licenses/brown_planks_03/` | ✅ |

Each set is Diffuse + nor_gl + Rough as 2K JPG, in `RealityKitContent.rkassets/textures/`.

## Audio

| ID | Sound | Use | Source | Price | License | License folder | Status |
|---|---|---|---|---|---|---|---|
| A-001 | _(e.g. Fireplace crackle loop)_ | fireplace | freesound | $0 | CC0 | `licenses/A-001/` | ☐ |

## HDRIs

| ID | HDRI | Use | Source | Price | License | License folder | Status |
|---|---|---|---|---|---|---|---|
| H-001 | kloofendal_38d_partly_cloudy 4K | day sky + IBL | Poly Haven | $0 | CC0 | `licenses/kloofendal_38d_partly_cloudy/` | ✅ |
| H-002 | rogland_sunset 4K | sunset sky + IBL | Poly Haven | $0 | CC0 | `licenses/rogland_sunset/` | ✅ |
| H-003 | rogland_moonlit_night 4K | night sky + IBL | Poly Haven | $0 | CC0 | `licenses/rogland_moonlit_night/` | ✅ |

## Budget tracker

| Category | Budget | Spent |
|---|---|---|
| Room shell | $50–150 | $0 |
| Furniture | $20–80 | $0 |
| Props | $20–60 | $0 |
| Window frame — *spend here*, it's inspected at 30 cm | included in shell | $0 |
| Exterior geometry (rooftops, tree, tower wall) | $20–60 | $0 |
| Sky HDRIs, 4–8K | $0–30 | $0 |
| Audio | $0 | $0 |
| **Total** | **~$170–460** | **$0** |

Budget is taste-driven now, not ROI-driven — see [`../docs/decisions/DECISIONS.md`](../docs/decisions/DECISIONS.md).
Still buy **commercial-use** licences so a generic App Store version stays cheap to do later.

## Attribution required?

If any asset ends up attribution-only, list it here — this becomes the in-app credits screen:

- _(none yet)_
