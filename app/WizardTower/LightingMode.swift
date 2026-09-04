import Foundation

/// Where the lighting takes its cue from.
enum LightingMode: Equatable {
    /// Follow the real sun for the current place and clock.
    case liveClock
    /// Pin the room to one look, for screenshots or because you feel like night.
    case manual(TimeOfDay)
}

/// Where the tower stands, and which way its window faces.
///
/// Latitude cannot be derived without asking for location, so it is a setting.
/// Longitude defaults from the device time zone, which is close enough to put the
/// sun in the right part of the sky without any permission prompt.
struct TowerPlace: Equatable {
    var latitude: Double = 40.0
    var longitude: Double
    /// Compass bearing the window faces, degrees clockwise from north.
    /// South by default, so it catches sun across the day up north.
    var windowBearing: Double = 180.0

    /// The window sits 55° to the right of the desk you face — see
    /// WINDOW_CENTRE in tools/generate_tower_shell.py.
    static let windowOffsetInRoom = 55.0

    init(timeZone: TimeZone = .current) {
        let hours = Double(timeZone.secondsFromGMT()) / 3600.0
        longitude = hours * 15.0
    }

    /// Convert a compass bearing into the room's own frame, where 0 is straight
    /// ahead at the desk and +90 is your right.
    func bearingInRoom(compass: Double) -> Double {
        let roomForwardCompass = windowBearing - Self.windowOffsetInRoom
        return (compass - roomForwardCompass).truncatingRemainder(dividingBy: 360)
    }
}
