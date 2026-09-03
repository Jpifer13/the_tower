import RealityKit
import RealityKitContent
import SwiftUI

/// Loads the Reality Composer Pro scene. Everything built in Phases 1–4
/// lands in `Packages/RealityKitContent` and surfaces through here.
struct TowerImmersiveView: View {

    @Environment(AppModel.self) private var appModel

    var body: some View {
        RealityView { content in
            guard let scene = try? await Entity(named: "Tower", in: realityKitContentBundle) else {
                assertionFailure("Failed to load the Tower scene from RealityKitContent.")
                return
            }
            content.add(scene)
        }
        .onAppear { appModel.immersiveSpaceState = .open }
        .onDisappear { appModel.immersiveSpaceState = .closed }
    }
}
