import RealityKit
import RealityKitContent
import SwiftUI

/// Loads the Reality Composer Pro scene and keeps it lit.
struct TowerImmersiveView: View {

    @Environment(AppModel.self) private var appModel
    @State private var rig = LightRig()
    @State private var scene: Entity?

    /// How often the sun is re-aimed in live mode. A minute is far finer than the
    /// eye can follow — the sun moves a quarter of a degree — but it keeps the
    /// room honest across a long working day without any real cost.
    private static let refreshInterval = Duration.seconds(60)

    var body: some View {
        RealityView { content in
            guard let loaded = try? await Entity(named: "Tower", in: realityKitContentBundle) else {
                assertionFailure("Failed to load the Tower scene from RealityKitContent.")
                return
            }
            content.add(rig.root)
            content.add(loaded)
            scene = loaded
            await rig.apply(appModel.lightingState(), to: loaded)
        }
        .task {
            // Re-aim as the day moves, and whenever the mode changes.
            while !Task.isCancelled {
                if let scene {
                    await rig.apply(appModel.lightingState(), to: scene)
                }
                try? await Task.sleep(for: Self.refreshInterval)
            }
        }
        .onChange(of: appModel.lightingMode) {
            guard let scene else { return }
            Task { await rig.apply(appModel.lightingState(), to: scene) }
        }
        .onAppear { appModel.immersiveSpaceState = .open }
        .onDisappear { appModel.immersiveSpaceState = .closed }
    }
}
