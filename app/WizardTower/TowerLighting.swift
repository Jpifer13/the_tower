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
    /// Compute the sky rather than photograph it. See `SkyModel`.
    var proceduralSky: Bool = true
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

    /// Grid of the fire flipbook. Must match the sheet, or frames slide instead of
    /// One particle lives for many loops, so a respawn is rare rather than every

    /// Loads a sprite sheet from the bundle, or nil if none has been added.
    private static func flipbook(named name: String) -> TextureResource? {
        for ext in ["png", "jpg"] {
            guard let url = Bundle.main.url(forResource: name, withExtension: ext) else { continue }
            if let texture = try? TextureResource.load(contentsOf: url) { return texture }
        }
        return nil
    }

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
    private struct SkyKey: Equatable {
        var elevation: Int
        var azimuth: Int
        var procedural: Bool
        var timeOfDay: TimeOfDay
    }
    private var appliedSky: SkyKey?
    /// How many of the 25 street lamps get a real point light, nearest first.
    private static let litLampRange = 20
    /// Lumens. A street lamp is a dim thing; it only has to beat a moonless night.
    private static let lampIntensity: Float = 34000
    /// Metres. Keeps each lamp local to its own stretch of street.
    private static let lampReach: Float = 17

    private var appliedLamps: Bool?
    /// The emissive materials the generator baked onto the lamp heads, kept so
    /// they can be put back at dusk after being swapped out for daylight.
    private var litLampMaterials: [String: [any RealityKit.Material]] = [:]
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
        Self.frostGlass(state, in: scene)
        await applySky(state, to: scene)
        applySun(state)
        applyCandles(state, in: scene)
        applyFire(in: scene)
        applyOrb(in: scene)
        applyFireParticles(in: scene)
        applyStreetLamps(state, in: scene)
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

        // Sits just above the coals; the particles rise from there.
        let riser = Entity()
        riser.name = "FireParticles"
        riser.position = [0, 0.02, 0]
        fire.addChild(riser)

        // Many small flames rather than one big billboard. A single sprite spawned
        // dozens of times, with the emitter doing the animating — drift, spread,
        // rotation, staggered lifespans — builds volume that no single 2D card can.
        // The flipbook attempt failed because a whole-campfire sheet can only be
        // shown once, so it could never be more than a flat picture of a fire.
        var emitter = ParticleEmitterComponent()
        emitter.emitterShape = .box
        emitter.emitterShapeSize = [0.30, 0.03, 0.18]   // the grate bed
        emitter.birthDirection = .local
        emitter.emissionDirection = [0, 1, 0]
        emitter.speed = 0.22
        emitter.speedVariation = 0.12

        var flame = ParticleEmitterComponent.ParticleEmitter()
        flame.birthRate = 55
        flame.birthRateVariation = 15
        flame.lifeSpan = 1.1
        flame.lifeSpanVariation = 0.4
        flame.size = 0.17
        flame.sizeVariation = 0.07
        flame.acceleration = [0, 0.55, 0]      // convection
        flame.dampingFactor = 1.6
        flame.spreadingAngle = 0.35
        flame.angleVariation = .pi             // random roll, so no two look alike
        flame.blendMode = .additive            // fire adds light and never occludes
        flame.billboardMode = .billboard
        flame.isLightingEnabled = false        // it is the source, not lit
        flame.opacityCurve = .gradualFadeInOut // no popping in or out
        // The sprite is white, so the colour ramp does the work: hot at the base,
        // cooling to red as it rises.
        flame.color = .evolving(
            start: .single(UIColor(red: 1.0, green: 0.85, blue: 0.45, alpha: 1)),
            end: .single(UIColor(red: 0.90, green: 0.20, blue: 0.04, alpha: 1)))

        if let sprite = Self.flipbook(named: "fire_particle") {
            flame.image = sprite
            log.info("fire sprite loaded")
        } else {
            log.info("no fire sprite — the hearth will show untextured particles")
        }
        emitter.mainEmitter = flame

        riser.components.set(emitter)
        fireParticles = riser
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

    /// Build the sky once, and use it for both the dome and the light.
    ///
    /// One image drives what you see out of the window *and* what the room is lit
    /// by, so the two cannot disagree -- which they did while the sky was a
    /// photograph, since its sun was wherever the photographer stood and the
    /// light came from wherever SolarPosition said.
    private func applySky(_ state: LightingState, to scene: Entity) async {
        // The procedural sky is continuous, so keying the cache on time-of-day is
        // not enough; quantise the sun instead. A degree is far finer than the eye
        // follows and still collapses a whole minute of drift to one rebuild.
        let key = SkyKey(elevation: Int((state.sunElevation).rounded()),
                         azimuth: Int((state.sunBearingInRoom).rounded()),
                         procedural: state.proceduralSky,
                         timeOfDay: state.timeOfDay)
        guard appliedSky != key else { return }

        let name: String
        let cgImage: CGImage?
        if state.proceduralSky {
            name = "procedural"
            let sky = SkyModel(sunElevation: Float(state.sunElevation),
                               sunAzimuth: Float(state.sunBearingInRoom))
            // Off the main actor: this is a few tens of milliseconds of pixels.
            cgImage = await Task.detached(priority: .userInitiated) {
                sky.image()
            }.value
        } else {
            name = state.timeOfDay.skyImageName
            cgImage = Self.skyImage(name)
        }
        guard let cgImage else {
            log.error("no sky image for \(name)")
            return
        }
        appliedSky = key

        // The dome is what you actually look at.
        if let dome = scene.findEntity(named: "Sky"),
           var model = dome.components[ModelComponent.self] {
            do {
                let texture = try await TextureResource(
                    image: cgImage, options: .init(semantic: .color))
                // Unlit: the sky is a backdrop, not a surface in the room, so it
                // must not darken when the room does.
                var material = UnlitMaterial()
                material.color = .init(texture: .init(texture))
                model.materials = Array(repeating: material,
                                        count: max(1, model.materials.count))
                dome.components.set(model)
            } catch {
                log.error("sky dome texture failed: \(error.localizedDescription)")
            }
        } else {
            log.error("no Sky entity with a mesh to retexture")
        }

        // ...and the same image lights the room.
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
            log.info("sky \(name) sun \(key.elevation)/\(key.azimuth), \(count) receivers")
        } catch {
            log.error("EnvironmentResource.generate failed: \(error.localizedDescription)")
        }
    }

    /// The window pane must not cast, or it blocks the very light it is there to
    /// let through. Transparency does not affect shadow casting on its own.
    /// Let the frosted pane glow only while there is daylight behind it.
    ///
    /// Frosted glass reads as milky because it scatters the light striking it.
    /// The generator gives the pane a mottled emissive to fake that, but emission
    /// is constant in the USD, so at night the window became a grey lamp and
    /// washed the lit village out entirely. Scaling the intensity with the sun
    /// keeps the daytime veil and hands the night back its lights.
    private static func frostGlass(_ state: LightingState, in entity: Entity) {
        if entity.name.localizedCaseInsensitiveContains("glass"),
           var model = entity.components[ModelComponent.self] {
            let lit = Float(max(0.0, min(1.0, state.daylight)))
            model.materials = model.materials.map { material in
                guard var pbr = material as? PhysicallyBasedMaterial else { return material }
                // Scale the emissive the USD authored rather than replacing the
                // material, so the pane keeps its mottling.
                pbr.emissiveIntensity = lit
                return pbr
            }
            entity.components.set(model)
        }
        entity.children.forEach { frostGlass(state, in: $0) }
    }

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

    /// Street lamps and lit windows burn only after dark.
    ///
    /// Their glow is baked into the generated USD, so without this they sit there
    /// lit at midday -- pools of lamplight on sunlit cobbles. The pools are simply
    /// switched off; the heads keep their geometry but drop to plain dull glass,
    /// since a lamp is still a visible object in daylight, just not a bright one.
    private func applyStreetLamps(_ state: LightingState, in scene: Entity) {
        let lit = state.timeOfDay.candlesLit
        guard appliedLamps != lit else { return }
        appliedLamps = lit

        var unlitHead = PhysicallyBasedMaterial()
        unlitHead.baseColor = .init(tint: UIColor(white: 0.62, alpha: 1.0))
        unlitHead.roughness = 0.35
        unlitHead.metallic = 0.0

        var heads: [Entity] = []
        var pools = 0, panes = 0
        func walk(_ entity: Entity) {
            if entity.name.hasPrefix("LampPool_") {
                entity.isEnabled = lit
                pools += 1
            } else if entity.name.hasPrefix("WinGlow") {
                // Lit panes are emissive geometry like the lamps, so they burn
                // through midday unless they are switched too.
                entity.isEnabled = lit
                panes += 1
            } else if entity.name.hasPrefix("Lamp_") {
                heads.append(entity)
                if var model = entity.components[ModelComponent.self] {
                    if lit {
                        if let saved = litLampMaterials[entity.name] {
                            model.materials = saved
                            entity.components.set(model)
                        }
                    } else {
                        litLampMaterials[entity.name] = model.materials
                        model.materials = Array(repeating: unlitHead,
                                                count: max(1, model.materials.count))
                        entity.components.set(model)
                    }
                }
            }
            for child in entity.children { walk(child) }
        }
        walk(scene)

        // The glowing head and the pool underneath it are both fakes painted on
        // the geometry: they put no light on anything else, so the house fronts
        // beside a lamp stayed black. A real point light fixes that, but there
        // are 25 lamps and point lights are not free, so only the nearest few
        // get one -- the rest are too far to read as anything but their own glow.
        // (Point lights cannot cast shadows in RealityKit, which outdoors at this
        // distance costs nothing.)
        let nearest = heads
            .sorted { simd_length_squared($0.position(relativeTo: nil))
                    < simd_length_squared($1.position(relativeTo: nil)) }
        for (index, head) in nearest.enumerated() {
            guard lit, index < Self.litLampRange else {
                head.components.remove(PointLightComponent.self)
                continue
            }
            head.components.set(PointLightComponent(
                color: UIColor(red: 1.0, green: 0.78, blue: 0.46, alpha: 1.0),
                intensity: Self.lampIntensity,
                attenuationRadius: Self.lampReach))
        }
        let real = lit ? min(Self.litLampRange, nearest.count) : 0
        let state = lit ? "lit" : "out"
        log.info("village lights \(state): \(nearest.count) lamps, \(pools) pools, \(panes) window groups, \(real) casting real light")
    }

    /// Sky images are loose files in the bundle, not asset-catalog entries, so
    /// neither UIImage(named:) nor TextureResource(named:in:) can find them --
    /// the latter fails with "Could not get asset catalog from supplied bundle".
    /// Resolve the URL instead.
    private static func skyImage(_ name: String) -> CGImage? {
        guard let url = Bundle.main.url(forResource: name, withExtension: "jpg"),
              let image = UIImage(contentsOfFile: url.path) else { return nil }
        return image.cgImage
    }


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
