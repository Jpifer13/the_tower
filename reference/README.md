# Reference material

Not part of the app. Downloaded material used for learning and practice.

```
reference/
├── apple-samples/        # gitignored (~1 GB)
│   ├── diorama/          # Apple's Diorama — the canonical RCP scene to dissect
│   └── hello-world/      # Apple's "Hello World" (World) visionOS sample
└── practice-assets/      # gitignored (~53 MB)
    ├── hdri/             # Poly Haven 2K HDRIs — day / sunset / moonlit night
    └── usdz/             # Apple Quick Look gallery models
```

## Licences

- **Apple samples** — Apple's sample code licence, in each folder's `LICENSE.txt`. Reference
  only; do not copy assets into the shipping app.
- **Poly Haven HDRIs** — CC0. Usable commercially with no attribution. If one of these ends up
  in the shipped app, promote it into `assets/hdri/` and give it a row in `assets/ASSET_MANIFEST.md`.
- **Apple Quick Look models** — Apple's gallery, for practice only. Do not ship them.

## Getting it back

All of it is gitignored, so a fresh clone won't have any of it. One command:

```bash
./reference/fetch.sh
```

It's idempotent — it skips anything already downloaded.
