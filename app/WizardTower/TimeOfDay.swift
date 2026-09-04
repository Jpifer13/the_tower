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

    /// How much the image-based light contributes. Night wants far less.
    var iblExponent: Float {
        switch self {
        case .day:    0.0
        case .sunset: -0.6
        case .night:  -2.2
        }
    }

    /// Candles are lit when the daylight isn't doing the work.
    var candlesLit: Bool { self != .day }
}
