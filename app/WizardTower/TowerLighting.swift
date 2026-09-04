import OSLog
import RealityKit
import SwiftUI
import UIKit

private let log = Logger(subsystem: "io.confuseddev.wizardtower", category: "lighting")

/// How the room is lit right now.
struct LightingState: Equatable {
    var timeOfDay: TimeOfDay
    /// Degrees above the horizon. Drives intensity and how the light rakes in.
    var sunElevation: Double
    /// Degrees clockwise from straight ahead (the desk); the window is at +55.
    var sunBearingInRoom: Double
    /// 0 below the horizon, 1 in full day.
    var daylight: Double
}

/// The room's lights, held so they can be re-aimed as the day moves rather than
/// rebuilt. The window is the primary source: image-based lighting generated from
/// the same sky visible through the opening, plus a directional sun or moon.
@MainActor
final class LightRig {

    let root = Entity()

    private let sun = Entity()
    private var iblEntity: Entity?
    private var candleEntities: [Entity] = []
    private var appliedSky: TimeOfDay?
    private var appliedCandles: Bool?

    /// Candle flames, in the same user-relative space as the props.
    /// Kept in step with PROPS in tools/generate_tower_shell.py.
    static let candlePositions: [SIMD3<Float>] = [
        [0.85, 0.98, -0.95],   // CandleStick_Triple
        [1.35, 0.90, -0.80],   // Candle_1
        [0.00, 4.05,  2.95],   // Chandelier
    ]

    init() {
        root.addChild(sun)
        sun.name = "Sun"
        // Directional lights cast nothing without a Shadow, and its default 5 m
        // reach does not cover a 9 m room.
        sun.components.set(DirectionalLightComponent.Shadow(
            shadowProjection: .automatic(maximumDistance: 28.0),
            depthBias: 1.5))
    }

    func apply(_ state: LightingState, to scene: Entity) async {
        Self.stopGlassCastingShadows(in: scene)
        await applySky(state, to: scene)
        applySun(state)
        applyCandles(state)
    }

    // MARK: - Window light

    private func applySky(_ state: LightingState, to scene: Entity) async {
        guard appliedSky != state.timeOfDay else { return }
        appliedSky = state.timeOfDay

        // UIImage(named:) is an asset-catalog lookup and will not find a loose
        // bundle file, so resolve the URL. Never fatal: a missing sky should dim
        // the room, not kill the app.
        let name = state.timeOfDay.skyImageName
        guard let url = Bundle.main.url(forResource: name, withExtension: "jpg"),
              let image = UIImage(contentsOfFile: url.path),
              let cgImage = image.cgImage else {
            log.error("no sky image named \(name).jpg in the bundle")
            return
        }
        do {
            let resource = try await EnvironmentResource
                .generate(fromEquirectangular: cgImage, withName: name)
            let entity = iblEntity ?? Entity()
            entity.name = "IBL"
            entity.components.set(ImageBasedLightComponent(
                source: .single(resource),
                intensityExponent: state.timeOfDay.iblExponent))
            if iblEntity == nil {
                root.addChild(entity)
                iblEntity = entity
            }
            // The receiver is not inherited: setting it on the root leaves every
            // child lit by the system's own environment light instead, which is
            // why the room stayed bright no matter how far the exponent dropped.
            let count = Self.attachReceiver(to: scene, light: entity)
            log.info("""
                image-based light ready for \(state.timeOfDay.rawValue),                 exponent \(state.timeOfDay.iblExponent), \(count) receivers
                """)
        } catch {
            log.error("EnvironmentResource.generate failed: \(error.localizedDescription)")
        }
    }

    /// The window pane must not cast, or it blocks the very light it is there to
    /// let through. Transparency does not affect shadow casting on its own.
    private static func stopGlassCastingShadows(in entity: Entity) {
        if entity.name.localizedCaseInsensitiveContains("glass") {
            entity.components.set(DynamicLightShadowComponent(castsShadow: false))
        }
        entity.children.forEach { stopGlassCastingShadows(in: $0) }
    }

    /// Apply the receiver to the whole subtree and report how many entities got it.
    @discardableResult
    private static func attachReceiver(to entity: Entity, light: Entity) -> Int {
        entity.components.set(ImageBasedLightReceiverComponent(imageBasedLight: light))
        return entity.children.reduce(1) { $0 + attachReceiver(to: $1, light: light) }
    }

    // MARK: - Sun

    private func applySun(_ state: LightingState) {
        var light = DirectionalLightComponent()
        // Fade with height rather than snapping on at sunrise. Moonlight is the floor.
        let daylight = Float(state.daylight)
        light.intensity = max(state.timeOfDay.moonIntensity,
                              state.timeOfDay.sunIntensity * daylight)
        let c = state.timeOfDay.sunColor
        light.color = UIColor(red: CGFloat(c.r), green: CGFloat(c.g),
                              blue: CGFloat(c.b), alpha: 1)
        sun.components.set(light)

        // Place the light on the room's own compass and look back at the middle.
        let bearing = Float(state.sunBearingInRoom) * .pi / 180
        let elevation = Float(max(state.sunElevation, 3.0)) * .pi / 180
        let distance: Float = 30
        let horizontal = distance * cos(elevation)
        let position = SIMD3<Float>(horizontal * sin(bearing),
                                    distance * sin(elevation),
                                    -horizontal * cos(bearing))
        sun.look(at: [0, 1.2, 0], from: position, relativeTo: nil)
    }

    // MARK: - Candles

    private func applyCandles(_ state: LightingState) {
        let lit = state.timeOfDay.candlesLit
        guard appliedCandles != lit else { return }
        appliedCandles = lit

        candleEntities.forEach { $0.removeFromParent() }
        candleEntities = []
        guard lit else { return }

        let flame = UIColor(red: 1.0, green: 0.72, blue: 0.42, alpha: 1)

        // Desk candles: point lights. RealityKit has no PointLightComponent.Shadow,
        // so these cannot cast — they are fill, not key.
        for (index, position) in Self.candlePositions.enumerated() where index < 2 {
            let entity = Entity()
            entity.name = "Candle\(index)"
            var light = PointLightComponent()
            light.intensity = 350
            light.attenuationRadius = 2.5
            light.color = flame
            entity.components.set(light)
            entity.position = position
            root.addChild(entity)
            candleEntities.append(entity)
        }

        // The chandelier is a spot light, which can cast, so the room gets at
        // least one warm source throwing shadows.
        if let hang = Self.candlePositions.last {
            let entity = Entity()
            entity.name = "Chandelier"
            var spot = SpotLightComponent()
            spot.intensity = 4200
            spot.attenuationRadius = 12.0
            spot.innerAngleInDegrees = 45
            spot.outerAngleInDegrees = 120
            spot.color = flame
            entity.components.set(spot)
            entity.components.set(SpotLightComponent.Shadow())
            entity.position = hang
            entity.look(at: [hang.x, 0, hang.z], from: hang, relativeTo: nil)
            root.addChild(entity)
            candleEntities.append(entity)
        }
    }
}
