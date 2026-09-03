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
            content.add(Self.blockoutKeyLight())
        }
        .onAppear { appModel.immersiveSpaceState = .open }
        .onDisappear { appModel.immersiveSpaceState = .closed }
    }

    /// Temporary. Enough light to read the blockout's shape while Phase 4 is
    /// still ahead; replaced by image-based lighting from the window HDRI.
    private static func blockoutKeyLight() -> Entity {
        let light = Entity()
        var directional = DirectionalLightComponent()
        directional.intensity = 3200
        light.components.set(directional)
        // From high on the window side, so the opening reads as the light source.
        light.look(at: .zero, from: [2.5, 3.0, -0.5], relativeTo: nil)
        return light
    }
}
