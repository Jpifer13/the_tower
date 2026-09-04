import Foundation

/// Which sky lights the room. Phase 5 syncs this to the clock and to WeatherKit;
/// for now it is set by hand.
enum TimeOfDay: String, CaseIterable, Identifiable {
    case day, sunset, night

    var id: String { rawValue }

    /// Equirectangular image in the app bundle, used both as the skydome's
    /// light source and as the room's ambient.
    var skyImageName: String {
        switch self {
        case .day:    "sky_day"
        case .sunset: "sky_sunset"
        case .night:  "sky_night"
        }
    }

    /// Sun or moon coming through the window, in lux-ish RealityKit units.
    var sunIntensity: Float {
        switch self {
        case .day:    3200
        case .sunset: 1400
        case .night:  180
        }
    }

    /// Warm at sunset, cold at night, neutral at midday.
    var sunColor: (r: Float, g: Float, b: Float) {
        switch self {
        case .day:    (1.00, 0.98, 0.94)
        case .sunset: (1.00, 0.72, 0.42)
        case .night:  (0.62, 0.72, 1.00)
        }
    }

    /// How much the image-based light contributes, as a power of two: 0 is the
    /// full open-sky value, -3 is an eighth of it.
    ///
    /// This has to be pushed well down. Image-based lighting is **unoccluded** —
    /// it lights every surface as though the sky were visible from all sides,
    /// with no account taken of walls. A stone room with one window sees a small
    /// fraction of the sky, so leaving this near 0 lights the place like an open
    /// courtyard. Night goes lower still, because the moonlit HDRI has warm
    /// street lamps in it and reads far brighter than moonlight should.
    var iblExponent: Float {
        switch self {
        case .day:    -2.6
        case .sunset: -3.6
        case .night:  -4.5
        }
    }

    /// Candles are lit when the daylight isn't doing the work.
    var candlesLit: Bool { self != .day }

    /// Floor the sun never drops below, so night still has moonlight to shape by.
    /// Directional, unlike the ambient, so it still throws shadows through the window.
    var moonIntensity: Float {
        switch self {
        case .day:    0
        case .sunset: 90
        case .night:  420
        }
    }
}
