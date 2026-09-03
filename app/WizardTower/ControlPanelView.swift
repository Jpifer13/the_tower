import SwiftUI

/// The floating SwiftUI window. Phase 5 turns this into the real settings
/// panel (immersion level, ambient volume, time of day).
struct ControlPanelView: View {

    @Environment(AppModel.self) private var appModel
    @Environment(\.openImmersiveSpace) private var openImmersiveSpace
    @Environment(\.dismissImmersiveSpace) private var dismissImmersiveSpace

    var body: some View {
        VStack(spacing: 20) {
            Text("The Tower")
                .font(.extraLargeTitle2)

            Text("Phase 0 — proving the toolchain works.")
                .font(.subheadline)
                .foregroundStyle(.secondary)

            Toggle(isOn: immersiveBinding) {
                Text(appModel.immersiveSpaceState == .open ? "Leave the tower" : "Enter the tower")
            }
            .toggleStyle(.button)
            .disabled(appModel.immersiveSpaceState == .inTransition)
        }
        .padding(40)
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
                // TowerImmersiveView flips the state to .open once it appears.
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
