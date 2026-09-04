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
/// A candle's single light, and how bright it should be for its number of wicks.
private struct CandleLight {
    let entity: Entity
    let intensity: Float
}

@MainActor
final class LightRig {

    let root = Entity()

    /// Room centre, in the same user-relative space the generator uses:
    /// SEAT_Z in tools/generate_tower_shell.py.
    private static let seatOffsetZ: Float = -2.95
    /// The fire is the room's biggest source once lit.
    private static let fireIntensity: Float = 7500
    /// The orb. Cool, steady, and always on — the one light that is not a flame.
    private static let orbIntensity: Float = 5200

    /// One light per candle, not per wick. A six-cup candelabra reads the same lit
    /// by a single source at its centre, and 22 point lights is more than the room
    /// needs or the device should pay for. Every candle gets one, so none is dark.
    private static let flameIntensity: Float = 2600
    private let sun = Entity()
    private var iblEntity: Entity?
    private var chandelierLight: Entity?
    private var fireLight: Entity?
    private var orbLight: Entity?
    private var fireParticles: Entity?
    private var flames: [Entity] = []
    private var candleLights: [CandleLight] = []
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
        applyFire(in: scene)
        applyOrb(in: scene)
        applyFireParticles(in: scene)
    }

    /// Flames in the hearth.
    ///
    /// A particle emitter, not geometry: fire has no shape to model. Only the
    /// hearth gets one — thirty candle flames with emitters each would be a lot of
    /// simulation for something that reads as a 2 cm dot, so those stay emissive
    /// geometry with an animated light.
    private func applyFireParticles(in scene: Entity) {
        guard fireParticles == nil,
              let fire = Self.findNamed(prefix: "Fire_", in: scene).first else { return }

        var emitter = ParticleEmitterComponent()
        // A shallow bed the width of the firebox, so flames rise off coals rather
        // than from a point.
        emitter.emitterShape = .box
        emitter.emitterShapeSize = [0.34, 0.04, 0.22]
        emitter.birthDirection = .local
        emitter.emissionDirection = [0, 1, 0]
        emitter.speed = 0.30
        emitter.speedVariation = 0.18

        var flame = ParticleEmitterComponent.ParticleEmitter()
        flame.birthRate = 190
        flame.birthRateVariation = 40
        flame.lifeSpan = 0.85
        flame.lifeSpanVariation = 0.35
        flame.size = 0.085
        flame.sizeVariation = 0.035
        flame.acceleration = [0, 0.45, 0]          // convection
        flame.dampingFactor = 1.4
        flame.spreadingAngle = 0.42
        flame.angleVariation = .pi
        flame.blendMode = .additive                 // fire adds light, never occludes
        flame.billboardMode = .billboard
        flame.isLightingEnabled = false             // it is the source, not lit
        flame.opacityCurve = .quickFadeInOut
        // Yellow at the base cooling to red as it rises.
        flame.color = .evolving(
            start: .single(UIColor(red: 1.0, green: 0.78, blue: 0.28, alpha: 1)),
            end: .single(UIColor(red: 0.85, green: 0.16, blue: 0.03, alpha: 1)))
        emitter.mainEmitter = flame

        fire.components.set(emitter)
        fireParticles = fire
    }


    /// The orb on its pedestal. A point light, so it throws in every direction as
    /// a floating light should — which does mean no shadows, since RealityKit has
    /// no PointLightComponent.Shadow. A spot would cast but would read as a lamp.
    private func applyOrb(in scene: Entity) {
        guard orbLight == nil,
              let orb = Self.findNamed(prefix: "Orb_", in: scene).first else { return }
        var light = PointLightComponent()
        light.intensity = Self.orbIntensity
        light.attenuationRadius = 7.0
        light.color = UIColor(red: 0.55, green: 0.78, blue: 1.0, alpha: 1)
        orb.components.set(light)
        orbLight = orb
    }

    /// The hearth. A spot light aimed out of the opening, because point lights
    /// cannot cast shadows and the fire should throw the room's longest ones.
    /// It burns whenever you are here — a toggle is a Phase 5 nice-to-have.
    private func applyFire(in scene: Entity) {
        guard fireLight == nil,
              let fire = Self.findNamed(prefix: "Fire_", in: scene).first else { return }
        let at = fire.position(relativeTo: nil)
        let entity = Entity()
        entity.name = "FireLight"
        var spot = SpotLightComponent()
        spot.intensity = Self.fireIntensity
        spot.attenuationRadius = 9.0
        spot.innerAngleInDegrees = 60
        spot.outerAngleInDegrees = 150
        spot.color = UIColor(red: 1.0, green: 0.55, blue: 0.20, alpha: 1)
        entity.components.set(spot)
        entity.components.set(SpotLightComponent.Shadow())
        entity.position = at
        // Aim out of the hearth, across the middle of the room at head height.
        entity.look(at: [0, 1.1, -Self.seatOffsetZ], from: at, relativeTo: nil)
        root.addChild(entity)
        fireLight = entity
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
            flames = Self.findFlames(in: scene)
            candleLights = Self.makeCandleLights(from: flames, color: flameColor)
            candleLights.forEach { root.addChild($0.entity) }
            log.info("\(self.flames.count) flames in \(self.candleLights.count) candles")
        }

        flames.forEach { $0.isEnabled = lit }
        for candle in candleLights {
            candle.entity.isEnabled = lit
            guard lit else { continue }
            var light = PointLightComponent()
            light.intensity = candle.intensity
            light.attenuationRadius = 5.0
            light.color = flameColor
            candle.entity.components.set(light)
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
        if chandelierLight == nil,
           let hang = candleLights.map({ $0.entity.position }).filter({ $0.y > 2.5 })
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

    /// One light per candle, placed at the centre of its wicks and brightened for
    /// how many it stands in for — but sub-linearly, or a six-cup stand would
    /// out-shine everything else in the room.
    private static func makeCandleLights(from flames: [Entity],
                                         color: UIColor) -> [CandleLight] {
        var groups: [Int: [Entity]] = [:]
        for flame in flames {
            let parts = flame.name.split(separator: "_")
            guard parts.count >= 2, let group = Int(parts[1]) else { continue }
            groups[group, default: []].append(flame)
        }
        return groups.keys.sorted().compactMap { key in
            guard let members = groups[key], !members.isEmpty else { return nil }
            let centre = members
                .map { $0.position(relativeTo: nil) }
                .reduce(SIMD3<Float>.zero, +) / Float(members.count)
            let entity = Entity()
            entity.name = "CandleLight_\(key)"
            entity.position = centre
            return CandleLight(entity: entity,
                               intensity: flameIntensity * sqrt(Float(members.count)))
        }
    }

    /// Candlelight is never steady. Each flame gets its own phase, so they do not
    /// pulse together — which reads as a fault rather than as fire.
    private func startFlickering() {
        flickerTask = Task { [weak self] in
            var t = 0.0
            while !Task.isCancelled {
                guard let self else { return }
                t += 0.08
                for (index, candle) in self.candleLights.enumerated()
                where candle.entity.isEnabled {
                    guard var light = candle.entity.components[PointLightComponent.self]
                    else { continue }
                    let phase = Double(index) * 1.7
                    // Slower and deeper than the first attempt, which was
                    // imperceptible: 18% at 5 Hz just reads as steady light.
                    let wobble = sin(t * 2.1 + phase) * 0.55
                        + sin(t * 4.7 + phase * 2.0) * 0.3
                        + sin(t * 9.1 + phase * 3.0) * 0.15
                    light.intensity = candle.intensity * Float(1.0 + 0.42 * wobble)
                    candle.entity.components.set(light)
                }
                if let orb = self.orbLight,
                   var light = orb.components[PointLightComponent.self] {
                    // A slow swell, not a flicker. It should read as alive but
                    // steady, against the fire and candles which are neither.
                    let swell = sin(t * 0.55) * 0.7 + sin(t * 1.27) * 0.3
                    light.intensity = Self.orbIntensity * Float(1.0 + 0.12 * swell)
                    orb.components.set(light)
                }
                if let fire = self.fireLight,
                   var spot = fire.components[SpotLightComponent.self] {
                    // Slower and broader than a candle: a fire breathes rather
                    // than gutters.
                    let breathe = sin(t * 1.3) * 0.6 + sin(t * 3.1) * 0.25 + sin(t * 6.7) * 0.15
                    spot.intensity = Self.fireIntensity * Float(1.0 + 0.30 * breathe)
                    fire.components.set(spot)
                }
                try? await Task.sleep(for: .milliseconds(80))
            }
        }
    }

    private static func findFlames(in entity: Entity) -> [Entity] {
        findNamed(prefix: "Flame_", in: entity)
    }

    private static func findNamed(prefix: String, in entity: Entity) -> [Entity] {
        var found: [Entity] = []
        if entity.name.hasPrefix(prefix) { found.append(entity) }
        for child in entity.children {
            found.append(contentsOf: findNamed(prefix: prefix, in: child))
        }
        return found
    }
}
