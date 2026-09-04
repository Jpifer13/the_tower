import OSLog
import RealityKit
import SwiftUI
import UIKit

private let log = Logger(subsystem: "io.confuseddev.wizardtower", category: "lighting")

/// Builds the room's lighting.
///
/// The design makes the window the primary light: image-based lighting generated
/// from the same sky you can see through the opening, so the room's ambient and
/// the view agree. On top of that sits a directional sun or moon, and warm point
/// lights where the candles are.
enum TowerLighting {

    /// Candle flames, in the same user-relative space as the props.
    /// Kept in step with PROPS in tools/generate_tower_shell.py.
    static let candlePositions: [SIMD3<Float>] = [
        [0.85, 0.98, -0.95],   // CandleStick_Triple
        [1.35, 0.90, -0.80],   // Candle_1
        [0.00, 4.05,  2.95],   // Chandelier
    ]

    /// Image-based light. Generated from the sky image at runtime, so no
    /// Reality Composer Pro environment asset is needed.
    @MainActor
    static func imageBasedLight(for time: TimeOfDay) async -> Entity? {
        // Never fatal: a missing or unusable sky should dim the room, not kill the app.
        //
        // UIImage(named:) is really an asset-catalog lookup and does not reliably
        // find loose bundle files, so resolve the URL explicitly.
        guard let url = Bundle.main.url(forResource: time.skyImageName, withExtension: "jpg"),
              let ui = UIImage(contentsOfFile: url.path),
              let cg = ui.cgImage else {
            log.error("no sky image named \(time.skyImageName).jpg in the bundle")
            return nil
        }
        log.info("sky \(time.skyImageName) loaded, \(cg.width)x\(cg.height)")
        let resource: EnvironmentResource
        do {
            resource = try await EnvironmentResource
                .generate(fromEquirectangular: cg, withName: time.skyImageName)
        } catch {
            log.error("EnvironmentResource.generate failed: \(error.localizedDescription)")
            return nil
        }
        let entity = Entity()
        entity.name = "IBL"
        entity.components.set(ImageBasedLightComponent(source: .single(resource),
                                                       intensityExponent: time.iblExponent))
        log.info("image-based light ready for \(time.rawValue)")
        return entity
    }

    /// Sun or moon through the window. The window sits 55° to the right, so the
    /// light comes from that side rather than from an arbitrary angle.
    @MainActor
    static func sun(for time: TimeOfDay) -> Entity {
        let entity = Entity()
        entity.name = "Sun"
        var light = DirectionalLightComponent()
        light.intensity = time.sunIntensity
        let c = time.sunColor
        light.color = UIColor(red: CGFloat(c.r), green: CGFloat(c.g),
                              blue: CGFloat(c.b), alpha: 1)
        entity.components.set(light)
        // Sunset rakes in low; midday comes from higher up.
        let height: Float = time == .sunset ? 1.6 : 5.0
        entity.look(at: [0, 1, 0], from: [5.2, height, -1.0], relativeTo: nil)
        return entity
    }

    /// Warm, small point lights at each flame.
    @MainActor
    static func candles(for time: TimeOfDay) -> [Entity] {
        guard time.candlesLit else { return [] }
        return candlePositions.enumerated().map { index, position in
            let entity = Entity()
            entity.name = "Candle\(index)"
            var light = PointLightComponent()
            light.intensity = index == 2 ? 900 : 350   // the chandelier carries more
            light.attenuationRadius = index == 2 ? 6.0 : 2.5
            light.color = UIColor(red: 1.0, green: 0.72, blue: 0.42, alpha: 1)
            entity.components.set(light)
            entity.position = position
            return entity
        }
    }
}
