# The Tower

A wizard-themed immersive environment for Apple Vision Pro — **a personal tool, built to be worked in.** One circular tower study with live weather, time-of-day and subtle interactions, with the Mac Virtual Display floating over the desk.

Built for an audience of one. An App Store release may follow as a stripped-down generic version, but it drives no decisions. See [`docs/decisions/DECISIONS.md`](docs/decisions/DECISIONS.md).

Full plan: [wizard_tower_build_plan.md](wizard_tower_build_plan.md)
Current status: [PROGRESS.md](PROGRESS.md)

## Directory layout

```
the_tower/
├── wizard_tower_build_plan.md   # The master plan (source of truth for phases)
├── PROGRESS.md                  # Phase tracker — update as you go
├── app/                         # visionOS Xcode project (see app/README.md)
├── docs/
│   ├── design/                  # Phase 2: design doc, floor plan, lighting & audio plans
│   │   └── mood-board/          # Reference images (wizard towers, alchemist studies)
│   ├── decisions/               # Decision log — the 5 go/no-go gates + anything else
│   └── learning-notes/          # Phase 1: WWDC session notes, RCP gotchas
├── assets/
│   ├── models/                  # USDZ/USD files, organized by category
│   │   ├── room-shell/
│   │   ├── furniture/
│   │   └── props/
│   ├── audio/                   # Ambient loops, fire crackle, wind, owl, page rustle
│   ├── hdri/                    # Skybox / IBL environments (day, sunset, night)
│   ├── source/                  # Original downloads (FBX/OBJ) before USDZ conversion
│   ├── licenses/                # One folder per asset: receipt + license terms snapshot
│   └── ASSET_MANIFEST.md        # Every asset, its source, price, and license status
├── testing/                     # Phase 6: device test checklist and results
└── marketing/
    ├── app-store/               # Name, subtitle, description, keywords, reviewer notes
    ├── screenshots/             # Simulator captures at required resolutions
    └── preview-video/           # 15–30s preview video project + exports
```

## Working rules

1. **PROGRESS.md is the dashboard.** Check items off there; don't edit the build plan.
2. **No asset enters `assets/models|audio|hdri` without a row in ASSET_MANIFEST.md and a folder in `assets/licenses/`.** License hygiene is a hard rule, not a chore.
3. **Decision gates are real.** At the end of Phases 1, 2, 3, 4, and 6, write the verdict in `docs/decisions/DECISIONS.md` before starting the next phase.
4. **Buy commercial-use asset licences anyway.** Usually the same price, and it keeps a generic App Store version cheap to do later instead of requiring a re-buy.
5. **Keep the scene data-driven.** This has to stay tweakable for years — lighting, audio, time-of-day and prop placement belong in RCP or config, not hardcoded in Swift.
4. **The Xcode project stays inside `app/`** so project docs, assets-in-progress, and marketing material don't pollute the build tree. Only assets that ship get copied into the RCP package.
