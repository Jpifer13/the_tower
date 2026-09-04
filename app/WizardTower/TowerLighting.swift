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

    /// Every flame glows, but only the nearest few carry a light — 22 point lights
    /// is more than the room needs and more than the device should pay for. The
    /// rest still read as flames because the geometry is emissive.
    private static let maxLitFlames = 10
    /// Base brightness of one candle flame. RealityKit's default point light is
    /// around 27,000, so candle values live in the low thousands — a few hundred
    /// glows without lighting anything.
    private static let flameIntensity: Float = 3800

    private let sun = Entity()
    private var iblEntity: Entity?
    private var chandelierLight: Entity?
    private var flames: [Entity] = []
    private var flickerTask: Task<Void, Never>?
    private var appliedSky: TimeOfDay?
    private var appliedCandles: Bool?

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
        applyCandles(state, in: scene)
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
            // The receiver is not inherited: setting it on the root alone leaves
            // every child lit by the system's own environment light instead.
            let count = Self.attachReceiver(to: scene, light: entity)
            log.info("sky \(state.timeOfDay.rawValue), \(count) receivers")
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
        sun.look(at: [0, 1.2, 0],
                 from: SIMD3<Float>(horizontal * sin(bearing),
                                    distance * sin(elevation),
                                    -horizontal * cos(bearing)),
                 relativeTo: nil)
    }

    // MARK: - Candles

    /// Flames are found in the scene by name rather than listed here. The generator
    /// emits a small emissive sphere called Flame_N above every wick, so a candle's
    /// position lives in one place — move it there and the light follows.
    private func applyCandles(_ state: LightingState, in scene: Entity) {
        let lit = state.timeOfDay.candlesLit
        let flameColor = UIColor(red: 1.0, green: 0.72, blue: 0.42, alpha: 1)

        if flames.isEmpty {
            // Nearest the seat first, so the lights land where you actually are.
            flames = Self.findFlames(in: scene)
                .sorted { simd_length($0.position(relativeTo: nil))
                        < simd_length($1.position(relativeTo: nil)) }
            log.info("found \(self.flames.count) flames, lighting \(min(self.flames.count, Self.maxLitFlames))")
        }

        for (index, entity) in flames.enumerated() {
            entity.isEnabled = lit
            guard lit, index < Self.maxLitFlames else {
                entity.components.remove(PointLightComponent.self)
                continue
            }
            var light = PointLightComponent()
            light.intensity = Self.flameIntensity
            light.attenuationRadius = 4.5
            light.color = flameColor
            entity.components.set(light)
        }

        guard appliedCandles != lit else { return }
        appliedCandles = lit
        flickerTask?.cancel()
        flickerTask = nil

        guard lit else {
            chandelierLight?.removeFromParent()
            chandelierLight = nil
            return
        }

        // One spot light under the chandelier, because point lights cannot cast
        // shadows at all and the room needs at least one warm source that does.
        // Positioned from the chandelier's own flames rather than a second constant.
        if chandelierLight == nil,
           let hang = Self.findFlames(in: scene)
               .map({ $0.position(relativeTo: nil) })
               .filter({ $0.y > 2.5 })
               .max(by: { $0.y < $1.y }) {
            let entity = Entity()
            entity.name = "ChandelierLight"
            var spot = SpotLightComponent()
            spot.intensity = 9000
            spot.attenuationRadius = 11.0
            spot.innerAngleInDegrees = 45
            spot.outerAngleInDegrees = 120
            spot.color = flameColor
            entity.components.set(spot)
            entity.components.set(SpotLightComponent.Shadow())
            entity.position = hang
            entity.look(at: [hang.x, 0, hang.z], from: hang, relativeTo: nil)
            root.addChild(entity)
            chandelierLight = entity
        }
        startFlickering()
    }

    /// Candlelight is never steady. Each flame gets its own phase, so they do not
    /// pulse together — which reads as a fault rather than as fire.
    private func startFlickering() {
        flickerTask = Task { [weak self] in
            var t = 0.0
            while !Task.isCancelled {
                guard let self else { return }
                t += 0.08
                for (index, entity) in self.flames.enumerated() where entity.isEnabled {
                    guard var light = entity.components[PointLightComponent.self] else { continue }
                    let phase = Double(index) * 1.7
                    // Slower and deeper than the first attempt, which was
                    // imperceptible: 18% at 5 Hz just reads as steady light.
                    let wobble = sin(t * 2.1 + phase) * 0.55
                        + sin(t * 4.7 + phase * 2.0) * 0.3
                        + sin(t * 9.1 + phase * 3.0) * 0.15
                    light.intensity = Self.flameIntensity * Float(1.0 + 0.42 * wobble)
                    entity.components.set(light)
                }
                try? await Task.sleep(for: .milliseconds(80))
            }
        }
    }

    private static func findFlames(in entity: Entity) -> [Entity] {
        var found: [Entity] = []
        if entity.name.hasPrefix("Flame") { found.append(entity) }
        for child in entity.children { found.append(contentsOf: findFlames(in: child)) }
        return found
    }
}
