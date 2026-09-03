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
    /// Mixed, not full: full immersion imposes a 1.5 m safety boundary that would eject
    /// you mid-pace. The room is a closed volume, so it occludes passthrough anyway.
    /// See docs/learning-notes/immersion-style-and-the-15m-boundary.md
    var immersionStyle: any ImmersionStyle = .mixed
}
