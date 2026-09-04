import SwiftUI

/// The floating window. Grows into the full settings panel in Phase 5.
struct ControlPanelView: View {

    @Environment(AppModel.self) private var appModel
    @Environment(\.openImmersiveSpace) private var openImmersiveSpace
    @Environment(\.dismissImmersiveSpace) private var dismissImmersiveSpace

    /// Ticks the readout so the live sun figures stay current while the panel is open.
    @State private var now = Date.now
    private let clock = Timer.publish(every: 30, on: .main, in: .common).autoconnect()

    var body: some View {
        VStack(spacing: 20) {
            Text("The Tower")
                .font(.extraLargeTitle2)

            Picker("Lighting", selection: modeBinding) {
                Text("Follow the sun").tag(0)
                Text("Day").tag(1)
                Text("Sunset").tag(2)
                Text("Night").tag(3)
            }
            .pickerStyle(.segmented)

            sunReadout

            Toggle(isOn: immersiveBinding) {
                Text(appModel.immersiveSpaceState == .open ? "Leave the tower" : "Enter the tower")
            }
            .toggleStyle(.button)
            .disabled(appModel.immersiveSpaceState == .inTransition)
        }
        .padding(40)
        .frame(minWidth: 460)
        .onReceive(clock) { now = $0 }
    }

    private var sunReadout: some View {
        let state = appModel.lightingState(at: now)
        let above = state.sunElevation >= 0
        return VStack(spacing: 4) {
            Text(state.timeOfDay.rawValue.capitalized)
                .font(.headline)
            Text(above
                 ? String(format: "Sun %.0f° above the horizon, %.0f° from the desk",
                          state.sunElevation, state.sunBearingInRoom)
                 : String(format: "Sun %.0f° below the horizon", -state.sunElevation))
                .font(.caption)
                .foregroundStyle(.secondary)
            if case .liveClock = appModel.lightingMode {
                Text(String(format: "at %.1f°%@ %.1f°%@, window facing %.0f°",
                            abs(appModel.place.latitude),
                            appModel.place.latitude >= 0 ? "N" : "S",
                            abs(appModel.place.longitude),
                            appModel.place.longitude >= 0 ? "E" : "W",
                            appModel.place.windowBearing))
                    .font(.caption2)
                    .foregroundStyle(.tertiary)
            }
        }
    }

    private var modeBinding: Binding<Int> {
        Binding(
            get: {
                switch appModel.lightingMode {
                case .liveClock: 0
                case .manual(.day): 1
                case .manual(.sunset): 2
                case .manual(.night): 3
                }
            },
            set: { tag in
                appModel.lightingMode = switch tag {
                case 1: .manual(.day)
                case 2: .manual(.sunset)
                case 3: .manual(.night)
                default: .liveClock
                }
            }
        )
    }

    private var immersiveBinding: Binding<Bool> {
        Binding(
            get: { appModel.immersiveSpaceState != .closed },
            set: { shouldOpen in
                Task { await toggleImmersiveSpace(open: shouldOpen) }
            }
        )
    }

    private func toggleImmersiveSpace(open: Bool) async {
        guard appModel.immersiveSpaceState != .inTransition else { return }
        appModel.immersiveSpaceState = .inTransition

        if open {
            switch await openImmersiveSpace(id: AppModel.immersiveSpaceID) {
            case .opened:
                break
            case .userCancelled, .error:
                fallthrough
            @unknown default:
                appModel.immersiveSpaceState = .closed
            }
        } else {
            await dismissImmersiveSpace()
            appModel.immersiveSpaceState = .closed
        }
    }
}
