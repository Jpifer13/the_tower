# visionOS scenes — Phase 0 findings

## An ImmersiveSpace never opens itself

Three things do **not** launch the app straight into the immersive space:

1. `UIApplicationPreferredDefaultSceneSessionRole = UIWindowSceneSessionRoleImmersiveSpaceApplication`
   in `Info.plist` (verified present in the built plist — no effect on a SwiftUI app).
2. Adding `UISceneInitialImmersionStyle = UIImmersionStyleFull` alongside it.
3. Declaring `ImmersiveSpace` before `WindowGroup` in the `App`'s `body`.

The only thing that opens it is an explicit call:

```swift
@Environment(\.openImmersiveSpace) private var openImmersiveSpace
...
await openImmersiveSpace(id: AppModel.immersiveSpaceID)
```

Apple's own "Immersive Environment App" template agrees — it ships
`UIWindowSceneSessionRoleApplication` and a toggle button. Window-first with a
deliberate "enter" action is the intended shape, so that's what `The Tower` does.

**Consequence for Phase 7:** simulator screenshots of the immersive scene can't be
taken from a cold launch. Either tap the button by hand, or temporarily add
`.task { await toggleImmersiveSpace(open: true) }` to `ControlPanelView` for the
screenshot session.

## Info.plist must be a real file, not generated

`GENERATE_INFOPLIST_FILE = YES` alone can't set the scene-manifest keys —
`INFOPLIST_KEY_UIApplicationPreferredDefaultSceneSessionRole` is not a recognized
build setting and is silently dropped. Apple's template sets
`INFOPLIST_FILE = $(TARGET_NAME)/Info.plist` and keeps generation on; the file is
the base and generated keys merge in.

Because the target uses a **file-system synchronized group**, an `Info.plist`
sitting inside the target folder is also copied as a resource →
`error: Multiple commands produce .../WizardTower.app/Info.plist`. The fix is a
membership exception in the project file:

```
PBXFileSystemSynchronizedBuildFileExceptionSet {
    membershipExceptions = ( Info.plist );
    target = <the app target>;
}
```

## RealityKitContent package

- `.rkassets` is compiled by `realitytool` into `RealityKitContent.reality`;
  nothing needs declaring as a resource in `Package.swift`.
- `Package.swift` at `swift-tools-version:5.9` only knows `.visionOS(.v1)`,
  `.macOS(.v14)`, `.iOS(.v17)`. Newer enum cases need tools 6.0.
- Reality Composer Pro needs a `Package.realitycomposerpro/` folder
  (`ProjectData/main.json` mapping scene paths → UUIDs, plus `WorkspaceData/`)
  or it won't treat the folder as an RCP project.
