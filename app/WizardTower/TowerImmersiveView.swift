import RealityKit
import RealityKitContent
import SwiftUI

/// Loads the Reality Composer Pro scene and lights it.
struct TowerImmersiveView: View {

    @Environment(AppModel.self) private var appModel

    var body: some View {
        RealityView { content in
            guard let scene = try? await Entity(named: "Tower", in: realityKitContentBundle) else {
                assertionFailure("Failed to load the Tower scene from RealityKitContent.")
                return
            }

            let time = appModel.timeOfDay
            if let ibl = await TowerLighting.imageBasedLight(for: time) {
                content.add(ibl)
                // Everything in the room should receive the window's light.
                scene.components.set(ImageBasedLightReceiverComponent(imageBasedLight: ibl))
            }
            content.add(TowerLighting.sun(for: time))
            for candle in TowerLighting.candles(for: time) {
                content.add(candle)
            }
            content.add(scene)
        }
        .onAppear { appModel.immersiveSpaceState = .open }
        .onDisappear { appModel.immersiveSpaceState = .closed }
    }
}
