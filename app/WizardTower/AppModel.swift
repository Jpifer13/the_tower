import SwiftUI

/// Single source of truth for the tower's state.
///
/// Phase 5 grows this: time-of-day, weather, fire on/off, ambient volume.
/// For Phase 0 it only tracks whether the immersive space is open.
@MainActor
@Observable
final class AppModel {

    static let controlPanelID = "ControlPanel"
    static let immersiveSpaceID = "TowerSpace"

    enum ImmersiveSpaceState {
        case closed
        case inTransition
        case open
    }

    var immersiveSpaceState: ImmersiveSpaceState = .closed

    /// Follow the real sun, or pin the room to one look.
    var lightingMode: LightingMode = .liveClock

    /// Where the tower stands and which way the window faces.
    var place = TowerPlace()

    /// The lighting implied by the mode and the clock.
    func lightingState(at date: Date = .now) -> LightingState {
        switch lightingMode {
        case .liveClock:
            let solar = SolarPosition.at(date,
                                         latitude: place.latitude,
                                         longitude: place.longitude,
                                         timeZone: .current)
            return LightingState(
                timeOfDay: solar.impliedTimeOfDay,
                sunElevation: solar.elevation,
                sunBearingInRoom: place.bearingInRoom(compass: solar.azimuth),
                daylight: solar.daylightFraction)

        case .manual(let time):
            // A plausible sun for each look, since there is no clock to ask.
            let elevation: Double = switch time {
            case .day: 48
            case .sunset: 4
            case .night: -20
            }
            return LightingState(
                timeOfDay: time,
                sunElevation: elevation,
                sunBearingInRoom: place.bearingInRoom(compass: place.windowBearing),
                daylight: time == .day ? 1.0 : (time == .sunset ? 0.35 : 0.0))
        }
    }
    /// Mixed, not full: full immersion imposes a 1.5 m safety boundary that would eject
    /// you mid-pace. The room is a closed volume, so it occludes passthrough anyway.
    /// See docs/learning-notes/immersion-style-and-the-15m-boundary.md
    var immersionStyle: any ImmersionStyle = .mixed
}
