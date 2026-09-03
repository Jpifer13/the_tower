# App

The visionOS app. Built and verified in Phase 0 against **Xcode 26.5 / visionOS 26.5**.

```
app/
├── WizardTower.xcodeproj
├── WizardTower/                    # app target (file-system synchronized group)
│   ├── WizardTowerApp.swift        # @main — WindowGroup + ImmersiveSpace
│   ├── AppModel.swift              # @Observable app state (grows in Phase 5)
│   ├── ControlPanelView.swift      # the floating window → becomes the settings panel
│   ├── TowerImmersiveView.swift    # RealityView that loads the RCP scene
│   ├── Info.plist                  # scene manifest (see note below)
│   └── Assets.xcassets             # AppIcon.solidimagestack (layered visionOS icon)
└── Packages/RealityKitContent/     # local Swift package = the Reality Composer Pro project
    ├── Package.realitycomposerpro/ # RCP project metadata — open THIS in RCP
    └── Sources/RealityKitContent/
        ├── RealityKitContent.swift # exposes `realityKitContentBundle`
        └── RealityKitContent.rkassets/
            └── Tower.usda          # placeholder orb — replaced by the real room in Phase 4
```

## Build & run

```bash
# Build
xcodebuild build -scheme WizardTower \
  -destination 'platform=visionOS Simulator,name=Apple Vision Pro'

# Run in the simulator
xcrun simctl boot "Apple Vision Pro"; open -a Simulator
xcrun simctl install "Apple Vision Pro" <path-to>/WizardTower.app
xcrun simctl launch "Apple Vision Pro" io.confuseddev.wizardtower
```

Or just open `WizardTower.xcodeproj` and hit ⌘R.

Edit 3D content by opening `Packages/RealityKitContent/Package.realitycomposerpro`
in Reality Composer Pro (Xcode → Open Developer Tool → Reality Composer Pro).

## Things worth knowing

- **Bundle ID is `io.confuseddev.wizardtower`**, team `89DJNH7K9F`.
- **An ImmersiveSpace only opens via `openImmersiveSpace`** — no Info.plist key or scene
  ordering will auto-open it at launch. See `docs/learning-notes/visionos-scenes.md`.
- **`Info.plist` is a real file** (`INFOPLIST_FILE`), and the project carries a
  `PBXFileSystemSynchronizedBuildFileExceptionSet` so the synchronized folder doesn't also
  copy it as a resource. Don't remove that exception — the build breaks with
  "Multiple commands produce .../Info.plist".
- **Deployment target is visionOS 2.0**; the RealityKitContent package declares `.visionOS(.v1)`
  because `swift-tools-version:5.9` doesn't know newer cases.

## Phase 5 architecture (planned)

SwiftUI for UI, RealityKit + RealityView for the scene, ImmersiveSpace for full immersion,
one `@Observable` model for time-of-day / weather / fire / volume, WeatherKit for live
conditions (needs the capability on the App ID **and** in Signing & Capabilities, plus
`NSLocationWhenInUseUsageDescription`).
