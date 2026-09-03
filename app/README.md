# App

The Xcode project goes here (Phase 0): **visionOS → App → SwiftUI + RealityKit**, initial scene Volume (switched to Full Space in task 3).

Keep the build tree clean — working assets stay up in `../assets/`; only final USDZs get added to the Reality Composer Pro package inside this project.

Architecture (from the plan, Phase 5):
- SwiftUI for all UI; RealityKit + RealityView for the scene; ImmersiveSpace for full immersion
- One `@Observable` app model: time-of-day, weather, fire on/off, ambient volume, immersion level
- WeatherKit for live weather (capability must be enabled on the App ID **and** in Signing & Capabilities)
- `NSLocationWhenInUseUsageDescription` in Info.plist
