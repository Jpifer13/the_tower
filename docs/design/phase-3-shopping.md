# Phase 3 — shopping list and findings

## The decision to make first: stylised or realistic?

Nothing else should be bought until this is settled, because the two look wrong together.
A stylised prop in a realistic room reads as a mistake, not a style.

Everything in the design doc so far quietly assumes **realistic** — stone roughness, PBR
materials, HDRI lighting, "feels like a place, not a Unity demo", a window frame inspected at
30 cm. But the best-value asset pack found is stylised. Hence the fork.

| | Realistic | Stylised (low-poly / hand-painted) |
|---|---|---|
| Matches the design doc | Yes | No — would need the doc revisiting |
| Holds up at 30 cm | Yes, if the assets are good | It's a deliberate look, so "soft" reads as intentional |
| Cost | $150–400 | Near zero — the best packs are CC0 |
| Poly budget | Tight against the 500K target | Trivially cheap |
| Lighting effort | High — the whole illusion rests on it | Forgiving |
| Risk | Cheap assets look *wrong*, not stylised | Might not feel like "a place you work" |

**Not a recommendation, a genuine preference call.** But note the realistic path is where the
plan's "single most important quality gate" (Phase 4: a place, or a Unity demo?) actually bites.

## Confirmed finds

### Quaternius Fantasy Props MegaKit — the standout if stylised
- https://quaternius.itch.io/fantasy-props-megakit
- **CC0.** Commercial use, no attribution, no royalty. Verified on the page.
- Free tier: 94 assets. Pro $9.99: 200+. **Source $14.99: includes a "Wizard's Den" scene.**
- FBX / OBJ / glTF → needs Blender → USDZ conversion.
- Covers furniture *and* props in one buy, at roughly 4% of the realistic budget.

### Medieval Library Model Pack (Sketchfab) — realistic-leaning
- Bookshelf, cupboard, librarian's desk, plus quill, ink pot, open book, book stacks,
  candle and holder, hourglass. Close to the prop list already written.
- Comes in standard / black / rustic variants.
- Paid, royalty-free. **Verify the licence on the page at purchase time.**

### Audio — no Freesound account needed
Freesound wants an account and API token. These are CC0 and directly downloadable:
- **BigSoundBank** — CC0, has fireplace recordings
- **OpenGameArt** — CC0 fire crackling
- **Chosic** — CC0 fire crackles
- **Creazilla** — 130k+ CC0 audio
- **Pixabay** — royalty-free SFX

Remember the audio list is larger than the original plan: window beds for clear / rain / snow /
wind across day / sunset / night, plus fire, room tone, owl and page rustle.

## Already done

| Item | Status |
|---|---|
| Room shell | **Generated**, not bought — `tools/generate_tower_shell.py` |
| Sky HDRIs (day / sunset / night, 4K) | Acquired, CC0, licences filed |
| Window frame | Part of the shell — but needs real detail, see below |

## Still needed

| Item | Notes | Budget |
|---|---|---|
| Furniture — desk, chair, shelves, fireplace | One pack ideally | $0–80 |
| Props — books, candles, scrolls, bottles, crystal ball, quill | One pack ideally | $0–60 |
| **Window frame + reveal** | Inspected at 30 cm. The one place to overspend | $0–40 |
| **Exterior geometry** — tower wall below, rooftops, tree | From the hybrid decision. Only the ~90° cone visible | $20–60 |
| Audio | CC0 sources above | $0 |

## Rules that still apply

- Every asset gets a row in `../../assets/ASSET_MANIFEST.md` and a folder in `assets/licenses/`
  **before** it's used — receipt plus a dated screenshot of the licence page.
- Commercial-use licences even though this is personal, so a generic version stays cheap.
- Reject "editorial only", "personal use only", "rendering only", AI-generated 3D, and anything
  derivative of branded IP.
- Purchased assets are **not** in git. Back them up yourself; only licences are tracked.
